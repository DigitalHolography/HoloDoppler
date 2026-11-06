"""Packet-averaged PCA images with registration on accumulated outputs."""

from numbers import Integral, Real

from holodoppler import backend
from holodoppler.core.filtering import filter_2d, pca_packet_mean
from holodoppler.core.image_utils import gaussian_flatfield
from holodoppler.core.pipeline import prepare_input, run_pipeline
from holodoppler.core.propagation import angular_spectrum_transform, fresnel_transform
from holodoppler.core.registration import apply_register_images_shifts, register_images_shifts


def _validate_parameters(parameters):
    for key in ("batch_size", "accumulation", "batch_stride"):
        value = parameters.get(key, 1)
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError(f"{key} must be a positive integer")
        if value <= 0:
            raise ValueError(f"{key} must be positive")
    bounds = parameters["pca_range"]
    if (not isinstance(bounds, (list, tuple)) or len(bounds) != 2
            or any(isinstance(v, bool) or not isinstance(v, Integral) for v in bounds)):
        raise TypeError("pca_range must contain two integers")
    if not 0 <= bounds[0] < bounds[1] <= parameters["batch_size"]:
        raise ValueError("pca_range must satisfy 0 <= start < end <= batch_size")


def _process_batch(parameters, frames):
    """Average unregistered packet sums, then flatfield the accumulated image."""
    xp, fft = backend.xp, backend.fft
    if parameters.get("filter2d", False):
        frames = filter_2d(xp, fft, frames, parameters["filter2d_low"])

    method = parameters["spatial_propagation"]
    args = (xp, fft, frames, parameters["z"], parameters["pixel_pitch"],
            parameters["wavelength"])
    if method == "Fresnel":
        holograms = fresnel_transform(
            *args, use_output_kernel=parameters["Fresnel_use_ouput_kernel"])
    elif method == "AngularSpectrum":
        holograms = angular_spectrum_transform(*args)
    else:
        raise ValueError(f"Unknown propagation method: {method!r}")

    image = pca_packet_mean(xp, holograms, parameters["batch_size"], parameters["pca_range"])
    return {
        "pca_sum": image,
        "pca_sum_ff": gaussian_flatfield(
            image, parameters.get("registration_flatfield_gw", 1.0), backend.gaussian_filter),
    }


def _process_one_batch(parameters, frames, registration_ref=None):
    result = _process_batch(parameters, frames)
    if parameters.get("image_registration", False):
        if registration_ref is None:
            # Copy before shifting either output; this reference stays fixed.
            registration_ref = result["pca_sum_ff"].copy()
        shift_y, shift_x = register_images_shifts(
            backend.xp, backend.fft, registration_ref, result["pca_sum_ff"],
            radius=parameters.get("registration_radius", .8),
            sub_pixel=parameters.get("registration_sub_pixel", True),
        )
        for key in ("pca_sum", "pca_sum_ff"):
            result[key] = apply_register_images_shifts(
                backend.xp, result[key], shift_y=shift_y, shift_x=shift_x,
                fft=backend.fft,
                block_size_mib=parameters.get("registration_block_size_mib", 8),
            )
        result["registration"] = backend.xp.stack(
            [backend.xp.asarray(shift_y), backend.xp.asarray(shift_x)])
    return result, registration_ref


def _run(file_path, parameters, preview=False, progress_callback=None, *, save_output=True):
    _validate_parameters(parameters)
    reader, p = prepare_input(file_path, parameters)
    p["output_frame_stride"] = p["batch_stride"]
    if isinstance(p.get("sampling_freq"), Real):
        p.setdefault("output_fps", p["sampling_freq"] / p["batch_stride"])

    def process_batch(frames, reference):
        return _process_one_batch(p, frames, registration_ref=reference)

    return run_pipeline(
        reader, p, process_batch, preview=preview, preview_key="pca_sum_ff",
        read_batch_size=p["batch_size"] * p.get("accumulation", 1),
        ecc_keys={"pca_sum", "pca_sum_ff"},
        progress_callback=progress_callback, save_output=save_output,
    )


def preview(file_path, parameters, *, save_outputs=True):
    return _run(file_path, parameters, preview=True, save_output=save_outputs)


def process(file_path, parameters, progress_callback=None):
    return _run(file_path, parameters, progress_callback=progress_callback)
