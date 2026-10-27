import numpy as np

from holodoppler import backend
from holodoppler.core.doppler_images import directional, finish_doppler_images
from holodoppler.core.filtering import (
    corner_compensation,
    filter_2d,
    fourier_time_transform,
    frequency_symmetric_filtering,
    symmetric_frequency_slices,
    svd_filter,
)
from holodoppler.core.image_utils import (
    gaussian_flatfield,
    resize_frames,
)
from holodoppler.core.moments import moments
from holodoppler.core.pipeline import (
    _MANAGED_DESTINATION,
    batch_indices as get_batch_indices,
    frame_stack as _frame_stack,
    prepare_input,
    run_pipeline,
    save_result_bundle,
    validate_reference_batch as _validate_reference_batch,
)
from holodoppler.core.plots import plot_phase_with_slopes_rgb
from holodoppler.core.propagation import (
    angular_spectrum_transform,
    angular_spectrum_transform_with_phase,
    build_fresnel_kernel_in,
    fresnel_transform,
    fresnel_transform_with_phase,
)
from holodoppler.core.registration import (
    apply_register_images_shifts,
    register_images_shifts,
)
from holodoppler.core.shack_hartmann import (
    calculate_displacements,
    calculate_displacements_graph_laplacian,
    construct_subapertures_angular,
    construct_subapertures_fresnel,
)
from holodoppler.core.zernike import (
    fit_zernike_angular_spectrum,
    fit_zernike_fresnel,
)
from holodoppler.logging import logger


def _process_batch(parameters, frames, phase_term=None, output_dict=None,
                   reference_only=False, propagation_kernel=None):
    xp = backend.xp
    fft = backend.fft

    nt_sub = frames.shape[0]
    prop_method = parameters["spatial_propagation"]

    # ------------------------------------------------------------
    # Spatial propagation
    # ------------------------------------------------------------
    if propagation_kernel is not None:
        holograms = fresnel_transform(
            xp, fft, frames, parameters["z"], parameters["pixel_pitch"],
            parameters["wavelength"],
            use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
            input_kernel=propagation_kernel,
        )
    elif phase_term is not None:
        if prop_method == "Fresnel":
            holograms = fresnel_transform_with_phase(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
                phase_term,
                use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
            )

        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform_with_phase(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
                phase_term,
            )

        else:
            raise ValueError(
                f"Unknown propagation method: {prop_method!r}"
            )

    else:
        if prop_method == "Fresnel":
            holograms = fresnel_transform(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
                use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
            )

        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
            )

        else:
            raise ValueError(
                f"Unknown propagation method: {prop_method!r}"
            )

    # ------------------------------------------------------------
    # SVD filtering
    # ------------------------------------------------------------
    holograms_f = svd_filter(
        backend.xp, backend.linalg, holograms.astype(xp.complex64, copy=False),
        parameters["svd_threshold"],
        filter_mode=parameters["svd_filter_mode"],
        remove_dc=parameters["svd_remove_dc"],
        block_size_mib=parameters.get("svd_block_size_mib", 8),
    )

    del holograms

    if output_dict is None:
        output_dict = {}

    # ------------------------------------------------------------
    # Temporal Fourier transform
    # ------------------------------------------------------------
    spectrum_f = fourier_time_transform(
        xp,
        fft,
        holograms_f,
    )
    del holograms_f

    psd = xp.abs(spectrum_f)
    del spectrum_f
    xp.square(psd, out=psd)

    # ------------------------------------------------------------
    # Frequency filtering
    # ------------------------------------------------------------
    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

    if not reference_only and parameters.get("directional_Doppler_image", False):
        band = parameters.get("directional_Doppler_frequency_band") or (
            parameters["low_freq"], parameters.get("high_freq"))
        output_dict["_directional_Doppler_pos"], output_dict["_directional_Doppler_neg"] = directional(
            xp, backend.gaussian_filter, psd, *band,
            parameters["sampling_freq"] / (parameters.get("skip_every") or 1),
            parameters.get("directional_Doppler_gaussian_width", 35.),
        )

    fs = parameters["sampling_freq"] / (parameters.get("skip_every") or 1)
    orders = [0] if reference_only else [0, 1, 2]
    indices, selected_freqs = frequency_symmetric_filtering(
        xp, fft, nt_sub, fs, parameters["low_freq"], parameters.get("high_freq"),
    )
    images = moments(xp, psd[indices], selected_freqs, orders)
    output_dict.update(zip(("moment0", "moment1", "moment2"), images))
    if reference_only:
        output_dict["moment0ff"] = gaussian_flatfield(
            output_dict["moment0"], parameters.get("registration_flatfield_gw", 1.0),
            backend.gaussian_filter,
        )
        return output_dict

    output_dict["spectrum_line"] = xp.mean(
        psd,
        axis=(-2, -1),
    )

    if parameters.get("color_Doppler_image", False):
        for name, default in (("low", [3000, 9000]), ("high", [9000, 18000])):
            band = parameters.get(f"color_Doppler_{name}_frequency_band", default)
            output_dict[f"_color_Doppler_{name}"] = _band_moments(
                psd, fs, *band, [0])[0]

    if parameters.get("save_spectograms",False) or parameters.get("save_averaged_spectrogram",False):
        output_dict["sh_psd"] = psd # the power spectrum density

    # ------------------------------------------------------------
    # Frequency bands
    # ------------------------------------------------------------
    for k, (f1, f2) in enumerate(
        parameters.get("frequency_bands", [])
    ):
        slices = symmetric_frequency_slices(nt_sub, fs, f1, f2)
        count = sum(part.stop - part.start for part in slices)
        summed = _band_moments(psd, fs, f1, f2, [0])[0]
        output_dict[f"band_{k}_{f1}_{f2}"] = (
            summed / count if count else xp.full_like(summed, xp.nan)
        )

    for k, (f1, f2) in enumerate(parameters.get("moments_frequency_ranges") or ()):
        band_moments = _band_moments(psd, fs, f1, f2, [0, 1])
        for order, image in enumerate(band_moments):
            suffix = f"range_{k}_{f1}_{f2}"
            output_dict[f"moment{order}_{suffix}"] = image
        image = band_moments[0]
        output_dict[f"moment0ff_{suffix}"] = gaussian_flatfield(
            image, parameters.get("registration_flatfield_gw", 1.0),
            backend.gaussian_filter,
        )

    del psd

    output_dict["moment0ff"] = gaussian_flatfield(
        output_dict["moment0"],
        parameters.get("registration_flatfield_gw", 1.0),
        backend.gaussian_filter,
    )

    return output_dict


