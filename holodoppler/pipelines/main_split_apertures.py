from holodoppler.saving import (
    save_preview_images,
    _get_default_output_path,
    _save_videos,
    _save_h5_2,
    _create_directories,
    _save_pngs,
    _save_metadata,
)
from holodoppler.propagation import (
    fresnel_transform,
    fresnel_transform_with_phase,
    angular_spectrum_transform,
    angular_spectrum_transform_with_phase,
    build_fresnel_kernel_in,
    build_fresnel_kernel_out,
    pad_array_centrally,
)
from holodoppler.shack_hartmann import (
    construct_subapertures_fresnel,
    construct_subapertures_angular,
    calculate_displacements,
    calculate_displacements_graph_laplacian,
)
from holodoppler.zernike import fit_zernike_fresnel, fit_zernike_angular_spectrum
from holodoppler.utils import (
    gaussian_flatfield,
    update_from_footer,
    normalize_to_uint8,
    square_cupy,
    stretchlim,
    imadjust,
    temporal_gaussian,
)
from holodoppler.filtering import (
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

import cupy as cp

# import numpy as np
from cupyx.scipy.ndimage import gaussian_filter

# from cupyx.scipy.ndimage import zoom
from tqdm import tqdm

from pathlib import Path


from collections import defaultdict


# ----------------------------------------------------------------------
#  Quadrant mask generation
# ----------------------------------------------------------------------
def make_quadrant_masks(shape, center=None):
    """
    Create boolean masks for NW, NE, SW, SE quadrants.
    shape : (ny, nx) of the pupil plane.
    center : (cy, cx) - if None, use geometric centre.
    """
    ny, nx = shape
    if center is None:
        cy, cx = ny // 2, nx // 2
    else:
        cy, cx = center

    Y, X = cp.ogrid[:ny, :nx]
    mask_NW = (Y <= cy) & (X <= cx)
    mask_NE = (Y <= cy) & (X > cx)
    mask_SW = (Y > cy) & (X <= cx)
    mask_SE = (Y > cy) & (X > cx)

    return mask_NW, mask_NE, mask_SW, mask_SE


def make_quadrant_indices(shape, center=None):
    """
    Create indices for NW, NE, SW, SE quadrants.
    shape : (ny, nx) of the pupil plane.
    center : (cy, cx) - if None, use geometric centre.
    """
    ny, nx = shape
    if center is None:
        cy, cx = ny // 2, nx // 2
    else:
        cy, cx = center

    idx_NW = ((0, cy ), (0, cx ))
    idx_NE = ((0, cy ), (cx , nx + 1))
    idx_SW = ((cy , ny + 1), (0, cx ))
    idx_SE = ((cy , ny + 1), (cx , nx + 1))
    
    return idx_NW, idx_NE, idx_SW, idx_SE


def fresnel_transform_with_phase_2(
    xp,
    fft,
    frames,
    z,
    pixel_pitch,
    wavelength,
    phase_term,
    idx,
    zero_padding=False,
    use_output_kernel=True,
):
    """Apply Fresnel transform with phase correction"""

    ny, nx = phase_term.shape[-2:]
    kernel_in = build_fresnel_kernel_in(
        xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None
    )

    result = fft.fftshift(
        fft.fft2(
            frames
            * kernel_in[:, idx[0][0] : idx[0][1], idx[1][0] : idx[1][1]]
            * phase_term[xp.newaxis, idx[0][0] : idx[0][1], idx[1][0] : idx[1][1]],
            axes=(-1, -2),
            norm="ortho",
        ),
        axes=(-1, -2),
    )

    return result


def _process_batch(parameters, frames, phase_term=None, output_dict=None):
    xp = cp
    fft = cp.fft
    nt_sub = frames.shape[0]
    prop_method = parameters["spatial_propagation"]

    # Split into four quadrants
    mask_names = ["NW", "NE", "SW", "SE"]
    quadrant_indices = make_quadrant_indices(frames.shape[1:], center=None)
    quadrant_idxs = dict(zip(mask_names, quadrant_indices))

    

    # Propagation
    U_quadrants = {}
    for qname, idx in quadrant_idxs.items():
        cropped_frames = frames[:, idx[0][0] : idx[0][1], idx[1][0] : idx[1][1]]
        if phase_term is not None:
            if prop_method == "Fresnel":
                U_q = fresnel_transform_with_phase_2(
                    xp,
                    fft,
                    cropped_frames,
                    parameters["z"],
                    parameters["pixel_pitch"],
                    parameters["wavelength"],
                    phase_term,
                    idx=quadrant_idxs[qname],
                    zero_padding=parameters.get("Fresnel_zero_padding", False),
                    use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
                )
        else:
            if prop_method == "Fresnel":
                U_q = fresnel_transform_with_phase_2(
                    xp,
                    fft,
                    cropped_frames,
                    parameters["z"],
                    parameters["pixel_pitch"],
                    parameters["wavelength"],
                    None,
                    idx=quadrant_idxs[qname],
                    use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
                )
        U_quadrants[qname] = U_q

    if phase_term is not None:
        if prop_method == "Fresnel":
            U_main = fresnel_transform_with_phase(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
                phase_term,
                zero_padding=parameters.get("Fresnel_zero_padding", False),
                use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
            )
    else:
        if prop_method == "Fresnel":
            U_main = fresnel_transform_with_phase(
                xp,
                fft,
                frames,
                parameters["z"],
                parameters["pixel_pitch"],
                parameters["wavelength"],
                None,
                use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
            )
    del frames


    # use combinations of quadrants here :

    combs = [[("NW",), ("SE",)], [("NE",), ("SW",)]] # only diagonals here

    U_combs = {}
    for addition_names, soustraction_names in combs:
        cname = ''.join(["+" + nm for nm in addition_names]) + ''.join(["-" + nm for nm in soustraction_names])
        U_combs[cname] = sum([U_quadrants[nm] for nm in addition_names]) - sum([U_quadrants[nm] for nm in soustraction_names])
    U_quadrants.clear()  # free memory
    del U_quadrants

    # SVD filtering per c
    U_q_filt = {}
    for qname, U_q in U_combs.items():
        U_q_filt[qname] = svd_filter(
            xp,
            U_q,
            parameters["svd_threshold"],
            filter_mode=parameters["svd_filter_mode"],
            remove_dc=parameters["svd_remove_dc"],
        )
    U_combs.clear()  # free memory
    del U_combs
    

    U_main = svd_filter(
        xp,
        U_main,
        parameters["svd_threshold"],
        filter_mode=parameters["svd_filter_mode"],
        remove_dc=parameters["svd_remove_dc"],
    )

    if output_dict is None:
        output_dict = {}

    # Temporal transform
    spectrum_f_q = {}
    for qname, U_q in U_q_filt.items():
        if parameters.get("temporal_transformation") == "FourierTransform":
            spectrum_f = fourier_time_transform(xp, fft, U_q)
        else:
            spectrum_f = U_q
        spectrum_f_q[qname] = spectrum_f

    U_q_filt.clear()  # free memory
    del U_q_filt

    U_main = fourier_time_transform(xp, fft, U_main)

    # Frequency selection
    idxs, freqs = frequency_symmetric_filtering(
        xp,
        fft,
        nt_sub,
        parameters["sampling_freq"],
        parameters["low_freq"],
        parameters.get("high_freq"),
    )

    psd_q = {}
    for qname, spectrum_f in spectrum_f_q.items():
        psd = xp.abs(spectrum_f) ** 2
        psd_q[qname] = psd
    spectrum_f_q.clear()  # free memory
    del spectrum_f_q

    U_main = xp.abs(U_main) ** 2

    if parameters.get("corner_compensation", False):
        for qname, psd in psd_q.items():
            psd_q[qname] = corner_compensation(xp, psd)

    # Moments
    quadrant_moments = {}
    for qname, psd in psd_q.items():
        qres = {
            qname + "_M0": moment(xp, psd[idxs], freqs, 0),
            qname + "_M1": moment(xp, psd[idxs], freqs, 1),
            qname + "_M2": moment(xp, psd[idxs], freqs, 2),
        }
        qres[qname + "_M0ff"] = gaussian_flatfield(
            qres[qname + "_M0"],
            parameters.get("registration_flatfield_gw", 1.0),
            gaussian_filter,
        )
        quadrant_moments[qname] = qres
        output_dict.update(qres)

    # # Normalization
    # psd_q_norm = {}
    # for cname, psd in psd_c.items():
    #     M0 = combinations_moments[cname][cname + "_M0"]
    #     total_energy = xp.sum(M0)  # scalar
    #     if total_energy == 0:
    #         total_energy = 1e-24
    #     psd_q_norm[cname] = psd / total_energy
    # del M0, total_energy

    # Full pupil image reconstruction
    output_dict["M0"] = moment(xp, U_main[idxs], freqs, 0)
    output_dict["M1"] = moment(xp, U_main[idxs], freqs, 1)
    output_dict["M2"] = moment(xp, U_main[idxs], freqs, 2)
    output_dict["M0ff"] = gaussian_flatfield(
        output_dict["M0"],
        parameters.get("registration_flatfield_gw", 1.0),
        gaussian_filter,
    )

    # Frequency bands
    for qname, psd in psd_q.items():
        bands = {}
        for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
            idxs_band, _ = frequency_symmetric_filtering(
                xp, fft, nt_sub, parameters["sampling_freq"], f1, f2
            )
            band = xp.mean(psd[idxs_band], axis=0)
            bands[f"{qname}_band_{k}_{f1}_{f2}"] = band
            output_dict.update(bands)

    # # Full pupil image reconstruction
    # psd_full = psd_q["NW"].copy()
    # psd_full += psd_q["NE"]
    # psd_full += psd_q["SW"]
    # psd_full += psd_q["SE"]

    # del psd_q  # free memory

    # I_full = xp.mean(psd_full, axis=0)

    # B_inc = sum(quadrant_moments[q][f"{q}_M0"] for q in quadrant_idxs.keys())

    # B_R = quadrant_moments["NE"]["NE_M0"] + quadrant_moments["SE"]["SE_M0"]
    # B_L = quadrant_moments["NW"]["NW_M0"] + quadrant_moments["SW"]["SW_M0"]
    # B_S = quadrant_moments["NW"]["NW_M0"] + quadrant_moments["NE"]["NE_M0"]
    # B_I = quadrant_moments["SW"]["SW_M0"] + quadrant_moments["SE"]["SE_M0"]

    # del psd_full, quadrant_moments

    # eps = 1e-12
    # Ax = (B_R - B_L) / (B_R + B_L + eps)
    # Ay = (B_S - B_I) / (B_S + B_I + eps)
    # A_mag = xp.sqrt(Ax**2 + Ay**2)

    # output_dict.update(
    #     {
    #         "I_full": I_full,
    #         "B_inc": B_inc,
    #         "B_R": B_R,
    #         "B_L": B_L,
    #         "B_S": B_S,
    #         "B_I": B_I,
    #         "Ax": Ax,
    #         "Ay": Ay,
    #         "A_mag": A_mag,
    #     }
    # )

    # del I_full, B_inc, B_R, B_L, B_S, B_I, Ax, Ay, A_mag


def _process_shack_hartmann(parameters, frames, output_dict=None):

    fft = cp.fft
    nt, ny, nx = frames.shape

    prop_method = parameters["spatial_propagation"]

    if prop_method == "Fresnel":
        U = construct_subapertures_fresnel(
            cp,
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
            cp,
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

    # Displacement estimation
    if parameters.get("shack_hartmann_graph_laplacian", False):  # Use all the sub aps
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            cp,
            fft,
            U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get(
                "shack_hartmann_deviation_threshold", 3.0
            ),
            shifts_range=parameters.get(
                "shack_hartmann_shifts_pixel_range_threshold", 20.0
            ),
        )
    else:  # Use only the shifts to the central sub ap
        ny_s, nx_s, Ny, Nx = U.shape
        shifts_y, shifts_x = calculate_displacements(
            cp,
            fft,
            U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get(
                "shack_hartmann_deviation_threshold", 3.0
            ),
            shifts_range=parameters.get(
                "shack_hartmann_shifts_pixel_range_threshold", 20.0
            ),
        )

    if output_dict is not None:

        sy, sx, numy, numx = U.shape
        U = cp.transpose(U, axes=(0, 2, 1, 3))
        output_dict["shack_hartmann_sub_images"] = cp.reshape(U, (numy * sy, numx * sx))

    del U, frames  # Memory footprint reduction

    # Phase reconstruction
    phase = None
    if parameters.get("shack_hartmann_zernike_fit", True):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                cp,
                ny,
                nx,
                parameters["pixel_pitch"][0],
                parameters["pixel_pitch"][1],
                parameters["wavelength"],
                shifts_y,
                shifts_x,
                parameters.get("shack_hartmann_zernike_fit_modes"),
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                cp,
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

    # Phase reconstruction
    phase = None
    if parameters.get("shack_hartmann_zernike_fit", True):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                cp,
                ny,
                nx,
                parameters["pixel_pitch"][0],
                parameters["pixel_pitch"][1],
                parameters["wavelength"],
                shifts_y,
                shifts_x,
                parameters.get("shack_hartmann_zernike_fit_modes"),
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                cp,
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
        # elif parameters.get("shack_hartmann_southwell_phase_integration", False):
        #     phase = southwell_phase_integration(
        #         bm, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
        #         parameters["wavelength"], shifts_y, shifts_x
        #     )
        if output_dict is not None:
            output_dict["shack_hartmann_zernike_coefs"] = coefs
            output_dict["shack_hartmann_wavefront_phase"] = phase
    else:
        phase = None

    # Phase correction term
    phase_term = None
    if phase is not None:
        phase_term = cp.exp(-1j * phase)
        phase_term = cp.nan_to_num(phase_term, nan=0.0)

    return phase_term


def preview(file_path, parameters):
    file_reader = FileReaderFactory.create(file_path)

    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)
    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    first_frame = parameters["first_frame"]
    frames = file_reader.read_frames(first_frame=first_frame, batch_size=batch_size)

    # transfer to gpu
    frames = cp.array(frames, dtype=cp.float32)

    res = {}

    phase_term = None
    if parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann(parameters, frames, output_dict=res)

    # calc on gpu
    _process_batch(parameters, frames=frames, phase_term=phase_term, output_dict=res)

    # transfer to cpu
    res_np = {k: cp.asnumpy(v) for k, v in res.items()}

    # free gpu ram
    del res
    cp.get_default_memory_pool().free_all_blocks()

    save_preview_images(
        res_np, _get_default_output_path(file_reader.file_path) / "preview"  / "SPLIT_APERTURES"
    )

    return res_np["M0ff"]


