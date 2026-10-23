from holodoppler import backend
from holodoppler.core.filtering import filter_2d, pca_time_transform
from holodoppler.core.image_utils import gaussian_flatfield
from holodoppler.core.propagation import (
    angular_spectrum_transform,
    angular_spectrum_transform_with_phase,
    fresnel_transform,
    fresnel_transform_with_phase,
)
from holodoppler.core.registration import apply_register_images_shifts, register_images_shifts


from holodoppler.core.pipeline import prepare_input, read_reference, run_pipeline, batch_indices
from .main_default import _process_shack_hartmann, _get_autofocus_phase_term

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

    # no svd filtering
    holograms_f = holograms

    # ------------------------------------------------------------
    # PCA transform
    # ------------------------------------------------------------
    holograms_f = pca_time_transform(xp, holograms_f, remove_dc=False)

    # ------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------
    start, end = parameters["pca_range"]

    

    # ------------------------------------------------------------
    # Moments
    # ------------------------------------------------------------
    output_dict["PROJ"] = xp.sum(xp.abs(holograms_f)[start:end], axis=0)

    output_dict["PROJff"] = gaussian_flatfield(
        output_dict["PROJ"],
        parameters.get("registration_flatfield_gw", 1.0),
        backend.gaussian_filter,
    )

    return output_dict


def _process_one_batch(
    parameters,
    frames,
    PROJ_reg=None,
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
        PROJ_reg is None
        and parameters.get("image_registration", False)
    ):
        PROJ_reg = res["PROJff"]

    if PROJ_reg is not None:

        shift_y, shift_x = register_images_shifts(
            backend.xp,
            backend.fft,
            PROJ_reg,
            res["PROJff"],
            radius=parameters.get("registration_radius", .8),
            sub_pixel=parameters.get("registration_sub_pixel", True),
        )

        for key, value in list(res.items()):

            if (
                key in {"PROJff", "PROJ"}
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

    return res, PROJ_reg


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
        reference = result["PROJff"].copy()
    def process_batch(frames, reference):
        return _process_one_batch(p, frames, PROJ_reg=reference, phase_term=phase)
    static = {} if coefs is None else {"shack_hartmann_autofocus_zernike_coefs": backend.to_numpy(coefs)}
    return run_pipeline(reader, p, process_batch, preview=preview, preview_key="PROJff",
                        reference=reference, static=static, accumulation=p.get("accumulation", 1),
                        ecc_keys={"PROJ", "PROJff"}, progress_callback=progress_callback)


def preview(file_path, parameters):
    return _run(file_path, parameters, preview=True)


def process(file_path, parameters, progress_callback=None):
    return _run(file_path, parameters, progress_callback=progress_callback)