def _fixed_fresnel_kernel(parameters, phase_term):
    """Build the fixed corrected input kernel before scheduling any batches."""
    if phase_term is None or parameters["spatial_propagation"] != "Fresnel":
        return None
    ny, nx = phase_term.shape[-2:]
    return (build_fresnel_kernel_in(
        backend.xp, parameters["z"], tuple(parameters["pixel_pitch"]),
        parameters["wavelength"], ny, nx,
    ) * phase_term).astype(backend.xp.complex64, copy=False)


def _band_moments(psd, sampling_freq, low, high, orders):
    """Keep legacy moment precision/order; use slice sums for plain band power."""
    xp = backend.xp
    if orders != [0]:
        indices, selected_freqs = frequency_symmetric_filtering(
            xp, backend.fft, psd.shape[0], sampling_freq, low, high,
        )
        return moments(xp, psd[indices], selected_freqs, orders)

    image = xp.zeros(psd.shape[1:], dtype=psd.dtype)
    for part in symmetric_frequency_slices(psd.shape[0], sampling_freq, low, high):
        image += xp.sum(psd[part], axis=0)
    return [image]


def _process_shack_hartmann(
    parameters,
    frames,
    output_dict=None,
    diagnostics=None,
):
    """
    Compute Shack-Hartmann displacements and fit the Zernike wavefront.

    Returns
    -------
    phase_term : backend array or None
        Complex phase correction term exp(-1j * phase).
    """

    xp = backend.xp
    fft = backend.fft

    _, ny, nx = frames.shape
    prop_method = parameters["spatial_propagation"]

    # ------------------------------------------------------------
    # Construct Shack-Hartmann subapertures
    # ------------------------------------------------------------
    if prop_method == "Fresnel":
        U = construct_subapertures_fresnel(
            xp,
            fft,
            frames,
            parameters["wavelength"],
            parameters["z"],
            parameters["pixel_pitch"],
            parameters["low_freq"],
            parameters.get("high_freq"),
            parameters["sampling_freq"] / (parameters.get("skip_every") or 1),
            frames.shape[0],
            parameters["shack_hartmann_nx_subap"],
            parameters["shack_hartmann_ny_subap"],
            parameters["shack_hartmann_svd_threshold"],
            sub_aps_process=parameters.get("shack_hartmann_sub_aps_process", "sequential"),
            svd_block_size_mib=parameters.get("svd_block_size_mib", 8),
            svd_regularization=parameters.get("shack_hartmann_svd_regularization", 1e-12),
        )

    elif prop_method == "AngularSpectrum":
        U = construct_subapertures_angular(
            xp,
            fft,
            frames,
            parameters["wavelength"],
            parameters["z"],
            parameters["pixel_pitch"],
            parameters["low_freq"],
            parameters.get("high_freq"),
            parameters["sampling_freq"] / (parameters.get("skip_every") or 1),
            frames.shape[0],
            parameters["shack_hartmann_nx_subap"],
            parameters["shack_hartmann_ny_subap"],
            parameters["shack_hartmann_svd_threshold"],
            sub_aps_process=parameters.get("shack_hartmann_sub_aps_process", "sequential"),
            svd_block_size_mib=parameters.get("svd_block_size_mib", 8),
            svd_regularization=parameters.get("shack_hartmann_svd_regularization", 1e-12),
        )

    else:
        raise ValueError(
            f"Unknown propagation method: {prop_method!r}"
        )

    # ------------------------------------------------------------
    # Calculate Shack-Hartmann displacements
    # ------------------------------------------------------------
    shift_diagnostics = {} if output_dict is not None else None
    if parameters.get("shack_hartmann_graph_laplacian", False):
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            xp,
            fft,
            U,
            diagnostics=shift_diagnostics,
            pupil_threshold=parameters.get(
                "shack_hartmann_pupil_threshold",
                1.0,
            ),
            deviation_threshold=parameters.get(
                "shack_hartmann_deviation_threshold",
                3.0,
            ),
            shifts_range=parameters.get(
                "shack_hartmann_shifts_pixel_range_threshold",
                20.0,
            ),
        )

    else:
        shifts_y, shifts_x = calculate_displacements(
            xp,
            fft,
            U,
            diagnostics=shift_diagnostics,
            pupil_threshold=parameters.get(
                "shack_hartmann_pupil_threshold",
                1.0,
            ),
            deviation_threshold=parameters.get(
                "shack_hartmann_deviation_threshold",
                3.0,
            ),
            shifts_range=parameters.get(
                "shack_hartmann_shifts_pixel_range_threshold",
                20.0,
            ),
        )

    # ------------------------------------------------------------
    # Optional diagnostic output
    # ------------------------------------------------------------
    if output_dict is not None:
        output_dict.update(shift_diagnostics or {})
        sy, sx, numy, numx = U.shape

        U = xp.transpose(
            U,
            axes=(0, 2, 1, 3),
        )

        output_dict["shack_hartmann_sub_images"] = xp.reshape(
            U,
            (numy * sy, numx * sx),
        )

    del U

    # ------------------------------------------------------------
    # Zernike fit
    # ------------------------------------------------------------
    phase = None

    if parameters.get("shack_hartmann_zernike_fit", True):

        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                xp,
                ny,
                nx,
                parameters["pixel_pitch"][0],
                parameters["pixel_pitch"][1],
                parameters["wavelength"],
                shifts_y,
                shifts_x,
                parameters.get("shack_hartmann_zernike_fit_modes"),
            )

        else:
            coefs, phase = fit_zernike_angular_spectrum(
                xp,
                ny,
                nx,
                parameters["pixel_pitch"][0],
                parameters["pixel_pitch"][1],
                parameters["wavelength"],
                parameters["z"],
                shifts_y,
                shifts_x,
                parameters.get("shack_hartmann_zernike_fit_modes"),
            )

        if output_dict is not None:
            output_dict["shack_hartmann_zernike_coefs"] = coefs
            output_dict["shack_hartmann_wavefront_phase"] = phase

    if phase is None:
        return None

    if diagnostics is not None:
        diagnostics["shack_hartmann_autofocus_wavefront_color_image"] = (
            plot_phase_with_slopes_rgb(
                backend.to_numpy(phase),
                backend.to_numpy(shifts_y),
                backend.to_numpy(shifts_x),
            )
        )

    # ------------------------------------------------------------
    # Convert phase to correction term
    # This is the fixed wavefront correction that will be reused
    # for all following batches when autofocus is enabled.
    # ------------------------------------------------------------
    phase_term = xp.exp(-1j * phase.astype(xp.float32, copy=False))

    return xp.nan_to_num(
        phase_term,
        nan=0.0,
    )


