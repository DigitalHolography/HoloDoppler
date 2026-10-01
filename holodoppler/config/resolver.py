"""Resolving parameters from acquisition metadata.

The shipped parameter files may leave a value as a sentinel such as
``"use_holovibes"`` or ``"use_metadata"``. These functions replace those
sentinels with the corresponding values read from the file's metadata, and are
the only place where a parameter value depends on the input file.
"""

from __future__ import annotations


def update_from_holo_footer(
    parameters,
    holofooter,
):
    """Update processing parameters using a HoloVibes footer.

    Parameters whose value is ``"use_holovibes"`` are replaced with the
    corresponding values found in the HoloVibes metadata.

    The original function name is retained for compatibility.
    """
    if holofooter is None:
        return parameters

    try:
        compute_settings = holofooter[
            "compute_settings"
        ]

        image_rendering = compute_settings[
            "image_rendering"
        ]

        info = holofooter[
            "info"
        ]

        # ------------------------------------------------------------------
        # Wavelength
        # ------------------------------------------------------------------

        if parameters.get(
            "wavelength"
        ) == "use_holovibes":
            parameters["wavelength"] = (
                image_rendering["lambda"]
            )

        # ------------------------------------------------------------------
        # Spatial propagation
        # ------------------------------------------------------------------

        if parameters.get(
            "spatial_propagation"
        ) == "use_holovibes":

            holovibes_transform = image_rendering[
                "space_transformation"
            ]

            if holovibes_transform == "FRESNELTR":
                parameters[
                    "spatial_propagation"
                ] = "Fresnel"

            elif holovibes_transform == "ANGULARTR":
                parameters[
                    "spatial_propagation"
                ] = "AngularSpectrum"

            else:
                print(
                    "Couldn't parse spatial transform name "
                    "in HoloVibes footer "
                    f"({holovibes_transform!r}); "
                    "using Fresnel."
                )

                parameters[
                    "spatial_propagation"
                ] = "Fresnel"

        # ------------------------------------------------------------------
        # Propagation distance
        # ------------------------------------------------------------------

        if parameters.get(
            "z"
        ) == "use_holovibes":
            parameters["z"] = image_rendering[
                "propagation_distance"
            ]

        # ------------------------------------------------------------------
        # Pixel pitch
        # ------------------------------------------------------------------

        if parameters.get(
            "pixel_pitch"
        ) == "use_holovibes":

            pixel_pitch = info[
                "pixel_pitch"
            ]

            parameters["pixel_pitch"] = (
                pixel_pitch["y"] * 1e-6,
                pixel_pitch["x"] * 1e-6,
            )

        # ------------------------------------------------------------------
        # Sampling frequency
        # ------------------------------------------------------------------

        if parameters.get(
            "sampling_freq"
        ) == "use_holovibes":

            parameters[
                "sampling_freq"
            ] = info["camera_fps"]

        # ------------------------------------------------------------------
        # High frequency
        # ------------------------------------------------------------------

        if parameters.get(
            "high_freq"
        ) == "use_holovibes":

            parameters[
                "high_freq"
            ] = info["camera_fps"] / 2

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(
            f"Issue from HoloVibes footer: {exc}"
        )

    return parameters



def update_from_cine_metadata(
        parameters,
        metadata
    ):

    # ------------------------------------------------------------------
    # Pixel pitch
    # ------------------------------------------------------------------

    if parameters.get(
        "pixel_pitch"
    ) == "use_metadata":

        parameters["pixel_pitch"] = (
            1/metadata.extra["biYPelsPerMeter"],
            1/metadata.extra["biXPelsPerMeter"],
        )

    # ------------------------------------------------------------------
    # Sampling frequency
    # ------------------------------------------------------------------

    if parameters.get(
        "sampling_freq"
    ) == "use_metadata":

        parameters[
            "sampling_freq"
        ] = metadata.extra["FrameRate"]
    # ------------------------------------------------------------------
    # High frequency
    # ------------------------------------------------------------------

    if parameters.get(
        "high_freq"
    ) == "use_metadata":

        parameters[
            "high_freq"
        ] = metadata.extra["FrameRate"] / 2
    
    return parameters
