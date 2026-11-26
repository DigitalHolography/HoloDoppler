from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from holodoppler.config.pipelines.fast_config import FastConfig


def reader(extension):
    return SimpleNamespace(
        extension=extension, total_frames=24, frame_shape=(10, 10),
        footer={"compute_settings": {"image_rendering": {"lambda": 8e-7, "propagation_distance": .1}},
                "info": {"camera_fps": 120, "pixel_pitch": {"y": 2, "x": 3}}},
        header=SimpleNamespace(extra={"FrameRate": 120, "biYPelsPerMeter": 500000,
                                      "biXPelsPerMeter": 250000}),
    )


@pytest.mark.parametrize("extension", [".holo", ".cine"])
@pytest.mark.parametrize("placeholder", ["use_holovibes", "use_metadata"])
def test_metadata_aliases_and_immutable_snapshot(extension, placeholder):
    parameters = {"z": .2, "pixel_pitch": placeholder, "sampling_freq": placeholder,
                  "time_window": 4, "accu": 3, "outputs": {"moment0": ["h5"]}}
    config = FastConfig.from_parameters(parameters, reader(extension))
    assert config.pixel_pitch == pytest.approx((2e-6, 3e-6 if extension == ".holo" else 4e-6))
    assert config.sampling_freq == 120
    assert config.z == .2
    assert config.output_frame_stride == 12
    assert config.output_fps == 10
    assert parameters["pixel_pitch"] == placeholder
    parameters["outputs"]["moment0"].append("png")
    assert config.as_dict()["outputs"] == {"moment0": ["h5"]}
    with pytest.raises(FrozenInstanceError):
        config.accu = 1
    with pytest.raises(TypeError):
        FastConfig()


def test_holo_optics_and_missing_metadata():
    p = {"z": "use_metadata", "wavelength": "use_metadata", "pixel_pitch": 1e-6,
         "sampling_freq": 120}
    config = FastConfig.from_parameters(p, reader(".holo"))
    assert config.z == .1
    assert config.wavelength == 8e-7
    with pytest.raises(ValueError, match="z"):
        FastConfig.from_parameters(p, reader(".cine"))
    missing = reader(".holo")
    missing.footer = None
    with pytest.raises(ValueError, match="z"):
        FastConfig.from_parameters(p, missing)


@pytest.mark.parametrize("override, match", [
    ({"time_window": 0}, "time_window"),
    ({"time_window": 4, "svd_filter": 4}, "svd_filter"),
    ({"time_window": 4, "frequency_ranges": [[0, 5]]}, "frequency_ranges"),
    ({"time_window": 4, "mode": "pca", "svd_filter": 1}, "only available"),
    ({"h5compression": 10}, "h5compression"),
    ({"num_saving_workers": -1}, "num_saving_workers"),
])
def test_invalid_config(override, match):
    p = {"z": .1, "pixel_pitch": 1e-6, "sampling_freq": 120, **override}
    with pytest.raises(ValueError, match=match):
        FastConfig.from_parameters(p, reader(".holo"))
