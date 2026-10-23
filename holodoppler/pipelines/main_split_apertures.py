"""Full-pupil and quadrant Doppler reconstructions on NumPy or CuPy."""
from holodoppler import backend
from holodoppler.core.pipeline import prepare_input, read_reference, run_pipeline, batch_indices
from holodoppler.core.filtering import (svd_filter, frequency_symmetric_filtering,
    fourier_time_transform, pca_time_transform, filter_2d)
from holodoppler.core.image_utils import gaussian_flatfield, resize_frames, pad_array_centrally
from holodoppler.core.moments import moment
from holodoppler.core.propagation import (fresnel_transform, fresnel_transform_with_phase,
    angular_spectrum_transform, angular_spectrum_transform_with_phase,
    build_fresnel_kernel_in, build_fresnel_kernel_out)
from holodoppler.core.registration import register_images_shifts, apply_register_images_shifts
from .main_default import _process_shack_hartmann, _get_autofocus_phase_term

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

    idx_NW = ((0, cy), (0, cx))
    idx_NE = ((0, cy), (cx, nx))
    idx_SW = ((cy, ny), (0, cx))
    idx_SE = ((cy, ny), (cx, nx))

    return idx_NW, idx_NE, idx_SW, idx_SE


def phase_shift_out(xp,
    fft,
    pixel_pitch,
    wavelength,
    z,
    idx,
    nxny):

    ny, nx = nxny

    ppy, ppx = pixel_pitch

    y0 = (idx[0][0] + idx[0][1] - ny / 2) / 2 * ppy
    x0 = (idx[1][0] + idx[1][1] - nx / 2) / 2 * ppx

    fx = xp.fft.fftfreq(nx, d=ppx)
    fx = xp.fft.fftshift(fx)
    fy = xp.fft.fftfreq(ny, d=ppy)
    fy = xp.fft.fftshift(fy)
    FX, FY = xp.meshgrid(fx, fy)

    X = wavelength * z * FX
    Y = wavelength * z * FY

    return xp.exp(-1j * 2 * xp.pi * (Y * y0 + X * x0) / (wavelength * z))


def fresnel_transform_with_phase_2(
    xp,
    fft,
    frames,
    z,
    pixel_pitch,
    wavelength,
    phase_term,
    idx,
    nxny=(0, 0),
    zero_padding=False,
    use_output_kernel=True,
    output_shape=None,
):
    """Apply Fresnel transform with phase correction"""

    if phase_term is None:
        ny, nx = nxny
    else:
        ny, nx = phase_term.shape[-2:]

    kernel_in = build_fresnel_kernel_in(
        xp, z, pixel_pitch, wavelength, ny, nx, zero_padding=None
    )

    if phase_term is None:
        result = fft.fftshift(
            fft.fft2(
                frames * kernel_in[:, idx[0][0] : idx[0][1], idx[1][0] : idx[1][1]],
                s=output_shape,
                axes=(-2, -1),
                norm="ortho",
            ),
            axes=(-1, -2),
        )
    else:

        result = fft.fftshift(
            fft.fft2(
                frames
                * kernel_in[:, idx[0][0] : idx[0][1], idx[1][0] : idx[1][1]]
                * phase_term[xp.newaxis, idx[0][0] : idx[0][1], idx[1][0] : idx[1][1]],
                s=output_shape,
                axes=(-2, -1),
                norm="ortho",
            ),
            axes=(-1, -2),
        )

    Ny, Nx = result.shape[-2:]

    if use_output_kernel:
        kernel_out = build_fresnel_kernel_out(
            xp, z, pixel_pitch, wavelength, Ny, Nx, zero_padding=None
        )
        result = result * kernel_out

    result *= phase_shift_out(xp,fft,pixel_pitch,wavelength,z,idx, (Ny, Nx))

    return result


