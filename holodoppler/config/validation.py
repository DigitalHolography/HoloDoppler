"""Parameter checks for the default processing pipeline."""

from numbers import Integral, Real


def validate_main_parameters(parameters):
    """Check each main-pipeline parameter after metadata resolution without mutation."""

    value = parameters.get("pipeline_name")
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'pipeline_name' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("force_numpy")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'force_numpy' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("use_parallel")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'use_parallel' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("numpy_num_workers")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'numpy_num_workers' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("batch_size")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'batch_size' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("first_frame")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'first_frame' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("batch_stride")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'batch_stride' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("end_frame")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'end_frame' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spatial_propagation")
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'spatial_propagation' has unresolved metadata placeholder {value!r}; "
            "required: spatial transformation name. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'spatial_propagation' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("z")
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'z' has unresolved metadata placeholder {value!r}; "
            "required: numeric propagation distance in meters. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'z' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("wavelength")
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'wavelength' has unresolved metadata placeholder {value!r}; "
            "required: numeric wavelength in meters. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'wavelength' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("pixel_pitch")
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

    value = parameters.get("Fresnel_use_ouput_kernel")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'Fresnel_use_ouput_kernel' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("filter2d")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'filter2d' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("filter2d_low")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'filter2d_low' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("svd_threshold")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'svd_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("svd_filter_mode")
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'svd_filter_mode' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("svd_remove_dc")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'svd_remove_dc' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("temporal_transformation")
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'temporal_transformation' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("sampling_freq")
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'sampling_freq' has unresolved metadata placeholder {value!r}; "
            "required: numeric camera sampling frequency in Hz. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'sampling_freq' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("low_freq")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'low_freq' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("high_freq")
    if isinstance(value, str) and value in ("use_holovibes", "use_metadata"):
        raise ValueError(
            f"Parameter 'high_freq' has unresolved metadata placeholder {value!r}; "
            "required: numeric upper frequency cutoff in Hz. Supply it explicitly or check the file metadata."
        )
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'high_freq' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("frequency_bands")
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

    value = parameters.get("registration_flatfield_gw")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_flatfield_gw' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("image_registration")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'image_registration' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_ref_first_frame")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_ref_first_frame' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_ref_batch_size")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_ref_batch_size' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_radius")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_radius' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_sub_pixel")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_sub_pixel' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("image_registration_with_ecc")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'image_registration_with_ecc' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_ecc_radius")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_ecc_radius' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("registration_ecc_min_threshold")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'registration_ecc_min_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("corner_compensation")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'corner_compensation' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("square")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'square' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("overwrite_option")
    if not (isinstance(value, str)):
        raise TypeError(
            f"Parameter 'overwrite_option' must be a string; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_autofocus")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_autofocus' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_autofocus_batch_size")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_autofocus_batch_size' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_nx_subap")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_nx_subap' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_ny_subap")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_ny_subap' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_svd_threshold")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_svd_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_pupil_threshold")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_pupil_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_deviation_threshold")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_deviation_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_shifts_pixel_range_threshold")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_shifts_pixel_range_threshold' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_graph_laplacian")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_graph_laplacian' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_zernike_fit")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'shack_hartmann_zernike_fit' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("shack_hartmann_zernike_fit_modes")
    if not (
        isinstance(value, (list, tuple))
        and all(isinstance(v, Integral) and not isinstance(v, bool) for v in value)
    ):
        raise TypeError(
            f"Parameter 'shack_hartmann_zernike_fit_modes' must be a sequence of integers; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("save_spectograms")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'save_spectograms' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spectrogram_resize_shape")
    if not (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(isinstance(v, Integral) and not isinstance(v, bool) for v in value)
    ):
        raise TypeError(
            f"Parameter 'spectrogram_resize_shape' must be a pair of integers; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spectrogram_resize_order")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'spectrogram_resize_order' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spectrogram_frequency_start")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'spectrogram_frequency_start' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spectrogram_frequency_end")
    if not (isinstance(value, Real) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'spectrogram_frequency_end' must be a real number; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("spectrogram_frequency_binning")
    if not (isinstance(value, Integral) and not isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'spectrogram_frequency_binning' must be an integer; got {value!r} ({type(value).__name__})."
        )

    value = parameters.get("save_averaged_spectrogram")
    if not (isinstance(value, bool)):
        raise TypeError(
            f"Parameter 'save_averaged_spectrogram' must be a boolean; got {value!r} ({type(value).__name__})."
        )

    print("parameters : ", parameters)
    return parameters
