"""Scheduling contracts independent of CUDA hardware, plus an optional GPU check."""
from types import SimpleNamespace
import threading
import weakref

import numpy as np
import pytest

from holodoppler import backend
from holodoppler.core import processing


@pytest.fixture
def cuda(monkeypatch):
    log = []
    state = SimpleNamespace(current=None, streams=[])

    class Stream:
        def __init__(self, non_blocking=True):
            self.index = len(state.streams)
            state.streams.append(self)
            self.tasks = []
            self.completed = 0

        def __enter__(self):
            self.previous = state.current
            state.current = self
            return self

        def __exit__(self, *args):
            state.current = self.previous

        def wait_event(self, event):
            assert event.stream is not None
            log.append(('wait', self.index, event.stream.index))
            self.tasks.append(event.finish)

        def finish(self, count):
            while self.completed < count:
                task = self.tasks[self.completed]
                self.completed += 1
                task()

        def synchronize(self):
            log.append(('sync', self.index))
            self.finish(len(self.tasks))

    class Event:
        def record(self, stream):
            self.stream = stream
            self.count = len(stream.tasks)
            log.append(('record', stream.index))

        def finish(self):
            self.stream.finish(self.count)

        def synchronize(self):
            log.append(('event_sync', self.stream.index))
            self.finish()

    class Array:
        def __init__(self, shape, dtype):
            self.value = np.empty(shape, dtype=dtype)
            self.shape, self.dtype = self.value.shape, self.value.dtype

        def set(self, source, stream):
            assert state.current is stream
            source_ref, device_ref = weakref.ref(source), weakref.ref(self)

            def transfer():
                assert source_ref() is not None and device_ref() is not None
                np.copyto(device_ref().value, source_ref())

            stream.tasks.append(transfer)
            log.append(('upload', stream.index))

        def get(self, *, out, stream, blocking):
            assert state.current is stream and blocking is False
            target_ref, device_ref = weakref.ref(out), weakref.ref(self)

            def transfer():
                assert target_ref() is not None and device_ref() is not None
                np.copyto(target_ref(), device_ref().value)

            stream.tasks.append(transfer)
            log.append(('download', stream.index))

    state.current = Stream()
    xp = SimpleNamespace(
        cuda=SimpleNamespace(Stream=Stream, Event=Event,
                             get_current_stream=lambda: state.current,
                             alloc_pinned_memory=bytearray),
        empty=Array, ndarray=Array,
    )
    monkeypatch.setattr(backend, 'xp', xp)
    monkeypatch.setattr(backend, 'is_gpu', True)
    monkeypatch.setattr(backend, 'get_backend_name', lambda: 'fake-cupy')
    return state, log


@pytest.mark.parametrize('depth', [1, 2, 4])
@pytest.mark.parametrize('count', [0, 1, 9])
def test_gpu_order_bounds_reference_and_progress(cuda, depth, count):
    state, log = cuda
    consumed, callbacks, references = [], [], []
    lock = threading.Lock()
    reads = 0
    caller = threading.get_ident()

    class Reader:
        def read_frames(self, first_frame, batch_size):
            nonlocal reads
            assert threading.get_ident() != caller
            with lock:
                reads += 1
                assert reads - len(consumed) <= depth
            return np.full((2, 3), first_frame, dtype=np.uint16)

    def process(frames, reference):
        assert state.current.index == 2
        assert frames.shape == (1, 2, 3)
        references.append(reference)
        return {'value': frames}, (reference or 0) + 1

    def prepare(result):
        assert state.current.index == 2
        return result

    def consume(index, result):
        assert threading.get_ident() == caller
        assert isinstance(result['value'], np.ndarray)
        np.testing.assert_array_equal(result['value'], index * 3)
        consumed.append(index)

    ref = processing.run_batches(
        Reader(), list(range(0, count * 3, 3)), 1, process, consume,
        cupy_prefetch_depth=depth, registration_ref=0, prepare_result=prepare,
        progress_callback=lambda *args: callbacks.append(args),
    )
    assert ref == count
    assert references == list(range(count))
    assert consumed == list(range(count))
    assert [item[0] for item in callbacks] == list(range(1, count + 1))
    if count:
        assert ('wait', 2, 0) in log  # Initial reference/autofocus dependency.
        assert log.count(('wait', 2, 1)) == count
        assert log.count(('wait', 3, 2)) == count
        assert [entry for entry in log if entry[0] == 'sync'] == [
            ('sync', 1), ('sync', 2), ('sync', 3)
        ]
        assert len(state.streams) == 4  # Caller plus three owned streams.