def _get_autofocus_phase_term(parameters, file_reader, diagnostics=None,
                              reference_frames=None):
    """
    Compute the Shack-Hartmann autofocus correction once from
    the configured reference batch.

    When diagnostics is supplied, populate it with an RGB phase-and-shifts
    image, kept separate from the normal batch outputs.

    Reference batch:
        start = registration_ref_first_frame
        size  = shack_hartmann_autofocus_batch_size (defaults to batch_size)
        reference_frames optionally supplies the already-read raw reference.

    Returns
    -------
    phase_term, coefs : tuple
        Fixed phase correction and fitted coefficients, or (None, None)
        when autofocus is disabled.
    """

    if not parameters.get("shack_hartmann_autofocus", False):
        return None, None

    ref_first_frame = parameters["registration_ref_first_frame"]
    ref_batch_size = parameters.get(
        "shack_hartmann_autofocus_batch_size", parameters["batch_size"]
    )

    logger.info(
        "Running Shack-Hartmann autofocus from reference batch: first_frame=%s, autofocus_batch_size=%s",
        ref_first_frame, ref_batch_size,
    )

    _validate_reference_batch(
        file_reader, ref_first_frame, ref_batch_size, "Autofocus reference", parameters.get("skip_every")
    )
    ref_frames = reference_frames
    if ref_frames is None:
        ref_frames = file_reader.read_frames(
            first_frame=ref_first_frame, batch_size=ref_batch_size,
            skip_every=parameters.get("skip_every"),
        )

    if ref_frames.shape[0] == 0:
        raise ValueError(
            "Shack-Hartmann autofocus reference batch is empty."
        )

    ref_frames = backend.to_backend(_frame_stack(ref_frames)).astype(
        backend.xp.float32,
        copy=False,
    )

    # Apply the same 2D filter to the autofocus reference as to all
    # normal processing batches.
    if parameters.get("filter2d", False):
        ref_frames = filter_2d(
            backend.xp,
            backend.fft,
            ref_frames,
            parameters["filter2d_low"],
        )

    # Diagnostics from the autofocus reference are deliberately not
    # appended to the normal batch output because their shape differs
    # from the regular per-batch outputs.
    autofocus_result = {}

    phase_term = _process_shack_hartmann(
        parameters,
        ref_frames,
        output_dict=autofocus_result,
        diagnostics=diagnostics,
    )

    coefs = autofocus_result.get("shack_hartmann_zernike_coefs")

    if diagnostics is not None and "shack_hartmann_shifts" in autofocus_result:
        diagnostics["shack_hartmann_autofocus_shifts"] = backend.to_numpy(
            autofocus_result["shack_hartmann_shifts"]
        )

    reason = None
    modes = list(parameters.get("shack_hartmann_zernike_fit_modes", [4, 5, 6]))
    threshold = parameters.get("shack_hartmann_autofocus_z4_threshold_rad", None)
    if threshold is None:
        threshold = np.inf
    values = None if coefs is None else backend.to_numpy(coefs)
    phase = autofocus_result.get("shack_hartmann_wavefront_phase")
    if values is None or not np.isfinite(values).all():
        reason = "missing or nonfinite Zernike coefficients"
    elif 4 not in modes:
        reason = "Z4 is absent from the fitted modes"
    elif abs(float(values[modes.index(4)])) > threshold:
        reason = f"Z4={float(values[modes.index(4)]):g} rad exceeds absolute threshold {threshold:g} rad"
    elif phase is None or not bool(backend.xp.isfinite(phase).all()):
        reason = "missing or nonfinite wavefront phase"

    del ref_frames
    del autofocus_result
    del phase
    if reason is not None:
        phase_term = None
    # Release unused autofocus allocations before processing the main batches.
    # The accepted phase correction and coefficients remain available for reuse.
    backend.clear_gpu_memory()
    if reason is not None:
        logger.warning("Shack-Hartmann autofocus correction rejected: %s; continuing without phase correction.", reason)
        return None, coefs

    if phase_term is None:
        raise RuntimeError(
            "Shack-Hartmann autofocus was enabled, but no phase "
            "correction was produced."
        )

    logger.info("Shack-Hartmann autofocus phase correction computed.")

    return phase_term, coefs


