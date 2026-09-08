import numpy as np
from collections import defaultdict
from pathlib import Path

import holodoppler.backend as backend
from tqdm import tqdm

from holodoppler.saving import (
    save_preview_images,
    save_outputs,
    get_default_output_path,
    save_h5,
)

from holodoppler.propagation import (
    fresnel_transform,
    fresnel_transform_with_phase,
    angular_spectrum_transform,
    angular_spectrum_transform_with_phase,
)

from holodoppler.shack_hartmann import (
    construct_subapertures_fresnel,
    construct_subapertures_angular,
    calculate_displacements,
    calculate_displacements_graph_laplacian,
)

from holodoppler.zernike import (
    fit_zernike_fresnel,
    fit_zernike_angular_spectrum,
)

from holodoppler.utils import (
    gaussian_flatfield,
    update_from_holo_footer,
    resize_frames,
)

from holodoppler.filtering import (
    filter_2d,
    svd_filter,
    frequency_symmetric_filtering,
    fourier_time_transform,
    corner_compensation,
)

from holodoppler.moments import moment

from holodoppler.registration import (
    register_images_shifts,
    apply_register_images_shifts,
)

from holodoppler.file_reader import FileReaderFactory


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
            holograms,
            parameters["svd_threshold"],
            filter_mode=parameters["svd_filter_mode"],
            remove_dc=parameters["svd_remove_dc"],
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
        parameters["sampling_freq"],
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
            parameters["sampling_freq"],
            f1,
            f2,
        )

        output_dict[f"band_{k}_{f1}_{f2}"] = xp.mean(
            psd[idxs_band],
            axis=0,
        )

    return output_dict


def _process_shack_hartmann(
    parameters,
    frames,
    output_dict=None,
):
    """
    Construct Shack-Hartmann sub-apertures, estimate displacements,
    and reconstruct the wavefront using a Zernike fit.
    """

    xp = backend.xp
    fft = backend.fft

    nt, ny, nx = frames.shape

    prop_method = parameters["spatial_propagation"]

    # ------------------------------------------------------------------
    # Construct sub-apertures
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Displacement estimation
    # ------------------------------------------------------------------
    if parameters.get(
        "shack_hartmann_graph_laplacian",
        False,
    ):
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

    # ------------------------------------------------------------------
    # Save sub-aperture image mosaic
    # ------------------------------------------------------------------
    if output_dict is not None:
        sy, sx, numy, numx = U.shape

        U_display = xp.transpose(
            U,
            axes=(0, 2, 1, 3),
        )

        output_dict["shack_hartmann_sub_images"] = xp.reshape(
            U_display,
            (numy * sy, numx * sx),
        )

    # U is no longer needed after displacement estimation.
    del U

    # ------------------------------------------------------------------
    # Zernike wavefront reconstruction
    # ------------------------------------------------------------------
    phase = None
    coefs = None

    if parameters.get(
        "shack_hartmann_zernike_fit",
        True,
    ):
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

        if output_dict is not None:
            output_dict["shack_hartmann_zernike_coefs"] = coefs
            output_dict["shack_hartmann_wavefront_phase"] = phase

    if phase is None:
        return None

    # ------------------------------------------------------------------
    # Phase correction term
    # ------------------------------------------------------------------
    phase_term = xp.exp(-1j * phase)

    phase_term = xp.nan_to_num(
        phase_term,
        nan=0.0,
    )

    return phase_term