@pytest.mark.parametrize('stage', ['read', 'compute', 'prepare', 'download', 'consume'])
def test_gpu_failure_cleanup(cuda, stage, monkeypatch):
    state, log = cuda

    def fail():
        raise RuntimeError(stage)

    class Reader:
        def read_frames(self, first_frame, batch_size):
            if stage == 'read':
                fail()
            return np.ones((1, 2, 2), dtype=np.float32)

    def process(frames, reference):
        if stage == 'compute':
            fail()
        return {'value': frames}, reference

    def prepare(result):
        if stage == 'prepare':
            fail()
        return result

    def consume(*args):
        if stage == 'consume':
            fail()

    if stage == 'download':
        monkeypatch.setattr(backend.xp.ndarray, 'get', lambda *args, **kwargs: fail())
    with pytest.raises(RuntimeError, match=stage):
        processing.run_batches(Reader(), list(range(8)), 1, process, consume,
                               prepare_result=prepare)
    assert [entry for entry in log if entry[0] == 'sync'] == [
        ('sync', 1), ('sync', 2), ('sync', 3)
    ]


def test_background_reads_overlap_compute(cuda):
    second_read = threading.Event()

    class Reader:
        def read_frames(self, first_frame, batch_size):
            if first_frame == 1:
                second_read.set()
            return np.ones((2, 2), dtype=np.float32)

    def process(frames, reference):
        assert second_read.wait(timeout=2)
        return {'value': frames}, reference

    processing.run_batches(Reader(), [0, 1], 1, process, lambda *args: None,
                           cupy_prefetch_depth=2)


@pytest.mark.parametrize('workers', [0, 2])
def test_cpu_preparation_and_registration(monkeypatch, workers):
    monkeypatch.setattr(processing, '_worker_count', lambda value: value)
    monkeypatch.setattr(backend, 'is_gpu', False)
    monkeypatch.setattr(backend, 'xp', np)
    monkeypatch.setattr(backend, 'to_backend', np.asarray)
    seen = []

    class Reader:
        def read_frames(self, first_frame, batch_size):
            return np.full((2, 2), first_frame, dtype=np.uint16)

    def process(frames, ref):
        assert frames.dtype == np.float32
        return {'value': frames + 1}, 7 if ref is None else ref

    result = processing.run_batches(
        Reader(), [0, 1, 2], 1, process,
        lambda index, value: seen.append((index, value['value'][0, 0, 0])),
        workers=workers, registration_enabled=True,
        prepare_result=lambda result: {'value': result['value'] * 2},
    )
    assert result == 7
    assert seen == [(0, 2), (1, 4), (2, 6)]


@pytest.mark.parametrize('settings,error', [
    ({'cupy_async': 1}, TypeError),
    ({'cupy_prefetch_depth': True}, TypeError),
    ({'cupy_prefetch_depth': 1.5}, TypeError),
    ({'cupy_prefetch_depth': 0}, ValueError),
])
def test_gpu_settings(settings, error):
    with pytest.raises(error):
        processing.run_batches(None, [], 1, None, None, **settings)


@pytest.mark.skipif(not backend.cupy_available, reason='CUDA device unavailable')
def test_real_cuda_matches_sequential():
    class Reader:
        def read_frames(self, first_frame, batch_size):
            return np.full((batch_size, 4, 4), first_frame + 1, dtype=np.uint16)

    def process(frames, ref):
        values = backend.xp.fft.fft2(frames).real
        reference = values[0].copy() if ref is None else ref
        return {'values': values + reference}, reference

    results = []
    for asynchronous in (False, True):
        output = []
        processing.run_batches(
            Reader(), list(range(7)), 2, process,
            lambda index, result: output.append(backend.to_numpy(result['values']).copy()),
            cupy_async=asynchronous, cupy_prefetch_depth=3,
            prepare_result=lambda result: {'values': result['values'] * 0.5},
        )
        results.append(output)
    np.testing.assert_allclose(results[0], results[1])


