"""Numerical Shack-Hartmann diagnostics and autofocus rejection."""
from types import SimpleNamespace
from unittest.mock import Mock

import h5py
import numpy as np
import pytest

from holodoppler import backend, saving
from holodoppler.saving import data as saving_data
from holodoppler.core.shack_hartmann import calculate_displacements, calculate_displacements_graph_laplacian
from holodoppler.pipelines import main_default


@pytest.mark.parametrize("small", [False, True])
def test_graph_intermediates(small):
    rng = np.random.default_rng(12)
    image = rng.normal(size=(32, 32))
    images = np.stack([np.roll(image, i, axis=0) for i in range(9)]).reshape(3, 3, 32, 32)
    diagnostics = {}
    y, x = calculate_displacements_graph_laplacian(
        np, np.fft, images, pupil_threshold=0 if small else 3,
        shifts_range=20, deviation_threshold=100, diagnostics=diagnostics)
    assert set(diagnostics) == {"shack_hartmann_shifts"}
    pairs = diagnostics["shack_hartmann_shifts"]
    assert pairs.shape == (3, 3, 3, 3, 2)
    assert pairs.dtype == np.float32
    if small:
        assert np.isnan(y).all()
        assert np.isnan(pairs).all()
    else:
        assert pairs[0, 0, 0, 1, 0] == pytest.approx(1, abs=.01)
        assert pairs[0, 1, 0, 0, 0] == pytest.approx(-1, abs=.01)
        assert np.isnan(pairs[0, 0, 0, 0]).all()
        np.testing.assert_allclose(y, np.arange(9).reshape(3, 3) - 4, atol=.01)


def test_reference_shifts():
    image = np.random.default_rng(2).normal(size=(32, 32))
    images = np.stack([np.roll(image, i, axis=0) for i in range(6)]).reshape(2, 3, 32, 32)
    diagnostics = {}
    y, x = calculate_displacements(np, np.fft, images, pupil_threshold=3,
                                    deviation_threshold=100, diagnostics=diagnostics)
    assert set(diagnostics) == {"shack_hartmann_shifts"}
    shifts = diagnostics["shack_hartmann_shifts"]
    assert shifts.shape == (2, 3, 2)
    assert shifts.dtype == np.float32
    np.testing.assert_equal(shifts[..., 0], y)
    np.testing.assert_equal(shifts[..., 1], x)


@pytest.mark.parametrize("z4, accepted", [(1.49, True), (1.5, True), (-1.5, True), (1.51, False), (-1.51, False), (np.nan, False)])
@pytest.mark.parametrize("failure", [None, "missing_z4", "nonfinite_phase"])
@pytest.mark.parametrize("modes", [[4, 5, 6], [6, 4, 5]])
def test_autofocus_guard(monkeypatch, z4, accepted, modes, failure):
    monkeypatch.setattr(backend, "to_backend", np.asarray)
    monkeypatch.setattr(backend, "to_numpy", np.asarray)
    monkeypatch.setattr(backend, "xp", np)
    values = np.zeros(3)
    values[modes.index(4)] = z4
    phase_values = np.zeros((2, 2))
    if failure == "missing_z4":
        modes = [7, 5, 6]
        accepted = False
    elif failure == "nonfinite_phase":
        phase_values[0, 0] = np.nan
        accepted = False
    warning = Mock()
    monkeypatch.setattr(main_default.logger, "warning", warning)
    def sense(parameters, frames, output_dict, diagnostics):
        output_dict.update(shack_hartmann_zernike_coefs=values,
                           shack_hartmann_wavefront_phase=phase_values,
                           shack_hartmann_shifts=np.ones((2, 2, 2), dtype=np.float32))
        return np.ones((2, 2), dtype=complex)
    monkeypatch.setattr(main_default, "_process_shack_hartmann", sense)
    reader = SimpleNamespace(total_frames=4, read_frames=Mock(return_value=np.ones((4, 2, 2))))
    params = dict(shack_hartmann_autofocus=True, registration_ref_first_frame=0,
                  batch_size=4, shack_hartmann_zernike_fit_modes=modes)
    diagnostics = {}
    phase, coefs = main_default._get_autofocus_phase_term(params, reader, diagnostics)
    assert warning.call_count == (0 if accepted else 1)
    assert (phase is not None) == accepted
    assert set(diagnostics) == {"autofocus_shack_hartmann_shifts"}
    np.testing.assert_equal(diagnostics["autofocus_shack_hartmann_shifts"], np.ones((2, 2, 2)))


