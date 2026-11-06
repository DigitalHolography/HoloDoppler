"""Standalone synthetic default-pipeline saving investigation (no benchmark.py).

Run from the repository root with the project Python. Outputs and JSON metrics
are retained under profiling_default_saving. Each run generates all input
batches independently on demand, avoiding a 7.8 GiB resident input allocation.
"""
import faulthandler
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import psutil
import yaml
from holodoppler import backend
from holodoppler.pipelines import main_default as pipeline
from holodoppler.saving import OutputClass, data, media, policy


def summarize(root):
    rows = []
    for path in sorted(root.glob('*_b*.json')):
        d = json.loads(path.read_text())
        samples = d['samples']
        children = {}
        for sample in samples:
            for child in sample['children']:
                children[child['pid']] = max(children.get(child['pid'], 0), sum(child['cpu'][:2]))
        parent_cpu = sum(samples[-1]['cpu_times'][:2])-sum(samples[0]['cpu_times'][:2])
        row = dict(label=d['label'], wall_s=d['wall_s'], drain_s=d['final_drain_s'],
            batch_loop_s=d['timings'].get('run_batches', {}).get('wall_s'),
            submit_s=d['timings'].get('add_batch', {}).get('wall_s'),
            peak_rss_gib=max(x['rss'] for x in samples)/2**30,
            min_available_gib=min(x['available'] for x in samples)/2**30,
            gpu_avg=sum(x.get('gpu_util',0) for x in samples)/len(samples),
            gpu_peak_mib=max(x.get('gpu_mib',0) for x in samples),
            parent_cpu_cores=parent_cpu/d['wall_s'],
            encoder_cpu_cores_lower_bound=sum(children.values())/d['wall_s'],
            process_write_gib=(samples[-1]['io']['write_bytes']-samples[0]['io']['write_bytes'])/2**30,
            system_disk_write_gib=(samples[-1]['disk']['write_bytes']-samples[0]['disk']['write_bytes'])/2**30,
            output_gib=sum(d['output_bytes'].values())/2**30)
        rows.append(row)
    (root / 'summary.json').write_text(json.dumps(rows, indent=2))
    print(json.dumps(rows, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['full', 'h5', 'none', 'no-aggregate-media'], default='full')
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--batches', type=int, default=100)
    parser.add_argument('--frame-chunks', action='store_true', help='Experimental append-aligned HDF5 layout; benchmark only')
    parser.add_argument('--summarize', action='store_true')
    parser.add_argument('--disk-probe', action='store_true', help='Write and fsync 1 GiB in the benchmark directory')
    args = parser.parse_args()
    faulthandler.dump_traceback_later(90, repeat=True)
    root = Path('profiling_default_saving').resolve()
    root.mkdir(exist_ok=True)
    if args.summarize:
        summarize(root)
        return
    if args.disk_probe:
        block = np.random.default_rng(43).integers(0,256,64*1024*1024,dtype=np.uint8).tobytes()
        start = time.perf_counter()
        with (root / 'disk_probe.bin').open('wb', buffering=0) as handle:
            for _ in range(16):
                handle.write(block)
            written = time.perf_counter()
            os.fsync(handle.fileno())
        elapsed = time.perf_counter()-start
        result = dict(bytes=2**30, write_s=written-start, total_with_fsync_s=elapsed,
                      mib_per_s_with_fsync=1024/elapsed)
        (root / 'disk_probe.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
        return
    label = f'{args.mode}_w{args.workers}_b{args.batches}'
    if args.frame_chunks:
        label += '_framechunks'
    params = yaml.safe_load(Path('parameters/default_parameters_default.yaml').read_text())
    params.update(z=0.1, pixel_pitch=[20e-6, 20e-6], sampling_freq=50000,
                  num_saving_workers=args.workers, overwrite_option='overwrite')
    timings = defaultdict(lambda: dict(calls=0, wall_s=0., thread_cpu_s=0.))
    lock = threading.Lock()
    if args.frame_chunks:
        def append_frame(self, name, value, t):
            value = data.h5_value(value)
            with self.lock:
                if t == 0:
                    self.file.create_dataset(name, shape=(0, *value.shape),
                        maxshape=(None, *value.shape), dtype=value.dtype,
                        chunks=(1, *value.shape), **self._dataset_options(name))
                dataset = self.file[name]
                dataset.resize(t + 1, axis=0)
                dataset[t] = value
                self.file.flush()
        data.Hdf5Writer.append = append_frame

    def wrap(owner, name, labeler=None):
        original = getattr(owner, name)
        def measured(*a, **kw):
            key = labeler(*a, **kw) if labeler else name
            start, cpu = time.perf_counter(), time.thread_time()
            try:
                return original(*a, **kw)
            finally:
                elapsed, used = time.perf_counter()-start, time.thread_time()-cpu
                with lock:
                    row = timings[key]
                    row['calls'] += 1
                    row['wall_s'] += elapsed
                    row['thread_cpu_s'] += used
        setattr(owner, name, measured)

    for method in ['append', 'write_static']:
        wrap(data.Hdf5Writer, method, lambda self, name, *a, _m=method, **kw: f'h5.{_m}.{name}')
    wrap(media.MediaStream, 'append', lambda self, *a, **kw: f'media.append.{self.name}')
    wrap(media.MediaStream, 'close', lambda self, *a, **kw: f'media.close.{self.name}')
    wrap(media, 'save_video', lambda path, *a, **kw: f'video.{Path(path).name}')
    wrap(OutputClass, 'add_batch')
    wrap(OutputClass, 'write_static')
    wrap(OutputClass, 'close')
    wrap(pipeline, 'run_batches')
    original_formats = policy.output_formats
    def formats(name, value, **kw):
        result = original_formats(name, value, **kw)
        if args.mode == 'h5' or (args.mode == 'no-aggregate-media' and name == 'averaged_spectrogram'):
            return result.intersection({'h5', 'csv'})
        return result
    policy.output_formats = formats

    class Reader:
        file_path = root / 'synthetic.raw'
        extension = '.raw'
        total_frames = 256 * args.batches
        def read_frames(self, first_frame, batch_size, skip_every=None):
            start = time.perf_counter()
            value = np.random.default_rng(12345 + first_frame).integers(
                0, 4096, size=(batch_size, 320, 512), dtype=np.uint16)
            with lock:
                timings['synthetic_generation']['wall_s'] += time.perf_counter()-start
                timings['synthetic_generation']['calls'] += 1
            return value
    reader = Reader()
    pipeline.get_reader = lambda path: reader
    backend.set_backend('cupy')
    # Initialize CUDA before sampling and synchronize at the end of the run.
    backend.xp.zeros(1).sum().get()
    samples = []
    stop = threading.Event()
    proc = psutil.Process()
    def monitor():
        while not stop.is_set():
            row = dict(t=time.perf_counter(), rss=proc.memory_info().rss,
                       available=psutil.virtual_memory().available,
                       cpu_times=list(proc.cpu_times()), io=proc.io_counters()._asdict())
            children = []
            for child in proc.children(recursive=True):
                try:
                    children.append(dict(pid=child.pid, cpu=list(child.cpu_times()), rss=child.memory_info().rss))
                except psutil.Error:
                    pass
            row['children'] = children
            row['disk'] = psutil.disk_io_counters()._asdict()
            try:
                out = subprocess.check_output(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used',
                    '--format=csv,noheader,nounits'], text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                row['gpu_util'], row['gpu_mib'] = map(int, out.strip().split(','))
            except Exception:
                pass
            samples.append(row)
            stop.wait(0.5)
    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.start()
    start = time.perf_counter()
    destination = None
    try:
        _, prepared, indices = pipeline._prepare_input(reader.file_path, params)
        if args.mode == 'none':
            class Null:
                def add_batch(self, *a): pass
                def write_static(self, *a): pass
            destination = Null()
        else:
            destination = OutputClass(reader, prepared, custom_path=root / label)
        pipeline._process_to_output(reader, prepared, indices, destination, None)
        submitted = time.perf_counter()
        if hasattr(destination, 'close'):
            destination.close()
        backend.xp.cuda.get_current_stream().synchronize()
        end = time.perf_counter()
    finally:
        stop.set()
        monitor_thread.join()
    sizes = defaultdict(int)
    if (root / label).exists():
        for path in (root / label).rglob('*'):
            if path.is_file(): sizes[path.suffix] += path.stat().st_size
    result = dict(label=label, parameters=params, shape=[256*args.batches,320,512],
                  input_dtype='uint16', wall_s=end-start, submit_done_s=submitted-start,
                  final_drain_s=end-submitted, timings=dict(timings), samples=samples,
                  output_bytes=dict(sizes), peak_pending=getattr(getattr(destination,'_scheduler',None),'peak_pending',None))
    (root / f'{label}.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in {'parameters','samples','timings'}}, indent=2), flush=True)


if __name__ == '__main__':
    main()
