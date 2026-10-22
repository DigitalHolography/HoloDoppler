import numpy as np

from holodoppler import backend
from holodoppler.logging import logger
from holodoppler.config import (
    update_from_cine_metadata,
    update_from_holo_footer,
    validate_main_parameters,
)
from holodoppler.core.batching import calculate_batch_indices
from holodoppler.core.processing import run_batches
from holodoppler.core.filtering import (
    corner_compensation,
    filter_2d,
    fourier_time_transform,
    frequency_symmetric_filtering,
    svd_filter,
)
from holodoppler.core.image_utils import (
    gaussian_flatfield,
    resize_frames,
)
from holodoppler.core.moments import moments
from holodoppler.core.plots import plot_phase_with_slopes_rgb
from holodoppler.core.propagation import (
    angular_spectrum_transform,
    angular_spectrum_transform_with_phase,
    fresnel_transform,
    fresnel_transform_with_phase,
)
from holodoppler.core.registration import (
    apply_ecc_registration,
    apply_register_images_shifts,
    register_images_shifts,
    register_with_ecc,
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
from holodoppler.file_reader import get_reader
from holodoppler.saving import (
    save_outputs,
)


def _frame_stack(frames):
    """Readers may squeeze a single frame to two dimensions."""
    return frames[None, ...] if frames.ndim == 2 else frames


def _validate_reference_batch(file_reader, first_frame, batch_size, label):
    try:
        indices = calculate_batch_indices(
            first_frame, 0, batch_size, batch_size, file_reader.total_frames
        )
        if not indices:
            raise ValueError("no complete batch fits")
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{label} batch (first_frame={first_frame}, batch_size={batch_size}) "
            f"cannot fit within {file_reader.total_frames} file frames: {exc}"
        ) from exc


def _process_batch(parameters, frames, phase_term=None, output_dict=None):
    xp = backend.xp
    fft = backend.fft

    nt_sub = frames.shape[0]
    prop_method = parameters["spatial_propagation"]

    # ------------------------------------------------------------
    # Spatial propagation
    # ------------------------------------------------------------
    if phase_term is not None:
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
        backend.xp, backend.linalg, holograms,
        parameters["svd_threshold"],
        filter_mode=parameters["svd_filter_mode"],
        remove_dc=parameters["svd_remove_dc"],
    )

    del holograms

    if output_dict is None:
        output_dict = {}

    # ------------------------------------------------------------
    # Temporal Fourier transform
    # ------------------------------------------------------------
    if parameters.get("temporal_transformation") == "FourierTransform":
        spectrum_f = fourier_time_transform(
            xp,
            fft,
            holograms_f,
        )
    else:
        spectrum_f = holograms_f
    del holograms_f

    psd = xp.abs(spectrum_f)**2
    del spectrum_f
    xp.square(psd, out=psd)

    # ------------------------------------------------------------
    # Frequency filtering
    # ------------------------------------------------------------
    idxs, freqs = frequency_symmetric_filtering(
        xp,
        fft,
        nt_sub,
        parameters["sampling_freq"],
        parameters["low_freq"],
        parameters.get("high_freq"),
    )

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

    # ------------------------------------------------------------
    # Moments
    # ------------------------------------------------------------
    output_dict["M0"], output_dict["M1"], output_dict["M2"] = moments(
        xp,
        psd[idxs],
        freqs,
        [0,1,2],
    )
    output_dict["spectrum_line"] = xp.mean(
        psd,
        axis=(-2, -1),
    )

    if parameters.get("save_spectograms",False) or parameters.get("save_averaged_spectrogram",False):
        output_dict["sh_psd"] = psd # the power spectrum density

    # ------------------------------------------------------------
    # Frequency bands
    # ------------------------------------------------------------
    for k, (f1, f2) in enumerate(
        parameters.get("frequency_bands", [])
    ):
        idxs_band, _ = frequency_symmetric_filtering(
            xp,
            fft,
            nt_sub,
            parameters["sampling_freq"],
            f1,
            f2,
        )

        output_dict[f"band_{k}_{f1}_{f2}"] = xp.mean(
            psd[idxs_band],
            axis=0,
        )

    del psd

    output_dict["M0ff"] = gaussian_flatfield(
        output_dict["M0"],
        parameters.get("registration_flatfield_gw", 1.0),
        backend.gaussian_filter,
    )

    return output_dict


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
            parameters["sampling_freq"],
            frames.shape[0],
            parameters["shack_hartmann_nx_subap"],
            parameters["shack_hartmann_ny_subap"],
            parameters["shack_hartmann_svd_threshold"],
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
            parameters["sampling_freq"],
            frames.shape[0],
            parameters["shack_hartmann_nx_subap"],
            parameters["shack_hartmann_ny_subap"],
            parameters["shack_hartmann_svd_threshold"],
        )

    else:
        raise ValueError(
            f"Unknown propagation method: {prop_method!r}"
        )

    # ------------------------------------------------------------
    # Calculate Shack-Hartmann displacements
    # ------------------------------------------------------------
    if parameters.get("shack_hartmann_graph_laplacian", False):
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            xp,
            fft,
            U,
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
    phase_term = xp.exp(-1j * phase)

    return xp.nan_to_num(
        phase_term,
        nan=0.0,
    )