@pytest.mark.parametrize("name", ["shack_hartmann_shifts", "autofocus_shack_hartmann_shifts", "spectrum_line"])
@pytest.mark.parametrize("streaming", [False, True])
def test_diagnostic_h5(tmp_path, monkeypatch, streaming, name):
    monkeypatch.setattr(saving_data, "get_git_version", lambda: "test")
    values = np.array([np.nan, 2, -2, np.inf, -np.inf, 0], dtype=np.float32)
    if name != "spectrum_line":
        values = values.reshape(1, 3, 2)
    if streaming:
        reader = SimpleNamespace(file_path=tmp_path / "input.raw")
        with saving.OutputClass(reader, {"sampling_freq": 1000, "batch_stride": 4}, custom_path=tmp_path) as destination:
            destination.add_batch({name: values}, 0)
            destination.write_static("averaged_spectrogram", values.reshape(-1))
        path = next(tmp_path.rglob("*.h5"))
    else:
        path = saving.save_h5(tmp_path, {name: values})
    with h5py.File(path) as h5:
        np.testing.assert_equal(h5[name][0] if streaming else h5[name][:], values)
        if streaming:
            np.testing.assert_equal(h5["averaged_spectrogram"][:], values.reshape(-1))
    assert not list(tmp_path.rglob("*.png"))
    assert not list(tmp_path.rglob("*.mp4"))
    if streaming and name.endswith("shack_hartmann_shifts"):
        csv_path = next(tmp_path.rglob(name + ".csv"))
        np.testing.assert_equal(np.loadtxt(csv_path, delimiter=",").reshape(values.shape), values)


@pytest.mark.parametrize("threshold", [0, -1, np.nan, np.inf, True, "1.5"])
def test_invalid_threshold(threshold):
    from holodoppler.config.validation import validate_main_parameters
    import yaml
    from pathlib import Path
    parameters = yaml.safe_load((Path(__file__).resolve().parents[1] / "parameters/default_parameters_default.yaml").read_text())
    parameters.update(sampling_freq=1000, z=.1, wavelength=852e-9, pixel_pitch=[1e-6, 1e-6], spatial_propagation="Fresnel",
                      shack_hartmann_autofocus_z4_threshold_rad=threshold)
    with pytest.raises((TypeError, ValueError), match="shack_hartmann_autofocus_z4_threshold_rad"):
        validate_main_parameters(parameters)


def test_rejected_autofocus_does_not_fall_back_to_live(monkeypatch):
    sense = Mock(side_effect=AssertionError("live correction must not run"))
    process = Mock()
    monkeypatch.setattr(main_default, "_process_shack_hartmann", sense)
    monkeypatch.setattr(main_default, "_process_batch", process)
    frames = np.ones((4, 2, 2))
    main_default._process_one_batch(
        {"shack_hartmann_autofocus": True, "shack_hartmann": True}, frames,
        phase_term=None)
    sense.assert_not_called()
    assert process.call_args.kwargs["phase_term"] is None


def test_rejected_pairs_are_nan():
    rng = np.random.default_rng(21)
    image = rng.normal(size=(32, 32))
    images = np.stack([np.roll(image, i, axis=0) for i in range(9)]).reshape(3, 3, 32, 32)
    diagnostics = {}
    calculate_displacements_graph_laplacian(
        np, np.fft, images, pupil_threshold=3, shifts_range=.1,
        diagnostics=diagnostics)
    assert np.isnan(diagnostics["shack_hartmann_shifts"][0, 0, 0, 1]).all()


@pytest.mark.parametrize("shape", [(2, 3, 2), (2, 3, 2, 3, 2), (4, 2, 3, 2, 3, 2)])
def test_multidimensional_shift_csv(tmp_path, shape):
    values = np.arange(np.prod(shape), dtype=np.float32).reshape(shape)
    values.flat[0] = np.nan
    path = tmp_path / "shifts.csv"
    saving.save_csv(path, values)
    np.testing.assert_equal(np.loadtxt(path, delimiter=",").reshape(shape), values)


def test_shift_bundle_csv_job(tmp_path):
    values = np.full((2, 3, 2, 3, 2), np.nan, dtype=np.float32)
    jobs = list(saving._bundle_saving_jobs(
        tmp_path, None, {"autofocus_shack_hartmann_shifts": values}, {}, 1, False))
    assert jobs[0][0] is saving.save_csv
    assert all(job[0] not in (saving.save_png, saving.save_video) for job in jobs)
