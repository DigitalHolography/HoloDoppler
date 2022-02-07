classdef ShackHartmann
    properties
        n_SubAp % n_subapertures
        modes % idx array of zernikes
        calibration_factor
        SubAp_margin
        CorrMap_margin 
        PowFilterPreCorr
        SigmaFilterPreCorr  
    end
    methods
        % methods declaration
        [M_aso,StitchedMomentsInMaso] = construct_M_aso(obj, f1, f2, gw, acquisition)
        [shifts,StitchedMomentsInSubApertures,StitchedCorrInSubApertures] = compute_images_shifts(obj, FH, f1, f2, gw, calibration, enable_svd, acquisition)
        [shifts,StitchedMomentsInSubApertures,StitchedCorrInSubApertures] = spatial_signal_analysis_PCA(obj, FH, f1, f2, gw, calibration, enable_svd, acquisition)

        function obj = ShackHartmann(n_SubAp, p, calibration_factor,SubAp_margin,CorrMap_margin,PowFilterPreCorr,SigmaFilterPreCorr)
            obj.n_SubAp = n_SubAp;
            obj.modes = p;
            obj.calibration_factor = calibration_factor;
            obj.SubAp_margin = SubAp_margin;
            obj.CorrMap_margin = CorrMap_margin;
            obj.PowFilterPreCorr = PowFilterPreCorr;
            obj.SigmaFilterPreCorr = SigmaFilterPreCorr;
        end
        
        % reload M_aso that was previously constructed
        % to avoid recomputing it each time
        function [M_aso, found] = fetch_M_aso_from_cache(obj, cache_dir)
            path = fullfile(cache_dir, sprintf('M_aso_%d_mode_%d.mat', obj.n_SubAp, obj.n_modes));
            if exist(path, 'file')
                M_aso = importdata(path);
                found = true;
            else
                M_aso = [];
                found = false;
            end
        end
        
        function save_M_aso(obj, cache_dir, M_aso)
            save(fullfile(cache_dir, sprintf('M_aso_%d_mode_%d.mat', obj.n_SubAp, obj.n_modes)), 'M_aso');
        end
    end
end