@pytest.mark.parametrize('save_spectrograms,save_average', [
    (False, False), (False, True), (True, False), (True, True),
])
def test_spectrogram_preparation_and_collection(monkeypatch, save_spectrograms, save_average):
    from scipy.ndimage import zoom
    from holodoppler.pipelines.main_default import (
        _append_numpy_results, _prepare_batch_results,
    )
    from holodoppler.core.image_utils import resize_frames

    monkeypatch.setattr(backend, 'is_gpu', False)
    monkeypatch.setattr(backend, 'xp', np)
    monkeypatch.setattr(backend, 'zoom', zoom)
    monkeypatch.setattr(backend, 'to_numpy', np.asarray)
    psd = np.arange(8 * 4 * 4, dtype=np.float32).reshape(8, 4, 4)
    params = {
        'save_spectograms': save_spectrograms,
        'save_averaged_spectrogram': save_average,
        'spectrogram_resize_shape': (2, 2),
        'spectrogram_resize_order': 1,
        'spectrogram_frequency_start': 0,
        'spectrogram_frequency_end': 0.25,
        'spectrogram_frequency_binning': 2,
    }
    output = {}
    for index in range(2):
        raw = {'sh_psd': psd + index, 'moment0': np.ones((4, 4)) * index}
        prepared = _prepare_batch_results(raw, params)
        assert 'sh_psd' in raw  # Preparation does not mutate the batch mapping.
        assert ('sh_psd' in prepared) == save_average
        assert ('spectrograms' in prepared) == save_spectrograms
        _append_numpy_results(output, prepared, params, index, 2)
    np.testing.assert_array_equal(output['moment0'][:, 0, 0], [0, 1])
    if save_average:
        np.testing.assert_array_equal(output['averaged_spectrogram'], 2 * psd + 1)
    if save_spectrograms:
        for index in range(2):
            resized = resize_frames(np, zoom, psd + index, 2, 2, order=1)
            expected = np.concatenate((resized[:2], resized[4:]), axis=0)
            expected = expected.reshape(3, 2, 2, 2).mean(axis=1)
            np.testing.assert_array_equal(output['spectrograms'][index], expected)


def test_config_defaults_and_validation():
    from pathlib import Path
    import contextlib
    import io
    import yaml
    from holodoppler.config.validation import validate_main_parameters

    root = Path(__file__).resolve().parents[1]
    defaults = yaml.safe_load((root / 'parameters/default_parameters_default.yaml').read_text())
    assert defaults['cupy_async'] is True
    assert defaults['cupy_prefetch_depth'] == 4
    params = {**defaults, 'z': 0.2, 'pixel_pitch': [1e-6, 1e-6], 'sampling_freq': 40000}
    with contextlib.redirect_stdout(io.StringIO()):
        validate_main_parameters(params)
        validate_main_parameters({key: value for key, value in params.items()
                                  if key not in ('cupy_async', 'cupy_prefetch_depth')})
    for key, value, error in [
        ('cupy_async', None, TypeError),
        ('cupy_prefetch_depth', True, TypeError),
        ('cupy_prefetch_depth', 0, ValueError),
    ]:
        with pytest.raises(error, match=key):
            validate_main_parameters({**params, key: value})


@pytest.mark.parametrize('device', ['numpy', 'cupy'])
@pytest.mark.parametrize('registration,fixed_phase', [(False, False), (True, True)])
def test_default_pipeline_scheduled_equivalence(device, registration, fixed_phase):
    from pathlib import Path
    import yaml
    from holodoppler.pipelines.main_default import (
        _process_one_batch, _prepare_batch_results, _append_numpy_results,
    )

    if device == 'cupy' and not backend.cupy_available:
        pytest.skip('CUDA device unavailable')
    previous = backend.get_backend_name()
    backend.set_backend(device)
    try:
        params = yaml.safe_load((Path(__file__).resolve().parents[1] /
                                 'parameters/default_parameters_default.yaml').read_text())
        params.update(
            z=0.2, pixel_pitch=(1e-6, 1e-6), sampling_freq=40000,
            batch_size=16, svd_threshold=1, filter2d=True,
            registration_flatfield_gw=1, image_registration=registration,
            spectrogram_resize_shape=[8, 8], spectrogram_frequency_start=0,
            spectrogram_frequency_end=0.25, spectrogram_frequency_binning=2,
        )
        data = np.random.default_rng(42).integers(0, 4096, (3, 16, 16, 16), dtype=np.uint16)

        class Reader:
            def read_frames(self, first_frame, batch_size):
                return data[first_frame].copy()

        outputs = []
        for asynchronous in (False, True):
            # Construct on the caller stream, as with a precomputed autofocus correction.
            phase = backend.xp.exp(-1j * backend.xp.full((16, 16), 0.2)) if fixed_phase else None
            output = {}
            processing.run_batches(
                Reader(), [0, 1, 2], 16,
                lambda frames, ref: _process_one_batch(params, frames, ref, phase),
                lambda index, result: _append_numpy_results(output, result, params, index, 3),
                registration_enabled=registration,
                workers=2 if asynchronous else 0,
                cupy_async=asynchronous, cupy_prefetch_depth=2,
                prepare_result=lambda result: _prepare_batch_results(result, params),
            )
            outputs.append(output)
        assert outputs[0].keys() == outputs[1].keys()
        for key in outputs[0]:
            np.testing.assert_allclose(outputs[0][key], outputs[1][key], rtol=1e-5, atol=1e-5,
                                       err_msg=key)
    finally:
        backend.set_backend(previous)
