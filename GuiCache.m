classdef GuiCache
% A parameter cache to store parameters from GUI
% so that during computations, values are fetched from cache instead of GUI
% so that the user can modify the values in the GUI without messing
% everything up
properties (Access = public)
    batch_size
    batch_stride
    z
    f1
    f2
    wavelength
    Fs
    pix_width
    pix_height
    registration
    temporal_filter_flag
    temporal_filter
    parallelism
    registration_via_phase
    aberration_compensation
    notes
    DX
    DY
    position_in_file
    save_additional_videos
    
    % color image parameters
    color_f1
    color_f2
    color_f3
    low_frequency
    
    % iterative optimization parameters
    iterative_aberration_compensation
    optimization_zernike_ranks
    mask_num_iter
    zernikes_tol
    max_constraint
    
    % shack-hartmann parameters
    shack_hartmann_aberration_compensation
    shack_hartmann_zernike_ranks
    num_subapertures
    subaperture_margin
end
methods (Access = public)
    function obj = GuiCache()
        % do nothing
    end
end
end