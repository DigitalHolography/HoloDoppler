import holodoppler.backend as backend
from holodoppler.core.filtering import (
    corner_compensation,
    filter_2d,
    fourier_time_transform,
    frequency_symmetric_filtering,
    svd_filter,
)
from holodoppler.core.moments import moment
from holodoppler.core.propagation import (
    angular_spectrum_transform,
    angular_spectrum_transform_with_phase,
    fresnel_transform,
    fresnel_transform_with_phase,
)
from holodoppler.core.registration import apply_register_images_shifts, register_images_shifts
from holodoppler.core.shack_hartmann import (
    calculate_displacements,
    calculate_displacements_graph_laplacian,
    construct_subapertures_angular,
    construct_subapertures_fresnel,
)
from holodoppler.core.image_utils import gaussian_flatfield


from holodoppler.core.zernike import (
    fit_zernike_angular_spectrum,
    fit_zernike_fresnel,
)

from holodoppler.core.plots import plot_phase_with_slopes_rgb

from holodoppler.core.pipeline import prepare_input, read_reference, run_pipeline, batch_indices
from .main_default import _get_autofocus_phase_term

def _process_batch(
    parameters,
    frames,
    phase_term=None,
    output_dict=None,
):
    """
    Process one batch of holographic frames.

    Performs:
        1. Spatial propagation
        2. SVD filtering
        3. Optional temporal Fourier transform
        4. Frequency selection
        5. PSD calculation
        6. Optional corner compensation
        7. Moment calculation
        8. Gaussian flat-field correction
        9. Optional frequency-band calculations
    """

    xp = backend.xp
    fft = backend.fft

    nt_sub = frames.shape[0]
    prop_method = parameters["spatial_propagation"]

    # ------------------------------------------------------------------
    # Propagation
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # SVD filtering
    # ------------------------------------------------------------------
    if parameters.get("svd_filtering", True):
        holograms_f = svd_filter(
            backend.xp, backend.linalg, holograms,
            parameters["svd_threshold"],
            filter_mode=parameters["svd_filter_mode"],
            remove_dc=parameters["svd_remove_dc"],
            block_size_mib=parameters.get("svd_block_size_mib", 8),
        )
        del holograms
    else:
        holograms_f = holograms

    if output_dict is None:
        output_dict = {}

    # ------------------------------------------------------------------
    # Temporal transform
    # ------------------------------------------------------------------
    if parameters.get("temporal_transformation") == "FourierTransform":
        spectrum_f = fourier_time_transform(
            xp,
            fft,
            holograms_f,
        )
    else:
        spectrum_f = holograms_f

    # ------------------------------------------------------------------
    # Frequency selection
    # ------------------------------------------------------------------
    idxs, freqs = frequency_symmetric_filtering(
        xp,
        fft,
        nt_sub,
        (parameters["sampling_freq"] / (parameters.get("skip_every") or 1)),
        parameters["low_freq"],
        parameters.get("high_freq"),
    )

    # ------------------------------------------------------------------
    # PSD
    # ------------------------------------------------------------------
    psd = xp.abs(spectrum_f) ** 2

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

    # ------------------------------------------------------------------
    # Moments
    # ------------------------------------------------------------------
    output_dict["M0"] = moment(
        xp,
        psd[idxs],
        freqs,
        0,
    )

    output_dict["M1"] = moment(
        xp,
        psd[idxs],
        freqs,
        1,
    )

    output_dict["M2"] = moment(
        xp,
        psd[idxs],
        freqs,
        2,
    )

    # ------------------------------------------------------------------
    # Flat-field correction
    # ------------------------------------------------------------------
    output_dict["M0ff"] = gaussian_flatfield(
        output_dict["M0"],
        parameters.get("registration_flatfield_gw", 1.0),
        backend.gaussian_filter,
    )

    # ------------------------------------------------------------------
    # Spectrum line
    # ------------------------------------------------------------------
    output_dict["spectrum_line"] = xp.mean(
        psd,
        axis=(-2, -1),
    )

    # ------------------------------------------------------------------
    # Frequency bands
    # ------------------------------------------------------------------
    for k, (f1, f2) in enumerate(
        parameters.get("frequency_bands", [])
    ):
        idxs_band, _ = frequency_symmetric_filtering(
            xp,
            fft,
            nt_sub,
            (parameters["sampling_freq"] / (parameters.get("skip_every") or 1)),
            f1,
            f2,
        )

        output_dict[f"band_{k}_{f1}_{f2}"] = xp.mean(
            psd[idxs_band],
            axis=0,
        )

    return output_dict