def _process_one_batch(
    parameters,
    frames,
    registration_ref=None,
    phase_term=None,
    propagation_kernel=None,
):
    """
    Process one batch.

    If `phase_term` is supplied, that fixed wavefront correction is
    applied to the batch.

    If live `shack_hartmann` processing is enabled and no phase term
    was supplied, a new Shack-Hartmann correction is calculated for
    this batch.
    """

    if parameters.get("filter2d", False):
        frames = filter_2d(
            backend.xp,
            backend.fft,
            frames,
            parameters["filter2d_low"],
        )

    res = {}

    # A fixed autofocus correction takes precedence. Rejected autofocus must
    # continue uncorrected rather than falling back to live Shack-Hartmann.
    if (phase_term is None and not parameters.get("shack_hartmann_autofocus", False)) and parameters.get(
        "shack_hartmann",
        False,
    ):
        phase_term = _process_shack_hartmann(
            parameters,
            frames,
            output_dict=res,
        )

    _process_batch(
        parameters,
        frames,
        phase_term=phase_term,
        output_dict=res,
        propagation_kernel=propagation_kernel,
    )

    # ------------------------------------------------------------
    # Image registration
    # ------------------------------------------------------------
    if (
        registration_ref is None
        and parameters.get("image_registration", False)
    ):
        registration_ref = res["moment0ff"]

    if registration_ref is not None:

        shift_y, shift_x = register_images_shifts(
            backend.xp,
            backend.fft,
            registration_ref,
            res["moment0ff"],
            radius=parameters["registration_radius"],
            sub_pixel=parameters["registration_sub_pixel"],
        )

        for key, value in list(res.items()):

            if (
                key in {"moment0ff", "moment0", "moment1", "moment2", "sh_psd"}
                or key.startswith(("moment0_range_", "moment1_range_", "moment0ff_range_"))
                or "band_" in key or key in {"_color_Doppler_low", "_color_Doppler_high",
                           "_directional_Doppler_pos", "_directional_Doppler_neg"}
            ):
                res[key] = apply_register_images_shifts(
                    backend.xp,
                    value,
                    shift_y=shift_y,
                    shift_x=shift_x,
                    fft=backend.fft,
                    block_size_mib=parameters.get("registration_block_size_mib", 8),
                )

        res["registration"] = backend.xp.stack(
            [
                backend.xp.asarray(shift_y),
                backend.xp.asarray(shift_x),
            ]
        )

    return res, registration_ref