def _process_batch(parameters, frames, phase_term=None, output_dict=None):
    xp = backend.xp
    fft = backend.fft
    nt_sub = frames.shape[0]
    prop_method = parameters["spatial_propagation"]

    # Split into four quadrants
    mask_names = ["NW", "NE", "SW", "SE"]
    quadrant_indices = make_quadrant_indices(frames.shape[1:], center=None)
    quadrant_idxs = dict(zip(mask_names, quadrant_indices))

    # All quadrants use the same output grid, including odd-sized pupils.
    if min(frames.shape[-2:]) < 2:
        raise ValueError("Split apertures require at least two pixels per spatial dimension")
    target = tuple((size + 1) // 2 for size in frames.shape[-2:])
    U_quadrants = {}
    for qname, idx in quadrant_idxs.items():
        ys, xs = slice(*idx[0]), slice(*idx[1])
        cropped = frames[:, ys, xs]
        if prop_method == "Fresnel":
            U_q = fresnel_transform_with_phase_2(
                xp, fft, cropped, parameters["z"], tuple(parameters["pixel_pitch"]),
                parameters["wavelength"], phase_term, idx, nxny=frames.shape[-2:],
                use_output_kernel=parameters["Fresnel_use_ouput_kernel"],
                output_shape=target,
            )
        elif prop_method == "AngularSpectrum":
            if phase_term is not None:
                cropped = cropped * phase_term[ys, xs]
            cropped = pad_array_centrally(xp, cropped, target)
            U_q = angular_spectrum_transform(
                xp, fft, cropped, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"])
        else:
            raise ValueError(f"Unknown propagation method: {prop_method!r}")
        U_quadrants[qname] = U_q
    args = (xp, fft, frames, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"])
    if prop_method == "Fresnel":
        options = {"use_output_kernel": parameters["Fresnel_use_ouput_kernel"]}
        U_main = (fresnel_transform(*args, **options) if phase_term is None
                  else fresnel_transform_with_phase(*args, phase_term, **options))
    else:
        U_main = (angular_spectrum_transform(*args) if phase_term is None
                  else angular_spectrum_transform_with_phase(*args, phase_term))
    del frames

    # SVD filtering per q
    U_q_filt = {}
    for qname, U_q in U_quadrants.items():
        U_q_filt[qname] = svd_filter(
            xp,
            backend.linalg, U_q,
            parameters["svd_threshold"],
            filter_mode=parameters["svd_filter_mode"],
            remove_dc=parameters["svd_remove_dc"],
        )
    U_quadrants.clear()  # free memory
    del U_quadrants

    U_main = svd_filter(
        xp,
        backend.linalg, U_main,
        parameters["svd_threshold"],
        filter_mode=parameters["svd_filter_mode"],
        remove_dc=parameters["svd_remove_dc"],
    )

    if output_dict is None:
        output_dict = {}

    # Temporal transform

    idxs, freqs = frequency_symmetric_filtering(
        xp,
        fft,
        nt_sub,
        (parameters["sampling_freq"] / (parameters.get("skip_every") or 1)),
        parameters["low_freq"],
        parameters.get("high_freq"),
    )

    # Temporal transform

    U_main = fourier_time_transform(xp, fft, U_main)
    U_main = xp.abs(U_main) ** 2

    quadrant_moments = {}
    for qname, U_q in U_q_filt.items():
        spectrum_f = fourier_time_transform(xp, fft, U_q)
        psd = xp.abs(spectrum_f) ** 2
        qres = {
            qname + "_M0": moment(xp, psd[idxs], freqs, 0),
            qname + "_M1": moment(xp, psd[idxs], freqs, 1),
        }
        qres[qname + "_M0ff"] = gaussian_flatfield(
            qres[qname + "_M0"],
            parameters.get("registration_flatfield_gw", 1.0),
            backend.gaussian_filter,
        )
        quadrant_moments[qname] = qres
        output_dict.update(qres)

    combs = [
        # ["NW", "SW"],
        # ["NE", "SE"],
        # ["NW", "NE"],
        # ["SW", "SE"],
        ["NW", "SE"],
        ["NE", "SW"],
    ]  # only diagonals here

    def process_spectr(spectr, prefix, suffix, output_dict):
        A = xp.abs(spectr)

        P = xp.angle(spectr)

        output_dict[f"{prefix}_{suffix}_M0_HF"] = moment(xp, A[idxs], freqs, 0)
        output_dict[f"{prefix}_{suffix}_M0_HF_phi"] = moment(xp, P[idxs], freqs, 0)
        # output_dict[f"{prefix}_{suffix}_M1_HF"] = moment(xp, A[idxs], freqs, 1)

        for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
            idxs_band, freqs_band = frequency_symmetric_filtering(
                xp, fft, nt_sub, (parameters["sampling_freq"] / (parameters.get("skip_every") or 1)), f1, f2
            )
            output_dict[f"{prefix}_{suffix}_M0_LF_{k}"] = moment(
                xp, A[idxs_band], freqs_band, 0
            )
            # output_dict[f"{prefix}_{suffix}_M1_LF_{k}"] = moment(
            #     xp, A[idxs_band], freqs_band, 1
            # )

    def process_cube(cube, prefix, suffix, output_dict):
        A = xp.abs(cube)
        # P = xp.angle(cube)
        for k, (i1, i2) in enumerate(parameters.get("pca_indices", [])):
            output_dict[f"{prefix}_{suffix}_PCA_{k}"] = xp.mean(A[i1:i2], axis=0)
            # output_dict[f"{prefix}_{suffix}_PCA_{k}_phi"] = xp.mean(P[i1:i2], axis=0)


    def process_combination(U_q_filta, U_q_filtb, cname, suffix, output_dict):

        # A time fft

        # 1----- H conj
        spectr = fourier_time_transform(xp, fft, U_q_filta * U_q_filtb.conj())

        process_spectr(spectr, cname, f"{suffix}_Hconj", output_dict)

        # 2------- SH conj
        spectr = (
            fourier_time_transform(xp, fft, U_q_filta)
            * fourier_time_transform(xp, fft, U_q_filtb).conj()
        )

        process_spectr(spectr, cname, f"{suffix}_SHconj", output_dict)

        # B time pca

        proj_cube = pca_time_transform(xp, U_q_filta * U_q_filtb.conj(), remove_dc=True)
        process_cube(proj_cube, cname, f"{suffix}_Hconj", output_dict)


    for a_name, b_name in combs:
        cname = a_name + "x" + b_name

        process_combination(U_q_filt[a_name], U_q_filt[b_name], cname, "", output_dict)
        # process_combination(
        #     xp.abs(U_q_filt[a_name]),
        #     xp.abs(U_q_filt[b_name]),
        #     cname,
        #     "amp",
        #     output_dict,
        # )
        # process_combination(
        #     xp.angle(U_q_filt[a_name]),
        #     xp.angle(U_q_filt[b_name]),
        #     cname,
        #     "phi",
        #     output_dict,
        # )

    U_q_filt.clear()  # free memory
    del U_q_filt

    # B_E = quadrant_moments["NE"]["NE_M0"] + quadrant_moments["SE"]["SE_M0"]
    # B_W = quadrant_moments["NW"]["NW_M0"] + quadrant_moments["SW"]["SW_M0"]
    # B_N = quadrant_moments["NW"]["NW_M0"] + quadrant_moments["NE"]["NE_M0"]
    # B_S = quadrant_moments["SW"]["SW_M0"] + quadrant_moments["SE"]["SE_M0"]

    # # Uncomment these if you need to free memory
    # # del psd_full, quadrant_moments

    # eps = 1e-12
    # Ax = (B_E - B_W) / (B_E + B_W + eps)
    # Ay = (B_N - B_S) / (B_N + B_S + eps)
    # A_mag = xp.sqrt(Ax**2 + Ay**2)

    # NESW = (quadrant_moments["NE"]["NE_M0"] - quadrant_moments["SW"]["SW_M0"])
    # NWSE = (quadrant_moments["NW"]["NW_M0"] - quadrant_moments["SE"]["SE_M0"])

    # A_mag = xp.sqrt(Ax**2 + Ay**2)

    # # Add all the new values to output_dict
    # output_dict.update(
    #     {
    #         "B_E": B_E,
    #         "B_L": B_W,
    #         "B_N": B_N,
    #         "B_S": B_S,
    #         "NESW": NESW,
    #         "NWSE": NWSE,
    #         "Ax": Ax,
    #         "Ay": Ay,
    #         "A_mag": A_mag,
    #     }
    # )

    # Full pupil image reconstruction
    output_dict["M0"] = moment(xp, U_main[idxs], freqs, 0)

    sq = 0
    for qname, moments in quadrant_moments.items():
        sq += moments[
            qname + "_M0"
        ]  # xp.squeeze(square_cupy(moments[qname + "_M0"][xp.newaxis, ...], newy=ny, newx=nx))
    output_dict["QSum_M0"] = sq

    jo = sq - xp.squeeze(
        resize_frames(xp, backend.zoom,
            output_dict["M0"][xp.newaxis, ...], sq.shape[0], sq.shape[1]
        )
    )
    output_dict["J0_M0"] = jo

    output_dict["M1"] = moment(xp, U_main[idxs], freqs, 1)
    output_dict["M2"] = moment(xp, U_main[idxs], freqs, 2)
    output_dict["M0ff"] = gaussian_flatfield(
        output_dict["M0"],
        parameters.get("registration_flatfield_gw", 1.0),
        backend.gaussian_filter,
    )

    # Frequency bands à réactiver
    # for qname, psd in psd_q.items():
    #     bands = {}
    #     for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
    #         idxs_band, _ = frequency_symmetric_filtering(
    #             xp, fft, nt_sub, (parameters["sampling_freq"] / (parameters.get("skip_every") or 1)), f1, f2
    #         )
    #         band = xp.mean(psd[idxs_band], axis=0)
    #         bands[f"{qname}_band_{k}_{f1}_{f2}"] = band
    #         output_dict.update(bands)

    for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
        idxs_band, _ = frequency_symmetric_filtering(
            xp, fft, nt_sub, (parameters["sampling_freq"] / (parameters.get("skip_every") or 1)), f1, f2
        )
        band = xp.mean(U_main[idxs_band], axis=0)
        output_dict[f"band_{k}_{f1}_{f2}"] = band


def _process_one_batch(parameters, frames, reference=None, phase_term=None):
    xp = backend.xp
    if parameters.get("filter2d", False):
        frames = filter_2d(xp, backend.fft, frames, parameters["filter2d_low"])
    result = {}
    if phase_term is None and parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann(parameters, frames, output_dict=result)
    _process_batch(parameters, frames, phase_term=phase_term, output_dict=result)
    if reference is None and parameters.get("image_registration", False):
        reference = result["M0ff"].copy()
    if reference is not None:
        sy, sx = register_images_shifts(xp, backend.fft, reference, result["M0ff"],
            radius=parameters.get("registration_radius", .8), sub_pixel=parameters.get("registration_sub_pixel", True))
        for key, value in list(result.items()):
            if value.ndim == 2 and not key.startswith("shack_hartmann_"):
                ny, nx = value.shape
                result[key] = apply_register_images_shifts(xp, backend.fft, value,
                    sy * ny / reference.shape[-2], sx * nx / reference.shape[-1])
        result["registration"] = xp.stack([xp.asarray(sy), xp.asarray(sx)])
    return result, reference


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
    def process_batch(frames, reference):
        return _process_one_batch(p, frames, reference=reference, phase_term=phase)
    static = {} if coefs is None else {"shack_hartmann_autofocus_zernike_coefs": backend.to_numpy(coefs)}
    return run_pipeline(reader, p, process_batch, preview=preview, reference=reference,
                        static=static, progress_callback=progress_callback)


def preview(file_path, parameters):
    return _run(file_path, parameters, preview=True)


def process(file_path, parameters, progress_callback=None):
    return _run(file_path, parameters, progress_callback=progress_callback)
