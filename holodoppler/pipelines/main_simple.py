import os
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from collections import defaultdict
from pathlib import Path

import holodoppler.backend as backend
from tqdm import tqdm

from holodoppler.saving import (
    save_outputs,
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
    register_with_ecc,
    apply_ecc_registration
)

from holodoppler.file_reader import FileReaderFactory


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
        holograms,
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

    psd = xp.abs(spectrum_f) ** 2

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

    # ------------------------------------------------------------
    # Moments
    # ------------------------------------------------------------
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

    output_dict["M0ff"] = gaussian_flatfield(
        output_dict["M0"],
        parameters.get("registration_flatfield_gw", 1.0),
        backend.gaussian_filter,
    )

    output_dict["spectrum_line"] = xp.mean(
        psd,
        axis=(-2, -1),
    )

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

    return output_dict


def _process_shack_hartmann(
    parameters,
    frames,
    output_dict=None,
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

    nt, ny, nx = frames.shape
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
    coefs = None

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


def _get_autofocus_phase_term(parameters, file_reader):
    """
    Compute the Shack-Hartmann autofocus correction once from
    the configured reference batch.

    Reference batch:
        start = registration_ref_first_frame
        size  = batch_size

    Returns
    -------
    phase_term : backend array or None
        Fixed phase correction to use for all processed batches.
    """

    if not parameters.get("shack_hartmann_autofocus", False):
        return None

    print(
        "Running Shack-Hartmann autofocus from reference batch:",
        f"first_frame={parameters['registration_ref_first_frame']},",
        f"batch_size={parameters['batch_size']}",
    )

    ref_first_frame = parameters["registration_ref_first_frame"]
    ref_batch_size = parameters["batch_size"]

    ref_frames = file_reader.read_frames(
        first_frame=ref_first_frame,
        batch_size=ref_batch_size,
    )

    if ref_frames.shape[0] == 0:
        raise ValueError(
            "Shack-Hartmann autofocus reference batch is empty."
        )

    ref_frames = backend.to_backend(ref_frames).astype(
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
    )

    coefs = autofocus_result["shack_hartmann_zernike_coefs"]

    del ref_frames
    del autofocus_result

    if phase_term is None:
        raise RuntimeError(
            "Shack-Hartmann autofocus was enabled, but no phase "
            "correction was produced."
        )

    print("Shack-Hartmann autofocus phase correction computed.")

    return phase_term, coefs


def _process_one_batch(
    parameters,
    frames,
    M0_reg=None,
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
        M0_reg is None
        and parameters.get("image_registration", False)
    ):
        M0_reg = res["M0ff"]

    if M0_reg is not None:

        shift_y, shift_x = register_images_shifts(
            backend.xp,
            backend.fft,
            M0_reg,
            res["M0ff"],
            radius=parameters["registration_radius"],
            sub_pixel=parameters["registration_sub_pixel"],
        )

        for key, value in list(res.items()):

            if (
                key in {"M0ff", "M0", "M1", "M2"}
                or "band_" in key
            ):
                res[key] = apply_register_images_shifts(
                    backend.xp,
                    backend.fft,
                    value,
                    shift_y,
                    shift_x,
                )

        res["registration"] = backend.xp.stack(
            [
                backend.xp.asarray(shift_y),
                backend.xp.asarray(shift_x),
            ]
        )

    return res, M0_reg


def _append_numpy_results(output, res):
    for key, value in res.items():
        output[key].append(
            backend.to_numpy(value)
        )

def _process_numpy(
    parameters,
    file_reader,
    first_frame,
    num_batch,
    batch_stride,
    batch_size,
    output,
    M0_reg=None,
    autofocus_phase_term=None,
):
    """
    Sequential NumPy/CPU processing.

    This is the direct CPU equivalent of the original NumPy path.

    Parameters
    ----------
    parameters : dict
        Processing parameters.

    file_reader :
        Frame reader.

    first_frame : int
        Index of the first frame.

    num_batch : int
        Number of batches.

    batch_stride : int
        Frame stride between batches.

    batch_size : int
        Number of frames per batch.

    output : defaultdict(list)
        Output accumulator.

    M0_reg : numpy.ndarray or None
        Registration reference.

    autofocus_phase_term :
        Optional autofocus phase term passed to
        _process_one_batch().
    """

    for i in tqdm(
        range(num_batch),
        desc="Processing (NumPy)",
    ):
        frames = file_reader.read_frames(
            first_frame=(
                first_frame
                + i * batch_stride
            ),
            batch_size=batch_size,
        )

        # Keep the CPU path explicitly float32.
        frames = backend.to_backend(frames).astype(
            backend.xp.float32,
            copy=False,
        )

        res, M0_reg = _process_one_batch(
            parameters,
            frames,
            M0_reg=M0_reg,
            phase_term=autofocus_phase_term,
        )

        _append_numpy_results(
            output,
            res,
        )

        del frames
        del res

    return output, M0_reg


# ============================================================================
# NumPy / CPU parallel
# ============================================================================

def _get_numpy_workers(n_workers=None):
    """
    Return a safe number of NumPy workers.

    Default:
        8 workers

    Safety limit:
        half of the available CPU cores.

    Examples
    --------
    4 cores:
        max 2 workers

    8 cores:
        max 4 workers

    16 cores:
        max 8 workers

    32 cores:
        max 8 workers
    """

    cpu_count = os.cpu_count() or 1

    # Fail-safe: never use more than half the CPU cores.
    safe_cpu_limit = max(
        1,
        cpu_count // 2,
    )

    # Requested default.
    if n_workers is None:
        n_workers = 8

    n_workers = max(
        1,
        int(n_workers),
    )

    return min(
        n_workers,
        safe_cpu_limit,
    )


def _process_numpy_parallel(
    parameters,
    file_reader,
    first_frame,
    num_batch,
    batch_stride,
    batch_size,
    output,
    M0_reg=None,
    autofocus_phase_term=None,
    n_workers=None,
):
    """
    Parallel NumPy/CPU processing.

    NumPy batches are processed concurrently using a
    ThreadPoolExecutor.

    The default number of workers is 8, capped at half
    of the available CPU cores.

    IMPORTANT
    ---------
    Image registration introduces a dependency between batches
    through M0_reg.

    Therefore, when image_registration=True, this function
    safely falls back to the sequential NumPy implementation.

    This keeps the behavior of _process_one_batch() unchanged.
    """

    # ------------------------------------------------------------------
    # Registration is stateful:
    #
    # batch 0 -> establishes M0_reg
    # batch 1 -> uses M0_reg
    # batch 2 -> uses M0_reg
    # ...
    #
    # Therefore batches cannot safely be processed independently.
    # ------------------------------------------------------------------
    if parameters.get(
        "image_registration",
        False,
    ):
        return _process_numpy(
            parameters=parameters,
            file_reader=file_reader,
            first_frame=first_frame,
            num_batch=num_batch,
            batch_stride=batch_stride,
            batch_size=batch_size,
            output=output,
            M0_reg=M0_reg,
            autofocus_phase_term=autofocus_phase_term,
        )

    n_workers = _get_numpy_workers(
        n_workers,
    )

    def process_batch(i):
        """
        Read and process one independent batch.

        Since image registration is disabled here, M0_reg does
        not need to be shared between workers.
        """

        frames = file_reader.read_frames(
            first_frame=(
                first_frame
                + i * batch_stride
            ),
            batch_size=batch_size,
        )

        # Match the normal NumPy path.
        frames = backend.to_backend(frames).astype(
            backend.xp.float32,
            copy=False,
        )

        res, _ = _process_one_batch(
            parameters,
            frames,
            M0_reg=None,
            phase_term=autofocus_phase_term,
        )

        del frames

        return res

    # ------------------------------------------------------------------
    # ThreadPoolExecutor is appropriate here when the expensive work
    # is performed by NumPy/SciPy operations that release the GIL.
    #
    # executor.map() preserves the input order, so results are appended
    # in exactly the same batch order as the sequential implementation.
    # ------------------------------------------------------------------
    with ThreadPoolExecutor(
        max_workers=n_workers,
    ) as executor:

        results = executor.map(
            process_batch,
            range(num_batch),
        )

        for res in tqdm(
            results,
            total=num_batch,
            desc=(
                f"Processing "
                f"(NumPy, {n_workers} workers)"
            ),
        ):
            _append_numpy_results(
                output,
                res,
            )

            del res

    return output, M0_reg


# ============================================================================
# CuPy / GPU
# ============================================================================

def _process_cupy(
    parameters,
    file_reader,
    first_frame,
    num_batch,
    batch_stride,
    batch_size,
    output,
    M0_reg=None,
    autofocus_phase_term=None,
):
    h2d_stream = backend.xp.cuda.Stream(
        non_blocking=True
    )

    compute_stream = backend.xp.cuda.Stream(
        non_blocking=True
    )

    PREFETCH_DEPTH = 4

    d_buffers = [None] * PREFETCH_DEPTH
    h2d_events = [None] * PREFETCH_DEPTH
    compute_events = [None] * PREFETCH_DEPTH
    buffer_ready = [False] * PREFETCH_DEPTH

    current_idx = 0
    processed_batches = 0

    for i in tqdm(
        range(
            num_batch + PREFETCH_DEPTH
        )
    ):
        prefetch_idx = (
            i % PREFETCH_DEPTH
        )

        # ------------------------------------------------------------
        # Prefetch next batch to GPU
        # ------------------------------------------------------------

        if i < num_batch:

            with h2d_stream:

                frames = file_reader.read_frames(
                    first_frame=(
                        first_frame
                        + i * batch_stride
                    ),
                    batch_size=batch_size,
                )

                # KEEP THIS EXACTLY AS IN THE ORIGINAL CODE.
                d_buffers[
                    prefetch_idx
                ] = backend.xp.asarray(
                    frames
                )

                h2d_events[
                    prefetch_idx
                ] = backend.xp.cuda.Event()

                h2d_events[
                    prefetch_idx
                ].record(
                    h2d_stream
                )

                buffer_ready[
                    prefetch_idx
                ] = True

        # ------------------------------------------------------------
        # Process ready batches
        # ------------------------------------------------------------

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
                    phase_term=autofocus_phase_term,
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

            current_idx = (
                current_idx + 1
            ) % PREFETCH_DEPTH

            if processed_batches >= num_batch:
                break

        if processed_batches >= num_batch:
            break

    # ------------------------------------------------------------
    # Flush remaining prefetched batches
    # ------------------------------------------------------------

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
                phase_term=autofocus_phase_term,
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

        current_idx = (
            current_idx + 1
        ) % PREFETCH_DEPTH

        if processed_batches >= num_batch:
            break

    return output, M0_reg

def preview(file_path, parameters):
    file_reader = FileReaderFactory.create(file_path)

    print("previewing file :", file_path)

    if file_reader.extension == ".holo":
        print("file header :", file_reader.header)

        parameters = update_from_holo_footer(
            parameters,
            file_reader.footer,
        )

    if file_reader.extension == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    # ------------------------------------------------------------
    # Build autofocus phase once from the configured reference batch
    # ------------------------------------------------------------
    autofocus_phase_term, auto_coefs = _get_autofocus_phase_term(
        parameters,
        file_reader,
    )
    auto_coefs = backend.to_numpy(auto_coefs)

    # ------------------------------------------------------------
    # Preview frames
    # ------------------------------------------------------------
    frames = file_reader.read_frames(
        first_frame=parameters["first_frame"],
        batch_size=parameters["batch_size"],
    )

    frames = backend.to_backend(frames).astype(
        backend.xp.float32,
        copy=False,
    )

    res = {}

    # If autofocus is active, reuse the reference correction here.
    # Otherwise live Shack-Hartmann is handled by _process_one_batch().
    res, _ = _process_one_batch(
        parameters,
        frames,
        M0_reg=None,
        phase_term=autofocus_phase_term,
    )

    res["shack_hartmann_autofocus_zernike_coefs"] = auto_coefs

    # ------------------------------------------------------------
    # Square output
    # ------------------------------------------------------------
    if parameters.get("square", False):
        res = {
            k: (
                resize_frames(
                    v,
                    max(v.shape[-2:]),
                    max(v.shape[-2:]),
                )
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

    save_outputs(
        file_reader=file_reader,
        output=res_np,
        parameters=parameters,
        custom_relative_path="preview",
        square=True,
    )

    return res_np["M0ff"]


def process(file_path, parameters):
    file_reader = FileReaderFactory.create(file_path)

    if file_reader.extension == ".holo":
        print("file header :", file_reader.header)

        parameters = update_from_holo_footer(
            parameters,
            file_reader.footer,
        )

    if file_reader.extension == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]

    end_frame = parameters.get(
        "end_frame",
        0,
    )

    if end_frame <= 0:
        end_frame = file_reader.total_frames

    span = end_frame - first_frame

    if span <= 0:
        return

    # ------------------------------------------------------------
    # Number of processing batches
    # ------------------------------------------------------------
    if batch_stride >= span:
        num_batch = (
            1
            if batch_size <= span
            else 0
        )
    else:
        num_batch = int(
            span / batch_stride
        )

    if num_batch <= 0:
        return

    output = defaultdict(list)

    M0_reg = None

    # ------------------------------------------------------------
    # Build the registration reference once
    # ------------------------------------------------------------
    if (
        parameters.get(
            "image_registration",
            False,
        )
        and (
            parameters["registration_ref_first_frame"] != 0
            or parameters["registration_ref_batch_size"]
            != parameters["batch_size"]
        )
    ):

        ref_frames = file_reader.read_frames(
            first_frame=parameters[
                "registration_ref_first_frame"
            ],
            batch_size=parameters[
                "registration_ref_batch_size"
            ],
        )

        ref_frames = backend.to_backend(ref_frames).astype(
            backend.xp.float32,
            copy=False,
        )

        ref_res, _ = _process_one_batch(
            parameters,
            ref_frames,
            M0_reg=None,
            phase_term=None,
        )

        M0_reg = ref_res["M0ff"].copy()

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
    autofocus_phase_term, auto_coefs = _get_autofocus_phase_term(
        parameters,
        file_reader,
    )
    auto_coefs = backend.to_numpy(auto_coefs)

    # ------------------------------------------------------------
    # NumPy / CPU path
    # ------------------------------------------------------------
    if not backend.is_gpu or parameters.get("no_cupy",False):

        n_workers = parameters.get("numpy_num_workers",8)

        if n_workers > 0:

            output, M0_reg = _process_numpy_parallel(
                parameters=parameters,
                file_reader=file_reader,
                first_frame=first_frame,
                num_batch=num_batch,
                batch_stride=batch_stride,
                batch_size=batch_size,
                output=output,
                M0_reg=M0_reg,
                autofocus_phase_term=autofocus_phase_term,
                n_workers=n_workers,
            )

        else:

            output, M0_reg = _process_numpy(
                parameters=parameters,
                file_reader=file_reader,
                first_frame=first_frame,
                num_batch=num_batch,
                batch_stride=batch_stride,
                batch_size=batch_size,
                output=output,
                M0_reg=M0_reg,
                autofocus_phase_term=autofocus_phase_term,
            )
    else:

        output, M0_reg = _process_cupy(
            parameters=parameters,
            file_reader=file_reader,
            first_frame=first_frame,
            num_batch=num_batch,
            batch_stride=batch_stride,
            batch_size=batch_size,
            output=output,
            M0_reg=M0_reg,
            autofocus_phase_term=autofocus_phase_term,
        )

    # ------------------------------------------------------------
    # Stack outputs
    # ------------------------------------------------------------
    output = {
        key: np.stack(
            values,
            axis=0,
        )
        for key, values in output.items()
    }

    output["shack_hartmann_autofocus_zernike_coefs"] = auto_coefs

    # ------------------------------------------------------------
    # ECC Image Registration at the end
    # ------------------------------------------------------------

    if parameters.get("image_registration_with_ecc", False):
        print(
            "Running Registration ECC algo:"
        )
        registration_ecc = register_with_ecc(output["M0ff"],radius=parameters.get("registration_ecc_radius",0.8),iterations=300,eps=1e-6)


        for key in output :
            if key in {"M0ff", "M0", "M1", "M2"} or "band_" in key :
                output[key] = apply_ecc_registration(output[key], registration_ecc, background="mean")

        output["registration_ecc"] = registration_ecc
        print(
            "Registration calculated."
        )


    # ------------------------------------------------------------
    # Square spatial outputs
    # ------------------------------------------------------------
    if parameters.get("square", False):

        output = {
            key: (
                resize_frames(
                    value,
                    max(value.shape[-2:]),
                    max(value.shape[-2:]),
                )
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

    save_outputs(
        file_reader=file_reader,
        output=output,
        parameters=parameters,
    )