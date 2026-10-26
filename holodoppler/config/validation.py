"""Parameter checks for the default processing pipeline."""

from numbers import Integral, Real
from math import isfinite

from holodoppler.logging import logger


def validate_main_parameters(parameters):
    """Check each main-pipeline parameter after metadata resolution without mutation."""

    value = parameters.get("skip_every")
    if value is not None:
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError("skip_every must be an integer or None")
        if value <= 0:
            raise ValueError("skip_every must be positive")

    value = parameters.get("pipeline_name", 'default')
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'pipeline_name' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("live_saving", True)
    if not isinstance(value, bool):
        raise TypeError("Parameter 'live_saving' must be a boolean.")

    value = parameters.get("num_saving_workers", 0)
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError("Parameter 'num_saving_workers' must be an integer.")
    if value < 0:
        raise ValueError("Parameter 'num_saving_workers' must be nonnegative.")

    value = parameters.get("saving_queue_depth")
    if value is not None:
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError("Parameter 'saving_queue_depth' must be an integer or null.")
        if value < 1:
            raise ValueError("Parameter 'saving_queue_depth' must be positive.")

    value = parameters.get("force_numpy", False)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'force_numpy' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("use_parallel", False)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'use_parallel' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("numpy_num_workers", 0)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'numpy_num_workers' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("cupy_async", True)
    if not isinstance(value, bool):
        raise TypeError("Parameter 'cupy_async' must be a boolean.")

    value = parameters.get("cupy_prefetch_depth", 4)
    if not isinstance(value, Integral) or isinstance(value, bool):
        raise TypeError("Parameter 'cupy_prefetch_depth' must be an integer.")
    if value < 1:
        raise ValueError("Parameter 'cupy_prefetch_depth' must be at least one.")

    value = parameters.get("batch_size", 256)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'batch_size' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("first_frame", 0)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'first_frame' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("batch_stride", 256)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'batch_stride' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("end_frame", -1)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'end_frame' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spatial_propagation", 'Fresnel')
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'spatial_propagation' has unresolved metadata placeholder {value!r}; "
            "required: spatial transformation name. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'spatial_propagation' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("z", 'use_holovibes')
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'z' has unresolved metadata placeholder {value!r}; "
            "required: numeric propagation distance in meters. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'z' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("wavelength", 8.52e-07)
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'wavelength' has unresolved metadata placeholder {value!r}; "
            "required: numeric wavelength in meters. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'wavelength' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("pixel_pitch", 'use_holovibes')
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'pixel_pitch' has unresolved metadata placeholder {value!r}; "
            "required: numeric pixel pitches [y, x] in meters. Supply it explicitly or check the file metadata."
        )
    if not (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(isinstance(v, Real) and not isinstance(v, bool) for v in value)
    ):
        raise TypeError(
            f"Parameter 'pixel_pitch' must be a pair of real numbers [y, x]; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("Fresnel_use_ouput_kernel", False)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'Fresnel_use_ouput_kernel' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("filter2d", False)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'filter2d' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("filter2d_low", 0.03)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'filter2d_low' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("svd_threshold", 39)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'svd_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("svd_filter_mode", 'number_of_values')
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'svd_filter_mode' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("svd_remove_dc", True)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'svd_remove_dc' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("temporal_transformation", 'FourierTransform')
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'temporal_transformation' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("sampling_freq", 'use_holovibes')
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'sampling_freq' has unresolved metadata placeholder {value!r}; "
            "required: numeric camera sampling frequency in Hz. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'sampling_freq' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("low_freq", 6000)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'low_freq' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("high_freq", 18300)
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'high_freq' has unresolved metadata placeholder {value!r}; "
            "required: numeric upper frequency cutoff in Hz. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'high_freq' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("frequency_bands", [[3000, 9000], [9000, 18000]])
    if not (
        isinstance(value, (list, tuple))
        and all(
            isinstance(pair, (list, tuple)) and len(pair) == 2
            and all(isinstance(v, Real) and not isinstance(v, bool) for v in pair)
            for pair in value
        )
    ):
        raise TypeError(
            f"Parameter 'frequency_bands' must be a sequence of real-number pairs; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_flatfield_gw", 35.0)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_flatfield_gw' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("image_registration", True)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'image_registration' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_ref_first_frame", 0)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_ref_first_frame' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_ref_batch_size", 512)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_ref_batch_size' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_radius", 0.8)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_radius' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_sub_pixel", True)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_sub_pixel' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("image_registration_with_ecc", False)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'image_registration_with_ecc' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_ecc_radius", 0.8)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_ecc_radius' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_ecc_min_threshold", 0.7)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_ecc_min_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("corner_compensation", False)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'corner_compensation' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("square", True)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'square' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("overwrite_option", 'erase')
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'overwrite_option' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_autofocus", False)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_autofocus' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_autofocus_z4_threshold_rad", 1.5)
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("shack_hartmann_autofocus_z4_threshold_rad must be a real number")
    if not isfinite(value) or value <= 0:
        raise ValueError("shack_hartmann_autofocus_z4_threshold_rad must be finite and positive")

    value = parameters.get("shack_hartmann_autofocus_batch_size", 256)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_autofocus_batch_size' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann", False)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_nx_subap", 5)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_nx_subap' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_ny_subap", 5)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_ny_subap' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_svd_threshold", 10)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_svd_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_pupil_threshold", 1.5)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_pupil_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_deviation_threshold", 10.0)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_deviation_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_shifts_pixel_range_threshold", 1000.0)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_shifts_pixel_range_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_graph_laplacian", True)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_graph_laplacian' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_zernike_fit", True)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_zernike_fit' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_zernike_fit_modes", [4, 5, 6])
    if not (
        isinstance(value, (list, tuple))
        and all(isinstance(v, Integral) and not isinstance(v, bool) for v in value)
    ):
        raise TypeError(
            f"Parameter 'shack_hartmann_zernike_fit_modes' must be a sequence of integers; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("save_spectograms", True)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'save_spectograms' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spectrogram_resize_shape", [128, 128])
    if not (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(isinstance(v, Integral) and not isinstance(v, bool) for v in value)
    ):
        raise TypeError(
            f"Parameter 'spectrogram_resize_shape' must be a pair of integers; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spectrogram_resize_order", 1)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'spectrogram_resize_order' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spectrogram_frequency_start", 0)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'spectrogram_frequency_start' must be a real number; got {value!r} ({type(value).__name__})."
        )
    if not 0 <= value <= 0.5:
        raise ValueError(
            f"Parameter 'spectrogram_frequency_start' must be between 0 and 0.5; got {value!r}."
        )

    value = parameters.get("spectrogram_frequency_end", 0.5)
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'spectrogram_frequency_end' must be a real number; got {value!r} ({type(value).__name__})."
        )
    if not 0 <= value <= 0.5:
        raise ValueError(
            f"Parameter 'spectrogram_frequency_end' must be between 0 and 0.5; got {value!r}."
        )

    value = parameters.get("spectrogram_frequency_binning", 4)
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'spectrogram_frequency_binning' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("save_averaged_spectrogram", True)
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'save_averaged_spectrogram' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    for key in ("color_Doppler_image", "color_Doppler_use_lab", "directional_Doppler_image"):
        if not isinstance(parameters.get(key, False), bool):
            raise TypeError(f"{key} must be a boolean")
    if parameters.get("color_Doppler_image", False) or parameters.get("directional_Doppler_image", False):
        if parameters.get("temporal_transformation") != "FourierTransform":
            raise ValueError("Doppler images require temporal_transformation='FourierTransform'")
        for key, default in (
            ("color_Doppler_low_frequency_band", [3000, 9000]),
            ("color_Doppler_high_frequency_band", [9000, 18000]),
            ("directional_Doppler_frequency_band", None),
        ):
            enabled = parameters.get("color_Doppler_image" if key.startswith("color_") else "directional_Doppler_image", False)
            if not enabled:
                continue
            band = parameters.get(key, default)
            if band is None and key == "directional_Doppler_frequency_band":
                continue
            if (not isinstance(band, (tuple, list)) or len(band) != 2
                    or any(isinstance(v, bool) or not isinstance(v, Real) or not isfinite(v) for v in band)
                    or not 0 <= band[0] < band[1]):
                raise ValueError(f"{key} must be [low, high] with finite frequencies and 0 <= low < high")
        if parameters.get("directional_Doppler_image", False):
            hues = parameters.get("directional_Doppler_hues", [1., .66])
            if (not isinstance(hues, (tuple, list)) or len(hues) != 2
                    or any(isinstance(v, bool) or not isinstance(v, Real)
                           or not isfinite(v) or not 0 <= v <= 1 for v in hues)):
                raise ValueError("directional_Doppler_hues must contain two finite hue values in [0, 1]")
            width = parameters.get("directional_Doppler_gaussian_width", 35.)
            if isinstance(width, bool) or not isinstance(width, Real) or not isfinite(width) or width < 0:
                raise ValueError("directional_Doppler_gaussian_width must be finite and nonnegative")

    logger.debug("Parameters: %s", parameters)
    return parameters