def _process_one_batch(
    parameters,
    frames,
    M0_reg=None,
    U_buffer=None,
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

    phase_term = None

    # ------------------------------------------------------------------
    # Shack-Hartmann
    # ------------------------------------------------------------------
    if parameters.get("shack_hartmann", False):

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
                parameters["sampling_freq"],
                frames.shape[0],
                parameters["shack_hartmann_nx_subap"],
                parameters["shack_hartmann_ny_subap"],
                parameters["shack_hartmann_svd_threshold"],
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

        # --------------------------------------------------------------
        # Sliding U accumulation
        # --------------------------------------------------------------
        if U_buffer is not None:
            U_buffer.append(U)

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
        # Optional sub-aperture output
        # --------------------------------------------------------------
        if parameters.get(
            "save_shack_hartmann_sub_images",
            False,
        ):
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

            phase_term = xp.exp(-1j * phase)
            phase_term = xp.nan_to_num(
                phase_term,
                nan=0.0,
            )

        # The current U can be released when it is not retained by the
        # sliding buffer.
        if U_buffer is None:
            del U

        if U_tot is not U:
            del U_tot

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


def _append_numpy_results(output, res):
    """
    Convert a batch result to NumPy and append it to the output dict.
    """

    for key, value in res.items():
        output[key].append(
            backend.to_numpy(value)
        )


def preview(file_path, parameters):
    """
    Process a single preview batch.

    The preview uses the same backend abstraction as process(), so it
    works with either NumPy or CuPy.
    """

    file_reader = FileReaderFactory.create(file_path)

    print("previewing file :", file_path)

    # ------------------------------------------------------------------
    # File metadata
    # ------------------------------------------------------------------
    if file_reader.extension == ".holo":
        print("file header :", file_reader.header)

        parameters = update_from_holo_footer(
            parameters,
            file_reader.footer,
        )

    if file_reader.extension == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    # ------------------------------------------------------------------
    # Read preview frames
    # ------------------------------------------------------------------
    frames = file_reader.read_frames(
        first_frame=parameters["first_frame"],
        batch_size=parameters["batch_size"],
    )

    frames = backend.to_backend(frames)

    # Preserve the float32 behavior of the original GPU implementation.
    frames = frames.astype(
        backend.xp.float32,
        copy=False,
    )

    # ------------------------------------------------------------------
    # Process
    # ------------------------------------------------------------------
    res, _ = _process_one_batch(
        parameters,
        frames,
        M0_reg=None,
        U_buffer=None,
    )

    # ------------------------------------------------------------------
    # Square/resize preview outputs
    # ------------------------------------------------------------------
    if parameters.get("square", False):
        squared_res = {}

        for key, value in res.items():
            if value.ndim == 2:
                max_size = max(value.shape[-2:])

                squared_res[key] = resize_frames(
                    value,
                    max_size,
                    max_size,
                )
            else:
                squared_res[key] = value

        res = squared_res

    # ------------------------------------------------------------------
    # Transfer to CPU
    # ------------------------------------------------------------------
    res_np = {
        key: backend.to_numpy(value)
        for key, value in res.items()
    }

    del res
    del frames

    backend.clear_gpu_memory()

    # ------------------------------------------------------------------
    # Save preview
    # ------------------------------------------------------------------
    save_dir = (
        get_default_output_path(
            file_reader.file_path
        )
        / "preview"
    )

    save_preview_images(
        res_np,
        save_dir,
        square=True,
    )

    save_h5(
        save_dir,
        res_np,
        parameters,
    )

    return res_np


def process(file_path, parameters):
    """
    Process a complete holographic file.

    Supports:
        - CPU/NumPy execution
        - GPU/CuPy execution
        - asynchronous GPU prefetching
        - sliding Shack-Hartmann accumulation
        - image registration
        - Laplacian registration
        - frequency bands
        - optional output squaring
    """

    file_reader = FileReaderFactory.create(file_path)

    print("processing file :", file_path)

    # ------------------------------------------------------------------
    # File metadata
    # ------------------------------------------------------------------
    if file_reader.extension == ".holo":
        print("file header :", file_reader.header)

        parameters = update_from_holo_footer(
            parameters,
            file_reader.footer,
        )

    if file_reader.extension == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    # ------------------------------------------------------------------
    # Processing parameters
    #
    # The second implementation uses batch_size/batch_stride.
    # The first implementation used time_window/time_stride.
    #
    # Prefer the second API, but retain compatibility with parameters
    # from the first implementation where possible.
    # ------------------------------------------------------------------
    batch_size = parameters.get(
        "batch_size",
        parameters.get("time_window"),
    )

    batch_stride = parameters.get(
        "batch_stride",
        parameters.get("time_stride"),
    )

    first_frame = parameters["first_frame"]

    end_frame = parameters.get(
        "end_frame",
        0,
    )

    if batch_size is None:
        raise KeyError(
            "Missing 'batch_size' parameter"
        )

    if batch_stride is None:
        raise KeyError(
            "Missing 'batch_stride' parameter"
        )

    # ------------------------------------------------------------------
    # Determine total frame count
    # ------------------------------------------------------------------
    if end_frame <= 0:
        if hasattr(file_reader, "total_frames"):
            end_frame = file_reader.total_frames

        elif hasattr(file_reader, "TotalImageCount"):
            end_frame = file_reader.TotalImageCount

        elif hasattr(file_reader, "header"):
            end_frame = file_reader.header.num_frames

        else:
            raise AttributeError(
                "Unable to determine the total number of frames "
                "from the file reader."
            )

    # ------------------------------------------------------------------
    # Number of batches
    # ------------------------------------------------------------------
    available_frames = end_frame - first_frame

    if batch_stride >= available_frames:
        num_batch = (
            1
            if batch_size <= available_frames
            else 0
        )
    else:
        num_batch = int(
            available_frames / batch_stride
        )

    if num_batch <= 0:
        return None

    # ------------------------------------------------------------------
    # Output storage
    # ------------------------------------------------------------------
    output = defaultdict(list)

    M0_reg = None

    # ------------------------------------------------------------------
    # Sliding Shack-Hartmann configuration
    #
    # Use a normal list rather than deque so that the import list remains
    # identical to the requested second file.
    # ------------------------------------------------------------------
    sh_time_accumulation = parameters.get(
        "sh_time_accumulation",
        1,
    )

    if sh_time_accumulation <= 0:
        sh_time_accumulation = 1

    U_buffer = []

    # ------------------------------------------------------------------
    # Registration reference
    # ------------------------------------------------------------------
    if parameters.get(
        "image_registration",
        False,
    ):
        registration_ref_first_frame = parameters.get(
            "registration_ref_first_frame",
            0,
        )

        registration_ref_batch_size = parameters.get(
            "registration_ref_batch_size",
            batch_size,
        )

        if (
            registration_ref_first_frame != 0
            or registration_ref_batch_size != batch_size
        ):
            ref_frames = file_reader.read_frames(
                first_frame=registration_ref_first_frame,
                batch_size=registration_ref_batch_size,
            )

            ref_frames = backend.to_backend(
                ref_frames
            )

            ref_res, _ = _process_one_batch(
                parameters,
                ref_frames,
                M0_reg=None,
                U_buffer=None,
            )

            M0_reg = ref_res["M0ff"].copy()

            del ref_frames
            del ref_res

            backend.clear_gpu_memory()

    # ==================================================================
    # CPU / NumPy path
    # ==================================================================
    if not backend.is_gpu:

        for i in tqdm(range(num_batch)):

            current_first_frame = (
                first_frame
                + i * batch_stride
            )

            frames = file_reader.read_frames(
                first_frame=current_first_frame,
                batch_size=batch_size,
            )

            frames = backend.to_backend(
                frames
            )

            # ----------------------------------------------------------
            # Process one batch
            # ----------------------------------------------------------
            res, M0_reg = _process_one_batch(
                parameters,
                frames,
                M0_reg=M0_reg,
                U_buffer=(
                    U_buffer
                    if parameters.get(
                        "shack_hartmann",
                        False,
                    )
                    else None
                ),
            )

            # ----------------------------------------------------------
            # Keep U buffer bounded
            # ----------------------------------------------------------
            if len(U_buffer) > sh_time_accumulation:
                del U_buffer[
                    :len(U_buffer) - sh_time_accumulation
                ]

            _append_numpy_results(
                output,
                res,
            )

            del frames
            del res

    # ==================================================================
    # GPU / CuPy path
    # ==================================================================
    else:

        # --------------------------------------------------------------
        # CUDA streams
        # --------------------------------------------------------------
        h2d_stream = backend.xp.cuda.Stream(
            non_blocking=True
        )

        compute_stream = backend.xp.cuda.Stream(
            non_blocking=True
        )

        # --------------------------------------------------------------
        # Prefetch buffers
        # --------------------------------------------------------------
        PREFETCH_DEPTH = 4

        d_buffers = [None] * PREFETCH_DEPTH
        h2d_events = [None] * PREFETCH_DEPTH
        compute_events = [None] * PREFETCH_DEPTH

        buffer_ready = [False] * PREFETCH_DEPTH

        current_idx = 0
        processed_batches = 0

        # --------------------------------------------------------------
        # Prefetch + processing loop
        # --------------------------------------------------------------
        for i in tqdm(
            range(num_batch + PREFETCH_DEPTH)
        ):

            prefetch_idx = (
                i % PREFETCH_DEPTH
            )

            # ----------------------------------------------------------
            # Prefetch next batch
            # ----------------------------------------------------------
            if i < num_batch:

                current_first_frame = (
                    first_frame
                    + i * batch_stride
                )

                with h2d_stream:

                    frames = file_reader.read_frames(
                        first_frame=current_first_frame,
                        batch_size=batch_size,
                    )

                    d_buffers[prefetch_idx] = (
                        backend.xp.asarray(frames)
                    )

                    h2d_events[prefetch_idx] = (
                        backend.xp.cuda.Event()
                    )

                    h2d_events[prefetch_idx].record(
                        h2d_stream
                    )

                    buffer_ready[prefetch_idx] = True

            # ----------------------------------------------------------
            # Process ready buffers in order
            # ----------------------------------------------------------
            while (
                buffer_ready[current_idx]
                and current_idx != prefetch_idx
            ):

                h2d_events[
                    current_idx
                ].synchronize()

                with compute_stream:

                    d_current = d_buffers[
                        current_idx
                    ]

                    res, M0_reg = _process_one_batch(
                        parameters,
                        d_current,
                        M0_reg=M0_reg,
                        U_buffer=(
                            U_buffer
                            if parameters.get(
                                "shack_hartmann",
                                False,
                            )
                            else None
                        ),
                    )

                    compute_events[
                        current_idx
                    ] = backend.xp.cuda.Event()

                    compute_events[
                        current_idx
                    ].record(
                        compute_stream
                    )

                compute_events[
                    current_idx
                ].synchronize()

                # ------------------------------------------------------
                # Store result on CPU
                # ------------------------------------------------------
                _append_numpy_results(
                    output,
                    res,
                )

                processed_batches += 1

                # ------------------------------------------------------
                # Release buffer
                # ------------------------------------------------------
                buffer_ready[
                    current_idx
                ] = False

                d_buffers[
                    current_idx
                ] = None

                # ------------------------------------------------------
                # Limit sliding SH buffer
                # ------------------------------------------------------
                if len(U_buffer) > sh_time_accumulation:
                    del U_buffer[
                        :len(U_buffer)
                        - sh_time_accumulation
                    ]

                current_idx = (
                    current_idx + 1
                ) % PREFETCH_DEPTH

                if processed_batches >= num_batch:
                    break

            if processed_batches >= num_batch:
                break

        # --------------------------------------------------------------
        # Drain remaining buffers
        # --------------------------------------------------------------
        while buffer_ready[current_idx]:

            h2d_events[
                current_idx
            ].synchronize()

            with compute_stream:

                d_current = d_buffers[
                    current_idx
                ]

                res, M0_reg = _process_one_batch(
                    parameters,
                    d_current,
                    M0_reg=M0_reg,
                    U_buffer=(
                        U_buffer
                        if parameters.get(
                            "shack_hartmann",
                            False,
                        )
                        else None
                    ),
                )

                compute_events[
                    current_idx
                ] = backend.xp.cuda.Event()

                compute_events[
                    current_idx
                ].record(
                    compute_stream
                )

            compute_events[
                current_idx
            ].synchronize()

            _append_numpy_results(
                output,
                res,
            )

            processed_batches += 1

            buffer_ready[
                current_idx
            ] = False

            d_buffers[
                current_idx
            ] = None

            if len(U_buffer) > sh_time_accumulation:
                del U_buffer[
                    :len(U_buffer)
                    - sh_time_accumulation
                ]

            current_idx = (
                current_idx + 1
            ) % PREFETCH_DEPTH

            if processed_batches >= num_batch:
                break

    # ------------------------------------------------------------------
    # Stack batch results
    # ------------------------------------------------------------------
    output = {
        key: np.stack(
            values,
            axis=0,
        )
        for key, values in output.items()
    }

    # ------------------------------------------------------------------
    # Laplacian registration
    # ------------------------------------------------------------------
    if parameters.get(
        "registration_laplacian",
        False,
    ):

        # register_laplacian is intentionally not imported here because
        # the requested import list matches the second file. Therefore
        # this feature is implemented only when supplied by the backend
        # registration module through its existing public API.
        #
        # Import locally to preserve the requested top-level imports.
        from holodoppler.registration import (
            register_laplacian,
        )

        shifts_y, shifts_x = register_laplacian(
            backend.xp,
            backend.fft,
            backend.to_backend(
                output["M0ff"]
            ),
            radius=parameters.get(
                "registration_laplacian_radius",
                0.7,
            ),
        )

        shifts_y = shifts_y - shifts_y[0]
        shifts_x = shifts_x - shifts_x[0]

        output["register_laplacian"] = (
            backend.to_numpy(
                backend.xp.stack(
                    [
                        shifts_y,
                        shifts_x,
                    ]
                )
            )
        )

        shifts_y = np.rint(
            backend.to_numpy(shifts_y)
        ).astype(np.int64)

        shifts_x = np.rint(
            backend.to_numpy(shifts_x)
        ).astype(np.int64)

        for key, value in output.items():

            if (
                key in {
                    "M0ff",
                    "M0",
                    "M1",
                    "M2",
                }
                or "band_" in key
            ):

                for m in range(value.shape[0]):

                    value_backend = (
                        backend.to_backend(
                            value[m]
                        )
                    )

                    value_backend = (
                        apply_register_images_shifts(
                            backend.xp,
                            backend.fft,
                            value_backend,
                            int(shifts_y[m]),
                            int(shifts_x[m]),
                        )
                    )

                    output[key][m] = (
                        backend.to_numpy(
                            value_backend
                        )
                    )

    # ------------------------------------------------------------------
    # Square output images
    # ------------------------------------------------------------------
    if parameters.get(
        "square",
        False,
    ):

        squared_output = {}

        for key, value in output.items():

            if value.ndim >= 3:

                max_size = max(
                    value.shape[-2:]
                )

                if value.ndim == 3:
                    squared_output[key] = (
                        resize_frames(
                            value,
                            max_size,
                            max_size,
                        )
                    )
                else:
                    # Apply frame-by-frame for outputs with additional
                    # dimensions.
                    squared_output[key] = value

            else:
                squared_output[key] = value

        output = squared_output

    # ------------------------------------------------------------------
    # Compatibility names
    # ------------------------------------------------------------------
    #
    # Keep the second implementation's Doppler View naming convention.
    #
    output["moment0"] = output.pop("M0")
    output["moment0ff"] = output.pop("M0ff")
    output["moment1"] = output.pop("M1")
    output["moment2"] = output.pop("M2")

    # ------------------------------------------------------------------
    # GPU cleanup
    # ------------------------------------------------------------------
    backend.clear_gpu_memory()

    # ------------------------------------------------------------------
    # Save outputs
    # ------------------------------------------------------------------
    save_outputs(
        file_reader=file_reader,
        output=output,
        parameters=parameters,
    )

    return output