def _prepare_batch_results(res, parameters):
    """Finish backend operations before the scheduler downloads results."""
    res = dict(res)
    if "sh_psd" in res:
        if parameters.get("save_spectograms", False):
            shape = parameters.get("spectrogram_resize_shape", (256, 256))
            order = parameters.get("spectrogram_resize_order", 1)
            value = resize_frames(
                backend.xp, backend.zoom, res["sh_psd"], *shape, order=order
            )
            n_freq, ny, nx = value.shape
            start = int(n_freq * parameters.get("spectrogram_frequency_start", 0.0))
            end = int(n_freq * parameters.get("spectrogram_frequency_end", 0.5))
            value = backend.xp.concatenate((value[:end], value[start + n_freq // 2:]), axis=0)
            binning = parameters.get("spectrogram_frequency_binning", 4)
            res["spectrograms"] = value.reshape(
                value.shape[0] // binning, binning, ny, nx).mean(axis=1)
        if not parameters.get("save_averaged_spectrogram", False):
            del res["sh_psd"]
    return res


class _DefaultOutputs:
    """Keep PSD aggregation on the compute stream for GPU, caller for CPU."""

    def __init__(self, parameters):
        self.parameters = parameters
        self.aggregates = {}

    def _accumulate(self, spectrum):
        if "averaged_spectrogram" not in self.aggregates:
            self.aggregates["averaged_spectrogram"] = spectrum.copy()
        else:
            self.aggregates["averaged_spectrogram"] += spectrum

    def prepare(self, result):
        result = _prepare_batch_results(result, self.parameters)
        if backend.is_gpu and "sh_psd" in result:
            self._accumulate(result.pop("sh_psd"))
        return result

    def consume(self, result):
        result = dict(result)
        if "sh_psd" in result:
            self._accumulate(backend.to_numpy(result.pop("sh_psd")))
        return result

    def finish(self, completed):
        output = {}
        if "averaged_spectrogram" in self.aggregates:
            spectrum = _square_spectrum(self.aggregates.pop("averaged_spectrogram"), self.parameters)
            spectrum = backend.to_numpy(spectrum)
            spectrum /= completed
            output["averaged_spectrogram"] = np.squeeze(spectrum)
        return output


def _ecc_spatial_key(key):
    return (key in {"moment0ff", "moment0", "moment1", "moment2"}
            or key.startswith(("moment0_range_", "moment1_range_", "moment0ff_range_"))
            or "band_" in key or key in {"_color_Doppler_low", "_color_Doppler_high",
                                        "_directional_Doppler_pos", "_directional_Doppler_neg"})


def _finalize_spatial_result(result, parameters):
    """Square scalar maps before rendering Doppler colors on the same backend."""
    result = dict(result)
    if parameters.get("square", False):
        for key, value in result.items():
            if (value.ndim == 2 and not key.startswith("shack_hartmann_")
                    and key not in {"registration", "registration_ecc"}):
                size = max(value.shape)
                result[key] = resize_frames(backend.xp, backend.zoom, value, size, size)
    finish_doppler_images(result, backend.xp, parameters)
    return result


def _square_spectrum(spectrum, parameters):
    if parameters.get("square", False):
        size = max(spectrum.shape[-2:])
        return resize_frames(backend.xp, backend.zoom, spectrum, size, size)
    return spectrum


def preview(file_path, parameters):
    file_reader, parameters = prepare_input(file_path, parameters, copy_parameters=False)
    logger.debug("Preview input: %s", file_path)

    _validate_reference_batch(
        file_reader, parameters["first_frame"], parameters["batch_size"], "Preview", parameters.get("skip_every")
    )

    # ------------------------------------------------------------
    # Build autofocus phase once from the configured reference batch
    # ------------------------------------------------------------
    autofocus_diagnostics = {}
    autofocus_phase_term, auto_coefs = _get_autofocus_phase_term(
        parameters,
        file_reader,
        diagnostics=autofocus_diagnostics,
    )

    # ------------------------------------------------------------
    # Preview frames
    # ------------------------------------------------------------
    frames = file_reader.read_frames(
        first_frame=parameters["first_frame"],
        batch_size=parameters["batch_size"],
        skip_every=parameters.get("skip_every"),
    )

    frames = backend.to_backend(_frame_stack(frames)).astype(
        backend.xp.float32,
        copy=False,
    )

    # If autofocus is active, reuse the reference correction here.
    # Otherwise live Shack-Hartmann is handled by _process_one_batch().
    res, _ = _process_one_batch(
        parameters,
        frames,
        registration_ref=None,
        phase_term=autofocus_phase_term,
    )

    if auto_coefs is not None:
        res["shack_hartmann_autofocus_zernike_coefs"] = backend.to_numpy(auto_coefs)

    res = _finalize_spatial_result(res, parameters)
    if "sh_psd" in res:
        res["sh_psd"] = _square_spectrum(res["sh_psd"], parameters)
    res_np = {key: backend.to_numpy(value) for key, value in res.items()}

    del res
    del autofocus_phase_term

    backend.clear_gpu_memory()

    res_np.update(autofocus_diagnostics)
    save_result_bundle(file_reader, parameters, res_np, preview=True)

    return res_np["moment0ff"]


def process(file_path, parameters, progress_callback=None):
    file_reader, parameters = prepare_input(file_path, parameters, copy_parameters=False)
    indices = get_batch_indices(file_reader, parameters)
    if not indices:
        return
    _process_to_output(file_reader, parameters, indices,
                       progress_callback=progress_callback)


def _process_to_output(file_reader, parameters, batch_indices,
                       destination=_MANAGED_DESTINATION, progress_callback=None):
    batch_size = parameters["batch_size"]
    first_frame = parameters["first_frame"]

    registration_ref = None
    explicit_reference = parameters.get("image_registration", False) and (
        parameters["registration_ref_first_frame"] != first_frame
        or parameters["registration_ref_batch_size"] != batch_size
    )
    ref_frames = None
    if explicit_reference:
        _validate_reference_batch(
            file_reader, parameters["registration_ref_first_frame"],
            parameters["registration_ref_batch_size"], "Registration reference",
            parameters.get("skip_every"),
        )
        ref_frames = backend.to_backend(_frame_stack(file_reader.read_frames(
            first_frame=parameters["registration_ref_first_frame"],
            batch_size=parameters["registration_ref_batch_size"],
            skip_every=parameters.get("skip_every"),
        ))).astype(backend.xp.float32, copy=False)

    autofocus_diagnostics = {}
    autofocus_frames = None
    if (ref_frames is not None and parameters.get("shack_hartmann_autofocus", False)
            and parameters.get("shack_hartmann_autofocus_batch_size", batch_size)
            == parameters["registration_ref_batch_size"]):
        autofocus_frames = ref_frames
    autofocus_phase_term, auto_coefs = _get_autofocus_phase_term(
        parameters, file_reader, diagnostics=autofocus_diagnostics,
        reference_frames=autofocus_frames,
    )
    propagation_kernel = _fixed_fresnel_kernel(parameters, autofocus_phase_term)
    if explicit_reference:
        if parameters.get("filter2d", False):
            ref_frames = filter_2d(backend.xp, backend.fft, ref_frames,
                                   parameters["filter2d_low"])
        reference_phase = autofocus_phase_term
        if (reference_phase is None and not parameters.get("shack_hartmann_autofocus", False)
                and parameters.get("shack_hartmann", False)):
            reference_phase = _process_shack_hartmann(parameters, ref_frames)
        registration_ref = _process_batch(
            parameters, ref_frames, phase_term=reference_phase,
            reference_only=True, propagation_kernel=propagation_kernel,
        )["moment0ff"]
    del ref_frames, autofocus_frames

    def process_batch(frames, reference):
        return _process_one_batch(
            parameters, frames, registration_ref=reference,
            phase_term=autofocus_phase_term, propagation_kernel=propagation_kernel,
        )

    outputs = _DefaultOutputs(parameters)

    def static_factory(completed):
        result = outputs.finish(completed)
        if auto_coefs is not None:
            result["shack_hartmann_autofocus_zernike_coefs"] = backend.to_numpy(auto_coefs)
        result.update(autofocus_diagnostics)
        return result

    try:
        run_pipeline(
            file_reader, parameters, process_batch, indices=batch_indices,
            reference=registration_ref, destination=destination, preallocate=True,
            prepare_batch=outputs.prepare, consume_batch=outputs.consume,
            finalize_result=lambda result: _finalize_spatial_result(result, parameters),
            ecc_key_predicate=_ecc_spatial_key, static_factory=static_factory,
            progress_callback=progress_callback,
        )
    finally:
        # Release references before clearing cached GPU allocations, also on failure.
        autofocus_phase_term = propagation_kernel = registration_ref = None
        outputs.aggregates.clear()
        backend.clear_gpu_memory()
