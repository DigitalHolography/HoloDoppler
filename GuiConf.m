classdef GuiConf
    properties (Access = public)
        batch_size
        ref_batch_size
        batch_stride
        spatialTransformation
        z
        f1
        f2
        wavelength
        image_registration
        SVD
        Fs
        pix_width
        pix_height
        registration
        temporal_filter_flag
        temporal_filter
        gw
        parallelism
        registration_via_phase
        aberration_compensation
        notes
        DX
        DY
        position_in_file
        save_raw_videos
        save_additional_videos
        low_memory
        rephasing
        
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
        function obj = GuiConf()
            % do nothing
        end
    end
end