def _process_one_batch(
    parameters,
    frames,
    M0_reg=None,
    U_buffer=None,
    phase_term=None,
):
    """
    Process one batch on the active backend.

    U_buffer is used for the sliding Shack-Hartmann accumulation.
    """

    xp = backend.xp

    # ------------------------------------------------------------------
    # Optional 2D filtering
    # ------------------------------------------------------------------
    if parameters.get("filter2d", False):
        frames = filter_2d(
            xp,
            backend.fft,
            frames,
            parameters["filter2d_low"],
        )

    res = {}

    # ------------------------------------------------------------------
    # Shack-Hartmann / fixed autofocus wavefront correction
    # ------------------------------------------------------------------
    if phase_term is None and parameters.get("shack_hartmann", False):

        # If sliding accumulation is requested, construct U separately
        # so that the last N U arrays can be accumulated.
        prop_method = parameters["spatial_propagation"]

        if prop_method == "Fresnel":
            U = construct_subapertures_fresnel(
                xp,
                backend.fft,
                frames,
                parameters["wavelength"],
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["low_freq"],
                parameters.get("high_freq"),
                (parameters["sampling_freq"] / (parameters.get("skip_every") or 1)),
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
                backend.fft,
                frames,
                parameters["wavelength"],
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["low_freq"],
                parameters.get("high_freq"),
                (parameters["sampling_freq"] / (parameters.get("skip_every") or 1)),
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

        # --------------------------------------------------------------
        # Sliding U accumulation
        # --------------------------------------------------------------
        if U_buffer is not None:
            U_buffer.append(U)
            del U_buffer[:-parameters.get("sh_time_accumulation", 1)]

            # Avoid Python's sum() starting with integer zero.
            U_tot = U_buffer[0]

            for u in U_buffer[1:]:
                U_tot = U_tot + u

        else:
            U_tot = U

        # --------------------------------------------------------------
        # Displacement estimation
        # --------------------------------------------------------------
        if parameters.get(
            "shack_hartmann_graph_laplacian",
            False,
        ):
            shifts_y, shifts_x = (
                calculate_displacements_graph_laplacian(
                    xp,
                    backend.fft,
                    U_tot,
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
            )

        else:
            shifts_y, shifts_x = calculate_displacements(
                xp,
                backend.fft,
                U_tot,
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

        # --------------------------------------------------------------
        # Sub-aperture montage output
        # --------------------------------------------------------------
        sy, sx, numy, numx = U_tot.shape

        U_display = xp.transpose(
            U_tot,
            axes=(0, 2, 1, 3),
        )

        res["shack_hartmann_sub_images"] = xp.reshape(
            U_display,
            (numy * sy, numx * sx),
        )

        # --------------------------------------------------------------
        # Zernike fit
        # --------------------------------------------------------------
        if parameters.get(
            "shack_hartmann_zernike_fit",
            True,
        ):
            nt, ny, nx = frames.shape

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
                    parameters.get(
                        "shack_hartmann_zernike_fit_modes"
                    ),
                )

            elif prop_method == "AngularSpectrum":
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
                    parameters.get(
                        "shack_hartmann_zernike_fit_modes"
                    ),
                )

            else:
                raise ValueError(
                    f"Unknown propagation method: {prop_method!r}"
                )

            res["shack_hartmann_zernike_coefs"] = coefs
            res["shack_hartmann_wavefront_phase"] = phase

            res["shack_hartmann_wavefront_color_image"] = plot_phase_with_slopes_rgb(
                backend.to_numpy(phase), backend.to_numpy(shifts_y), backend.to_numpy(shifts_x))

            phase_term = xp.exp(-1j * phase)
            phase_term = xp.nan_to_num(
                phase_term,
                nan=0.0,
            )

        # The current U can be released when it is not retained by the
        # sliding buffer.

        if U_tot is not U:
            del U_tot

        if U_buffer is None:
            del U

        

    # ------------------------------------------------------------------
    # Main Doppler processing
    # ------------------------------------------------------------------
    _process_batch(
        parameters,
        frames,
        phase_term=phase_term,
        output_dict=res,
    )

    # ------------------------------------------------------------------
    # Image registration
    # ------------------------------------------------------------------
    if (
        M0_reg is None
        and parameters.get("image_registration", False)
    ):
        M0_reg = res["M0ff"]

    if M0_reg is not None:
        shift_y, shift_x = register_images_shifts(
            xp,
            backend.fft,
            M0_reg,
            res["M0ff"],
            radius=parameters.get(
                "registration_radius",
                0.8,
            ),
            sub_pixel=parameters.get(
                "registration_sub_pixel",
                True,
            ),
        )

        for key, value in list(res.items()):
            if (
                key in {"M0ff", "M0", "M1", "M2"}
                or "band_" in key
            ):
                res[key] = apply_register_images_shifts(
                    xp,
                    backend.fft,
                    value,
                    shift_y,
                    shift_x,
                )

        res["registration"] = xp.stack(
            [
                xp.asarray(shift_y),
                xp.asarray(shift_x),
            ]
        )

    return res, M0_reg


def _run(file_path, parameters, preview=False, progress_callback=None):
    reader, p = prepare_input(file_path, parameters)
    if not batch_indices(reader, p):
        return None
    p.setdefault("registration_ref_first_frame", p["first_frame"])
    phase, coefs = _get_autofocus_phase_term(p, reader)
    reference = None
    ref_first = p["registration_ref_first_frame"]
    ref_size = p.get("registration_ref_batch_size", p["batch_size"])
    if p.get("image_registration", False) and (ref_first != p["first_frame"] or ref_size != p["batch_size"]):
        frames = read_reference(reader, p, ref_first, ref_size, "Registration reference")
        result, reference = _process_one_batch(p, frames, phase_term=phase)
        reference = result["M0ff"].copy()
    history = []
    stateful = p.get("shack_hartmann", False) and phase is None and p.get("sh_time_accumulation", 1) > 1
    def process_batch(frames, reference):
        return _process_one_batch(p, frames, M0_reg=reference,
                                  U_buffer=history if stateful else None, phase_term=phase)
    static = {} if coefs is None else {"shack_hartmann_autofocus_zernike_coefs": backend.to_numpy(coefs)}
    return run_pipeline(reader, p, process_batch, preview=preview, reference=reference,
                        static=static, stateful=stateful,
                        ecc_keys={"moment0", "moment0ff", "moment1", "moment2"},
                        progress_callback=progress_callback)


def preview(file_path, parameters):
    return _run(file_path, parameters, preview=True)


def process(file_path, parameters, progress_callback=None):
    return _run(file_path, parameters, progress_callback=progress_callback)