def process(file_path, parameters):
    import numpy as np

    file_reader = FileReaderFactory.create(file_path)

    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)

    # print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]
    end_frame = parameters.get("end_frame", 0)
    if end_frame <= 0:
        end_frame = (
            file_reader.file_header.num_frames
            if file_reader.ext == ".holo"
            else file_reader.TotalImageCount
        )

    if batch_stride >= (end_frame - first_frame):
        num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame) / batch_stride)
    if num_batch <= 0:
        return None

    output_np = defaultdict(list)

    # creating the registration reference image
    M0_reg = None
    if parameters["image_registration"] and (
        parameters["registration_ref_first_frame"] != 0
        or parameters["registration_ref_batch_size"] != parameters["batch_size"]
    ):
        frames = file_reader.read_frames(
            first_frame=parameters["registration_ref_first_frame"],
            batch_size=parameters["registration_ref_batch_size"],
        )
        frames = cp.array(frames)
        phase_term = None
        if parameters.get("shack_hartmann", False):
            phase_term = _process_shack_hartmann(parameters, frames)
        res = {}
        _process_batch(parameters, frames, phase_term=phase_term, output_dict=res)
        M0_reg = res["M0ff"].copy()
        print(res.keys())
        del frames, phase_term  # Memory footprint reduction
        res.clear()
        del res

    h2d_stream = cp.cuda.Stream(non_blocking=True)
    # d2h_stream = cp.cuda.Stream(non_blocking=True)
    compute_stream = cp.cuda.Stream(non_blocking=True)

    processed_batches = 0

    PREFETCH_DEPTH = 4  # Number of batches to prefetch ahead (set to 3 or 4)

    # prefetch buffers
    d_buffers = [None] * PREFETCH_DEPTH
    h2d_events = [None] * PREFETCH_DEPTH
    compute_events = [None] * PREFETCH_DEPTH
    buffer_ready = [False] * PREFETCH_DEPTH

    current_idx = 0
    processed_batches = 0

    for i in tqdm(range(num_batch + PREFETCH_DEPTH)):

        prefetch_idx = i % PREFETCH_DEPTH

        if i < num_batch:
            with h2d_stream:
                frames = file_reader.read_frames(
                    first_frame=first_frame + i * batch_stride, batch_size=batch_size
                )
                d_buffers[prefetch_idx] = cp.asarray(frames)

                h2d_events[prefetch_idx] = cp.cuda.Event()
                h2d_events[prefetch_idx].record(h2d_stream)
                buffer_ready[prefetch_idx] = True

        while buffer_ready[current_idx] and current_idx != prefetch_idx:

            h2d_events[current_idx].synchronize()

            with compute_stream:
                d_current = d_buffers[current_idx]

                res = {}

                phase_term = None
                if parameters.get("shack_hartmann", False):
                    phase_term = _process_shack_hartmann(
                        parameters, d_current, output_dict=res
                    )

                _process_batch(
                    parameters, d_current, phase_term=phase_term, output_dict=res
                )

                if (
                    M0_reg is None and parameters["image_registration"]
                ):  # first batch is used for fixed batch
                    M0_reg = res["M0ff"]

                if M0_reg is not None:
                    shift_y, shift_x = register_images_shifts(
                        cp,
                        cp.fft,
                        M0_reg,
                        res["M0ff"],
                        radius=parameters["registration_radius"],
                        sub_pixel=parameters["registration_sub_pixel"],
                    )

                for k, v in res.items():
                    if isinstance(v, cp.ndarray) and v.ndim == 2:
                        ny, nx = v.shape[-2:]
                        reg_ny, reg_nx = M0_reg.shape[-2:]
                        res[k] = apply_register_images_shifts(
                            cp, cp.fft, v, shift_y*ny/reg_ny, shift_x*nx/reg_nx
                        )

                res["registration"] = cp.stack([cp.array(shift_y), cp.array(shift_x)])

                compute_events[current_idx] = cp.cuda.Event()
                compute_events[current_idx].record(compute_stream)

            compute_events[current_idx].synchronize()

            if res:
                for k, v in res.items():
                    output_np[k].append(cp.asnumpy(v))

            processed_batches += 1

            buffer_ready[current_idx] = False
            d_buffers[current_idx] = None  # Free memory
            current_idx = (current_idx + 1) % PREFETCH_DEPTH

            if processed_batches >= num_batch:
                break

    while buffer_ready[current_idx]:

        h2d_events[current_idx].synchronize()

        with compute_stream:
            d_current = d_buffers[current_idx]

            res = {}

            phase_term = None
            if parameters.get("shack_hartmann", False):
                phase_term = _process_shack_hartmann(
                    parameters, d_current, output_dict=res
                )

            _process_batch(
                parameters, d_current, phase_term=phase_term, output_dict=res
            )

            if M0_reg is None and parameters["image_registration"]:
                M0_reg = res["M0ff"]

            if M0_reg is not None:
                shift_y, shift_x = register_images_shifts(
                    cp,
                    cp.fft,
                    M0_reg,
                    res["M0ff"],
                    radius=parameters["registration_radius"],
                    sub_pixel=parameters["registration_sub_pixel"],
                )

            for k, v in res.items():
                if isinstance(v, cp.ndarray) and v.ndim == 2:
                    res[k] = apply_register_images_shifts(
                        cp, cp.fft, v, shift_y, shift_x
                    )

            res["registration"] = cp.stack([cp.array(shift_y), cp.array(shift_x)])

            compute_events[current_idx] = cp.cuda.Event()
            compute_events[current_idx].record(compute_stream)

        compute_events[current_idx].synchronize()

        if res:
            for k, v in res.items():
                output_np[k].append(cp.asnumpy(v))

        processed_batches += 1

        buffer_ready[current_idx] = False
        d_buffers[current_idx] = None
        current_idx = (current_idx + 1) % PREFETCH_DEPTH

        if processed_batches >= num_batch:
            break

    # Free memory
    for i in range(PREFETCH_DEPTH):
        d_buffers[i] = None
        h2d_events[i] = None
        compute_events[i] = None
    del d_buffers, h2d_events, compute_events, buffer_ready

    for k, v in output_np.items():
        output_np[k] = np.stack(v, axis=0)

    if parameters.get("square", False):
        output_np = {
            k: cp.asnumpy(square_cupy(cp.array(v))) if v.ndim == 3 else v for k, v in output_np.items()
        }

    # Use output_np as the main numpy result dict

    cp.get_default_memory_pool().free_all_blocks()

    target_dir = _get_default_output_path(file_reader.file_path) / "SPLIT_APERTURES"

    if "saving_to_folder" in parameters:
        target_dir = Path(parameters["saving_to_folder"])

    _create_directories(target_dir, "FULL")

    save_to_h5_list = [
        # "M0ff",
        # "M0",
        # "M1",
        # "M2",
        "shack_hartmann_zernike_coefs",
        "registration",
    ] #+ [key for key in output_np.keys() if "band_" in key]

    _save_h5_2(target_dir, output_np, parameters, save_only_list=save_to_h5_list)

    # Save videos (sequential to avoid encoding conflicts)
    _save_videos(target_dir, output_np, 30)

    # Save PNGs (parallel)
    _save_pngs(target_dir, output_np)

    # Save metadata (fast)
    _save_metadata(target_dir, file_reader, parameters)