def _get_autofocus_phase_term(parameters, file_reader, diagnostics=None):
    """
    Compute the Shack-Hartmann autofocus correction once from
    the configured reference batch.

    When diagnostics is supplied, populate it with an RGB phase-and-shifts
    image, kept separate from the normal batch outputs.

    Reference batch:
        start = registration_ref_first_frame
        size  = shack_hartmann_autofocus_batch_size (defaults to batch_size)

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
        file_reader, ref_first_frame, ref_batch_size, "Autofocus reference"
    )
    ref_frames = file_reader.read_frames(
        first_frame=ref_first_frame,
        batch_size=ref_batch_size,
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

    del ref_frames
    del autofocus_result

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

    # ------------------------------------------------------------
    # Wavefront correction
    # ------------------------------------------------------------
    #
    # Fixed autofocus phase has priority when it is supplied.
    #
    # Therefore:
    #
    #   shack_hartmann_autofocus = True
    #   shack_hartmann = False
    #
    # computes the phase once and reuses it.
    #
    # Live Shack-Hartmann:
    #
    #   shack_hartmann_autofocus = False
    #   shack_hartmann = True
    #
    # computes a new correction for every batch.
    # ------------------------------------------------------------
    if phase_term is None and parameters.get(
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
    )

    # ------------------------------------------------------------
    # Image registration
    # ------------------------------------------------------------
    if (
        registration_ref is None
        and parameters.get("image_registration", False)
    ):
        registration_ref = res["M0ff"]

    if registration_ref is not None:

        shift_y, shift_x = register_images_shifts(
            backend.xp,
            backend.fft,
            registration_ref,
            res["M0ff"],
            radius=parameters["registration_radius"],
            sub_pixel=parameters["registration_sub_pixel"],
        )

        for key, value in list(res.items()):

            if (
                key in {"M0ff", "M0", "M1", "M2", "sh_psd"}
                or "band_" in key
            ):
                res[key] = apply_register_images_shifts(
                    backend.xp,
                    value,
                    shift_y=shift_y,
                    shift_x=shift_x,
                    fft=backend.fft,
                )

        res["registration"] = backend.xp.stack(
            [
                backend.xp.asarray(shift_y),
                backend.xp.asarray(shift_x),
            ]
        )

    return res, registration_ref


def _store_batch_result(output, key, value, batch_index, num_batches):
    """Allocate each output once, using its first batch's shape and dtype."""
    value = backend.to_numpy(value)
    if key not in output:
        output[key] = np.empty((num_batches, *value.shape), dtype=value.dtype)
    if output[key].shape[1:] != value.shape:
        raise ValueError(
            f"Output {key!r} changed shape from {output[key].shape[1:]} "
            f"to {value.shape} at batch {batch_index}."
        )
    output[key][batch_index] = value


