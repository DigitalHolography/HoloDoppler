classdef ShackHartmann

properties
    n_SubAp % size of subapertures
    n_SubAp_inter % number of sub_aparetures along a direction
    modes % idx array of zernikes
    calibration_factor
    SubAp_margin
    CorrMap_margin
    PowFilterPreCorr
    SigmaFilterPreCorr
    ref_image
    spatialTransformType
end

methods
    % methods declaration
    [M_aso, StitchedMomentsInMaso] = construct_M_aso(obj, f1, f2, gw, acquisition)
    [shifts, StitchedMomentsInSubApertures, StitchedCorrInSubApertures, FH] = compute_images_shifts(obj, FH, f1, f2, gw, calibration, enable_svd, svd_threshold, acquisition)
    phase = compute_SVD_for_SubAp(obj, FH, f1, f2, gw, calibration, enable_svd, acquisition);
    phase = compute_temporal_SVD_in_SubAp(obj, FH, f1, f2, gw, calibration, enable_svd, acquisition);
    [shifts, StitchedMomentsInSubApertures, StitchedCorrInSubApertures] = spatial_signal_analysis_PCA(obj, FH, f1, f2, gw, calibration, enable_svd, acquisition)
    SubFH = SubField(obj, FH);
    [idx_excluded_subap] = excluded_subapertures(obj, Nx, Ny)
    moment_chunk = reconstruct_moment_chunk(obj, FH_chunk, enable_svd, f1, f2, fs, gw);

    function obj = ShackHartmann(n_SubAp, n_SubAp_inter, p, calibration_factor, SubAp_margin, CorrMap_margin, PowFilterPreCorr, SigmaFilterPreCorr, ref_image, spatialTransformType)
        obj.n_SubAp = n_SubAp;
        obj.n_SubAp_inter = n_SubAp_inter;
        obj.modes = p;
        obj.calibration_factor = calibration_factor;
        obj.SubAp_margin = SubAp_margin;
        obj.CorrMap_margin = CorrMap_margin;
        obj.PowFilterPreCorr = PowFilterPreCorr;
        obj.SigmaFilterPreCorr = SigmaFilterPreCorr;
        obj.ref_image = ref_image;
        obj.spatialTransformType = spatialTransformType;
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
