classdef ShackHartmann
    properties
        n_pup % n_subapertures
        n_mode
        interp_factor
    end
    methods
        % methods declaration
        M_aso = construct_M_aso(obj, acquisition , gaussian_width, use_gpu)
        shifts = compute_images_shifts(obj, FH, calibration, f1, f2, fs, delta_x, delta_y, gaussian_width, use_gpu)
        
        % constructor
        function obj = ShackHartmann(n_pup, n_mode, interp_factor)
            obj.n_pup = n_pup;
            obj.n_mode = n_mode;
            obj.interp_factor = interp_factor;
        end
        
        function [M_aso, found] = fetch_M_aso_from_cache(obj, cache_dir)
            path = fullfile(cache_dir, sprintf('M_aso_%d_mode_%d.mat', obj.n_pup, obj.n_mode));
            if exist(path, 'file')
                M_aso = importdata(path);
                found = true;
            else
                M_aso = [];
                found = false;
            end
        end
        
        function save_M_aso(obj, cache_dir, M_aso)
            save(fullfile(cache_dir, sprintf('M_aso_%d_mode_%d.mat', obj.n_pup, obj.n_mode)), 'M_aso');
        end
    end
end