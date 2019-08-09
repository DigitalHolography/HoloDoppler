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
    optimization_plan
    additional_zernike_ranks
    registration_f1
    registration_f2
    first_name
    last_name
    year_of_birth
    notes
    DX
    DY
    horizontal_axis_flip
end
methods (Access = public)
    function obj = GuiCache()
        % do nothing
    end
end
end