def _prepare_batch_results(res, parameters):
    """Finish backend operations before the scheduler downloads results."""
    res = dict(res)
    if "sh_psd" in res:
        if parameters.get("save_spectograms", False):
            shape = parameters.get("spectrogram_resize_shape", (256, 256))
            order = parameters.get("spectrogram_resize_order", 1)
            res["spectrograms"] = resize_frames(
                backend.xp, backend.zoom, res["sh_psd"], *shape, order=order
            )
        if not parameters.get("save_averaged_spectrogram", False):
            del res["sh_psd"]
    return res


def _append_numpy_results(output, res, parameters, batch_index, num_batches):
    for key, value in res.items():
        if key == "sh_psd":
            spectrum = backend.to_numpy(value)
            if "averaged_spectrogram" in output:
                output["averaged_spectrogram"] += spectrum
            else:
                output["averaged_spectrogram"] = spectrum.copy()
        elif key == "spectrograms":
            value = backend.to_numpy(value)
            n_freq, nny, nnx = value.shape
            start_idx = int(n_freq * parameters.get("spectrogram_frequency_start", 0.0))
            end_idx = int(n_freq * parameters.get("spectrogram_frequency_end", 0.5))
            value = np.concatenate(
                (value[:end_idx], value[start_idx + n_freq // 2 :]), axis=0
            )
            binning = parameters.get("spectrogram_frequency_binning", 4)
            value = value.reshape(value.shape[0] // binning, binning, nny, nnx).mean(axis=1)
            _store_batch_result(output, key, value, batch_index, num_batches)
        else:
            _store_batch_result(output, key, value, batch_index, num_batches)


def preview(file_path, parameters):
    if parameters.get("force_numpy",False):
        backend.set_backend("numpy")
    file_reader = get_reader(file_path)

    logger.debug("Preview input: %s", file_path)

    if file_reader.extension == ".holo":
        logger.debug("File header: %s", file_reader.header)

        parameters = update_from_holo_footer(
            parameters,
            file_reader.footer,
        )

    if file_reader.extension == ".cine":
        logger.debug("File header: %s", file_reader.header)

        parameters = update_from_cine_metadata(
            parameters,
            file_reader.header
        )

    validate_main_parameters(parameters)

    _validate_reference_batch(
        file_reader, parameters["first_frame"], parameters["batch_size"], "Preview"
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

    # ------------------------------------------------------------
    # Square output
    # ------------------------------------------------------------
    if parameters.get("square", False):
        res = {
            k: (
                backend.to_numpy(resize_frames(backend.xp, backend.zoom,
                    v,
                    max(v.shape[-2:]),
                    max(v.shape[-2:]),
                ))
                if v.ndim == 2
                else v
            )
            for k, v in res.items()
        }

    res_np = {
        k: backend.to_numpy(v)
        for k, v in res.items()
    }

    del res
    del autofocus_phase_term

    backend.clear_gpu_memory()

    res_np["moment0"] = res_np.pop("M0")
    res_np["moment0ff"] = res_np.pop("M0ff")
    res_np["moment1"] = res_np.pop("M1")
    res_np["moment2"] = res_np.pop("M2")

    res_np.update(autofocus_diagnostics)
    save_outputs(
        file_reader=file_reader,
        output=res_np,
        parameters=parameters,
        custom_relative_path="preview",
    )

    return res_np["moment0ff"]


def process(file_path, parameters, progress_callback=None):
    if parameters.get("force_numpy",False):
        backend.set_backend("numpy")

    file_reader = get_reader(file_path)

    if file_reader.extension == ".holo":
        logger.debug("File header: %s", file_reader.header)

        parameters = update_from_holo_footer(
            parameters,
            file_reader.footer,
        )

    if file_reader.extension == ".cine":
        logger.debug("File header: %s", file_reader.header)

        parameters = update_from_cine_metadata(
            parameters,
            file_reader.header
        )

    validate_main_parameters(parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]

    end_frame = parameters.get(
        "end_frame",
        0,
    )

    batch_indices = calculate_batch_indices(
        first_frame, end_frame, batch_size, batch_stride, file_reader.total_frames
    )
    if not batch_indices:
        return

    output = {}

    registration_ref = None

    # ------------------------------------------------------------
    # Build the registration reference once
    # ------------------------------------------------------------
    if (
        parameters.get(
            "image_registration",
            False,
        )
        and (
            parameters["registration_ref_first_frame"] != first_frame
            or parameters["registration_ref_batch_size"]
            != parameters["batch_size"]
        )
    ):

        _validate_reference_batch(
            file_reader, parameters["registration_ref_first_frame"],
            parameters["registration_ref_batch_size"], "Registration reference",
        )
        ref_frames = file_reader.read_frames(
            first_frame=parameters[
                "registration_ref_first_frame"
            ],
            batch_size=parameters[
                "registration_ref_batch_size"
            ],
        )

        ref_frames = backend.to_backend(_frame_stack(ref_frames)).astype(
            backend.xp.float32,
            copy=False,
        )

        ref_res, _ = _process_one_batch(
            parameters,
            ref_frames,
            registration_ref=None,
            phase_term=None,
        )

        registration_ref = ref_res["M0ff"].copy()

        del ref_frames
        del ref_res

        backend.clear_gpu_memory()

    # ------------------------------------------------------------
    # Build one Shack-Hartmann autofocus correction from the
    # configured reference batch.
    #
    # The returned phase_term is kept alive and passed to every
    # processed batch below.
    # ------------------------------------------------------------
    autofocus_diagnostics = {}
    autofocus_phase_term, auto_coefs = _get_autofocus_phase_term(
        parameters,
        file_reader,
        diagnostics=autofocus_diagnostics,
    )

    def process_batch(frames, reference):
        return _process_one_batch(
            parameters, frames, registration_ref=reference,
            phase_term=autofocus_phase_term,
        )

    def consume_result(index, result):
        _append_numpy_results(output, result, parameters, index, len(batch_indices))

    registration_ref = run_batches(
        file_reader, batch_indices, batch_size, process_batch, consume_result,
        registration_ref=registration_ref,
        registration_enabled=parameters.get("image_registration", False),
        workers=parameters.get("numpy_num_workers", 8),
        cupy_async=parameters.get("cupy_async", True),
        cupy_prefetch_depth=parameters.get("cupy_prefetch_depth", 4),
        prepare_result=lambda result: _prepare_batch_results(result, parameters),
        progress_callback=progress_callback,
    )

    logger.debug("Output keys: %s", output.keys())

    if auto_coefs is not None:
        output["shack_hartmann_autofocus_zernike_coefs"] = backend.to_numpy(auto_coefs)

    if "averaged_spectrogram" in output:
        output["averaged_spectrogram"] = np.squeeze(output["averaged_spectrogram"]) # This aggregate has no batch axis.

    # ------------------------------------------------------------
    # ECC Image Registration at the end
    # ------------------------------------------------------------

    if parameters.get("image_registration_with_ecc", False):
        logger.info("Running Registration ECC algo:")
        registration_ecc = register_with_ecc(output["M0ff"],radius=parameters.get("registration_ecc_radius",0.8),iterations=300,eps=1e-6, progress_callback=progress_callback, ecc_min_threshold=parameters.get("registration_ecc_min_threshold",0.7))


        for key in output :
            if key in {"M0ff", "M0", "M1", "M2"} or "band_" in key :
                output[key] = apply_ecc_registration(output[key], registration_ecc, background="mean")

        output["registration_ecc"] = registration_ecc
        logger.info("Registration calculated.")


    # ------------------------------------------------------------
    # Square spatial outputs
    # ------------------------------------------------------------
    if parameters.get("square", False):

        output = {
            key: (
                backend.to_numpy(resize_frames(backend.xp, backend.zoom,
                    value,
                    max(value.shape[-2:]),
                    max(value.shape[-2:]),
                ))
                if value.ndim == 3
                else value
            )
            for key, value in output.items()
        }

    # The fixed autofocus correction is no longer needed.
    del autofocus_phase_term

    backend.clear_gpu_memory()

    # ------------------------------------------------------------
    # Renaming for compatibility with Doppler View
    # ------------------------------------------------------------
    output["moment0"] = output.pop("M0")
    output["moment0ff"] = output.pop("M0ff")
    output["moment1"] = output.pop("M1")
    output["moment2"] = output.pop("M2")

    output.update(autofocus_diagnostics)
    save_outputs(
        file_reader=file_reader,
        output=output,
        parameters=parameters,
    )
