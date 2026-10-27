"""Lifecycle hooks preserve output ordering, static values and failure cleanup."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from holodoppler import backend
from holodoppler.core import pipeline


@pytest.fixture(autouse=True)
def numpy_backend():
    previous = backend.get_backend_name()
    backend.set_backend("numpy")
    yield
    backend.set_backend(previous)


def reader():
    return SimpleNamespace(
        total_frames=3,
        read_frames=lambda first_frame, **kw: np.full((1, 2, 3), first_frame, np.float32),
    )


def parameters(**changes):
    return dict(batch_size=1, batch_stride=1, first_frame=0, numpy_num_workers=0,
                **changes)


@pytest.mark.parametrize("live", [False, True])
@pytest.mark.parametrize("ecc", [False, True])
def test_hook_order_and_static_output(monkeypatch, tmp_path, live, ecc):
    events, temporal, static = [], [], {}

    class Destination:
        target_dir = tmp_path

        def add_batch(self, result, index):
            events.append(("save", index))
            temporal.append(result)

        def write_static(self, key, value):
            static[key] = value

    def save_bundle(**kwargs):
        output = kwargs["output"]
        for index in range(3):
            temporal.append({key: output[key][index] for key in
                             ("moment0ff", "spectrograms", "rendered")})
        static["aggregate"] = output["aggregate"]
        return tmp_path

    monkeypatch.setattr(pipeline, "save_outputs", save_bundle)

    def process(frames, reference):
        value = int(frames[0, 0, 0])
        events.append(("process", value))
        return {"moment0ff": frames[0], "spectrograms": frames.copy()}, reference

    def prepare(result):
        events.append(("prepare", int(result["moment0ff"][0, 0])))
        return result

    def consume(result):
        events.append(("consume", int(result["moment0ff"][0, 0])))
        return result

    def estimate(images, **kwargs):
        events.append(("ecc", len(images)))
        assert images.shape == (3, 2, 3)
        return np.repeat(np.eye(2, 3)[None], 3, axis=0)

    warped = []

    def warp(images, *args, **kwargs):
        warped.append(images.shape)
        return images + 10

    monkeypatch.setattr(pipeline, "register_with_ecc", estimate)
    monkeypatch.setattr(pipeline, "apply_ecc_registration", warp)

    def finalize(result):
        value = int(result["moment0ff"][0, 0])
        events.append(("render", value))
        return {**result, "rendered": result["moment0ff"] * 2}

    def finish(completed):
        events.append(("static", completed))
        assert completed == 3
        return {"aggregate": np.full((5, 2, 3), 42)}

    pipeline.run_pipeline(
        reader(), parameters(live_saving=live, image_registration_with_ecc=ecc), process,
        # Explicit indices bypass reader-based schedule selection.
        indices=[0, 1, 2], prepare_batch=prepare, consume_batch=consume,
        finalize_result=finalize, ecc_key_predicate=lambda key: key == "moment0ff",
        static_factory=finish, destination=Destination() if live else None,
    )
    assert warped == ([(3, 2, 3)] if ecc else [])
    for index, result in enumerate(temporal):
        np.testing.assert_array_equal(result["moment0ff"], index + (10 if ecc else 0))
        np.testing.assert_array_equal(result["rendered"], 2 * (index + (10 if ecc else 0)))
        np.testing.assert_array_equal(result["spectrograms"], index)
    assert static["aggregate"].shape == (5, 2, 3)
    if ecc:
        assert events.index(("ecc", 3)) > events.index(("consume", 2))
        assert events.index(("render", 10)) > events.index(("ecc", 3))
    else:
        assert events.index(("prepare", 0)) < events.index(("render", 0))
        assert events.index(("render", 0)) < events.index(("consume", 0))
    assert events.index(("static", 3)) > events.index(("consume", 2))
    if ecc:
        assert events.index(("static", 3)) < events.index(("ecc", 3))


@pytest.mark.parametrize("failure", ["prepare", "consume", "ecc", "finalize", "static", "saving"])
def test_hook_failures_abort_managed_destination(monkeypatch, tmp_path, failure):
    exits = []

    class Destination:
        target_dir = tmp_path

        def __init__(self, *args):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            exits.append(exc)

        def add_batch(self, result, index):
            if failure == "saving":
                raise RuntimeError(failure)

        def write_static(self, *args):
            pass

    def hook(stage, value):
        if stage == failure:
            raise RuntimeError(stage)
        return value

    monkeypatch.setattr(pipeline, "OutputClass", Destination)
    monkeypatch.setattr(pipeline, "register_with_ecc", lambda images, **kw:
                        hook("ecc", np.zeros((3, 2, 3))))
    monkeypatch.setattr(pipeline, "apply_ecc_registration", lambda images, *args, **kw: images)
    with pytest.raises(RuntimeError, match=failure):
        pipeline.run_pipeline(
            reader(), parameters(image_registration_with_ecc=True),
            lambda frames, ref: ({"moment0ff": frames[0]}, ref),
            prepare_batch=lambda result: hook("prepare", result),
            consume_batch=lambda result: hook("consume", result),
            finalize_result=lambda result: hook("finalize", result),
            static_factory=lambda completed: hook("static", {}),
        )
    assert len(exits) == 1
    assert isinstance(exits[0], RuntimeError)


def test_prepare_input_copy_policy(monkeypatch):
    file_reader = SimpleNamespace(extension=".holo", footer={})
    monkeypatch.setattr(pipeline, "get_reader", lambda path: file_reader)
    monkeypatch.setattr(pipeline, "validate_main_parameters", lambda p: None)

    def resolve(parameters, footer):
        parameters["resolved"] = True
        return parameters

    monkeypatch.setattr(pipeline, "update_from_holo_footer", resolve)
    original = {"backend": "numpy"}
    _, copied = pipeline.prepare_input(Path("input.holo"), original)
    assert copied["resolved"]
    assert "resolved" not in original
    _, mutable = pipeline.prepare_input(Path("input.holo"), original, copy_parameters=False)
    assert mutable is original
    assert original["resolved"]


def test_generic_buffering_keeps_only_present_optional_values(monkeypatch, tmp_path):
    saved = {}
    monkeypatch.setattr(pipeline, "save_outputs", lambda **kw:
                        saved.update(kw["output"]) or tmp_path)

    def process(frames, reference):
        value = int(frames[0, 0, 0])
        return {"moment0ff": frames[0],
                "optional": frames[0] if value != 1 else None}, reference

    pipeline.run_pipeline(reader(), parameters(live_saving=False), process)
    assert saved["moment0ff"].shape == (3, 2, 3)
    np.testing.assert_array_equal(saved["optional"][:, 0, 0], [0, 2])
