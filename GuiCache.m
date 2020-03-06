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
    batch_size_factor_flag
    batch_size_factor
    notes
    DX
    DY
    horizontal_axis_flip
    vertical_axis_flip
    
    % iterative optimization parameters
    optimization_zernike_ranks
    mask_num_iter
    low_order_zernikes_tol
    high_order_zernikes_tol
    low_order_max_constraint
    high_order_max_constraint
    
    % shack-hartmann parameters
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