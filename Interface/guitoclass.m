function guitoclass(HD, app)
% Transfers all values from app UI to HD.params

% Helper function to safely get UI value
function val = safeGetUIValue(uiComponent, defaultValue)
    val = defaultValue;
    try
        if isprop(uiComponent, 'Value') && ~isempty(uiComponent.Value)
            val = uiComponent.Value;
        end
    catch
        % If anything goes wrong, use default
    end
end

% Helper function to safely get checkbox value
function val = safeGetCheckbox(uiComponent, defaultValue)
    val = defaultValue;
    try
        if isprop(uiComponent, 'Value') && islogical(uiComponent.Value) && ~isempty(uiComponent.Value)
            val = uiComponent.Value;
        end
    catch
        % If anything goes wrong, use default
    end
end

% Basic parameters
if isprop(app, 'fs')
    HD.params.fs = safeGetUIValue(app.fs, 0);
end

if isprop(app, 'lambda')
    HD.params.lambda = safeGetUIValue(app.lambda, 0);
end

if isprop(app, 'ppx')
    HD.params.ppx = safeGetUIValue(app.ppx, 0);
end

if isprop(app, 'ppy')
    HD.params.ppy = safeGetUIValue(app.ppy, 0);
end

if isprop(app, 'parfor_arg')
    HD.params.parfor_arg = safeGetUIValue(app.parfor_arg, 10);
end

if isprop(app, 'batchSize')
    HD.params.batchSize = safeGetUIValue(app.batchSize, 512);
end

if isprop(app, 'refBatchSize')
    HD.params.refBatchSize = safeGetUIValue(app.refBatchSize, 512);
end

if isprop(app, 'batchStride')
    HD.params.batchStride = safeGetUIValue(app.batchStride, 512);
end

% Frame position
if isprop(app, 'positioninfileSlider')
    HD.params.frame_position = round(safeGetUIValue(app.positioninfileSlider, 1));
end

% Registration parameters
if isprop(app, 'registration_disc_ratio')
    HD.params.registration_disc_ratio = safeGetUIValue(app.registration_disc_ratio, 0.8);
end

% Handle image types as a cell array
if isprop(app, 'Image_typesListBox') && isprop(app.Image_typesListBox, 'Value')
    value = app.Image_typesListBox.Value;
    if ~isempty(value)
        HD.params.image_types = value;
    end
end

% Image registration
if isprop(app, 'image_registration')
    HD.params.image_registration = safeGetCheckbox(app.image_registration, false);
end

% Spatial filtering parameters
if isprop(app, 'spatial_filter')
    HD.params.spatial_filter = safeGetCheckbox(app.spatial_filter, false);
end

if isprop(app, 'hilbert_filter')
    HD.params.hilbert_filter = safeGetCheckbox(app.hilbert_filter, false);
end

if isprop(app, 'spatial_filter_range1') && isprop(app, 'spatial_filter_range2')
    val1 = safeGetUIValue(app.spatial_filter_range1, 0);
    val2 = safeGetUIValue(app.spatial_filter_range2, 1);
    HD.params.spatial_filter_range = [val1, val2];
end

if isprop(app, 'spatial_transformation')
    HD.params.spatial_transformation = safeGetUIValue(app.spatial_transformation, 'Fresnel');
end

if isprop(app, 'spatial_propagation')
    HD.params.spatial_propagation = safeGetUIValue(app.spatial_propagation, 0);
end

if isprop(app, 'Padding_num')
    HD.params.Padding_num = safeGetUIValue(app.Padding_num, 0);
end

% SVD parameters
if isprop(app, 'svd_filter')
    HD.params.svd_filter = safeGetCheckbox(app.svd_filter, false);
end

if isprop(app, 'svdx_filter')
    HD.params.svdx_filter = safeGetCheckbox(app.svdx_filter, false);
end

if isprop(app, 'svdx_t_filter')
    HD.params.svdx_t_filter = safeGetCheckbox(app.svdx_t_filter, false);
end

if isprop(app, 'svd_threshold')
    HD.params.svd_threshold = safeGetUIValue(app.svd_threshold, 0);
end

if isprop(app, 'svdx_threshold')
    HD.params.svdx_threshold = safeGetUIValue(app.svdx_threshold, 0);
end

if isprop(app, 'svdx_t_threshold')
    HD.params.svdx_t_threshold = safeGetUIValue(app.svdx_t_threshold, 0);
end

if isprop(app, 'svdx_Nsub')
    HD.params.svdx_Nsub = safeGetUIValue(app.svdx_Nsub, 1);
end

if isprop(app, 'svdx_t_Nsub')
    HD.params.svdx_t_Nsub = safeGetUIValue(app.svdx_t_Nsub, 1);
end

% Time transformation parameters
if isprop(app, 'time_transform')
    HD.params.time_transform = safeGetUIValue(app.time_transform, 'FFT');
end

if isprop(app, 'time_range1') && isprop(app, 'time_range2')
    val1 = safeGetUIValue(app.time_range1, 0);
    val2 = safeGetUIValue(app.time_range2, 100);
    HD.params.time_range = [val1, val2];
end

if isprop(app, 'index_range1') && isprop(app, 'index_range2')
    val1 = safeGetUIValue(app.index_range1, 1);
    val2 = safeGetUIValue(app.index_range2, 100);
    HD.params.index_range = [val1, val2];
end

% Flatfield correction
if isprop(app, 'flat_field_gw')
    HD.params.flatfield_gw = safeGetUIValue(app.flat_field_gw, 0);
end

% Image transformations
if isprop(app, 'flip_y')
    HD.params.flip_y = safeGetCheckbox(app.flip_y, false);
end

if isprop(app, 'flip_x')
    HD.params.flip_x = safeGetCheckbox(app.flip_x, false);
end

if isprop(app, 'square')
    HD.params.square = safeGetCheckbox(app.square, false);
end

% Registration options
if isprop(app, 'AutofocusFromRef')
    HD.params.applyautofocusfromref = safeGetCheckbox(app.AutofocusFromRef, false);
end

if isprop(app, 'applyshackhartmannfromref')
    HD.params.applyshackhartmannfromref = safeGetCheckbox(app.applyshackhartmannfromref, false);
end

% Shack-Hartmann correction
if isprop(app, 'ShackHartmannCheckBox')
    if safeGetCheckbox(app.ShackHartmannCheckBox, false)
        % Initialize structure if it doesn't exist
        if ~isfield(HD.params, 'ShackHartmannCorrection') || isempty(HD.params.ShackHartmannCorrection)
            HD.params.ShackHartmannCorrection = struct();
        end
        
        if isprop(app, 'IterativeCheckBox')
            HD.params.ShackHartmannCorrection.iterate = safeGetCheckbox(app.IterativeCheckBox, false);
        end
        
        if isprop(app, 'NumberOfIterationEditField')
            HD.params.ShackHartmannCorrection.N_iterate = safeGetUIValue(app.NumberOfIterationEditField, 3);
        end
        
        if isprop(app, 'ZernikeProjectionCheckBox')
            HD.params.ShackHartmannCorrection.ZernikeProjection = safeGetCheckbox(app.ZernikeProjectionCheckBox, true);
        end
        
        if isprop(app, 'shackhartmannzernikeranksEditField')
            HD.params.ShackHartmannCorrection.zernikeranks = safeGetUIValue(app.shackhartmannzernikeranksEditField, 2);
        end
        
        if isprop(app, 'subapnumpositionsEditField')
            HD.params.ShackHartmannCorrection.subapnumpositions = safeGetUIValue(app.subapnumpositionsEditField, 5);
        end
        
        if isprop(app, 'imagesubapsizeratioEditField')
            HD.params.ShackHartmannCorrection.imagesubapsizeratio = safeGetUIValue(app.imagesubapsizeratioEditField, 5);
        end
        
        if isprop(app, 'subaperturemarginEditField')
            HD.params.ShackHartmannCorrection.subaperturemargin = safeGetUIValue(app.subaperturemarginEditField, 0.15);
        end
        
        if isprop(app, 'referenceimageDropDown')
            HD.params.ShackHartmannCorrection.referenceimage = safeGetUIValue(app.referenceimageDropDown, 'central subaperture');
        end
        
        if isprop(app, 'CalibrationFactorEditField')
            HD.params.ShackHartmannCorrection.calibrationfactor = safeGetUIValue(app.CalibrationFactorEditField, 60);
        end
        
        if isprop(app, 'ConvergenceThreshold')
            HD.params.ShackHartmannCorrection.convergencethreshold = safeGetUIValue(app.ConvergenceThreshold, 0.5);
        end
        
        if isprop(app, 'onlydefocusCheckBox')
            HD.params.ShackHartmannCorrection.onlydefocus = safeGetCheckbox(app.onlydefocusCheckBox, false);
        end
    else
        HD.params.ShackHartmannCorrection = [];
    end
end

% Advanced processing parameters
if isprop(app, 'SVDxCheckBox')
    HD.params.svdx_enable = safeGetCheckbox(app.SVDxCheckBox, false);
end

if isprop(app, 'SVDx_SubApEditField')
    HD.params.svdx_subap = safeGetUIValue(app.SVDx_SubApEditField, 3);
end

if isprop(app, 'SVDThresholdCheckBox')
    HD.params.svd_threshold_enable = safeGetCheckbox(app.SVDThresholdCheckBox, false);
end

if isprop(app, 'SVDThresholdEditField')
    HD.params.svd_threshold_value = safeGetUIValue(app.SVDThresholdEditField, 64);
end

if isprop(app, 'SVDStrideEditField')
    HD.params.svd_stride = safeGetUIValue(app.SVDStrideEditField, 1);
end

% Local filtering parameters
if isprop(app, 'spatialCheckBox')
    HD.params.local_spatial_filter = safeGetCheckbox(app.spatialCheckBox, false);
end

if isprop(app, 'temporalCheckBox')
    HD.params.local_temporal_filter = safeGetCheckbox(app.temporalCheckBox, false);
end

if isprop(app, 'phi1EditField')
    HD.params.local_phi1 = safeGetUIValue(app.phi1EditField, 0);
end

if isprop(app, 'phi2EditField')
    HD.params.local_phi2 = safeGetUIValue(app.phi2EditField, 0);
end

if isprop(app, 'nu1EditField')
    HD.params.local_nu1 = safeGetUIValue(app.nu1EditField, 0);
end

if isprop(app, 'nu2EditField')
    HD.params.local_nu2 = safeGetUIValue(app.nu2EditField, 0);
end

if isprop(app, 'unitcellsinlatticeEditField')
    HD.params.unit_cells = safeGetUIValue(app.unitcellsinlatticeEditField, 8);
end

if isprop(app, 'r1EditField')
    HD.params.r1 = safeGetUIValue(app.r1EditField, 3);
end

if isprop(app, 'xystrideEditField')
    HD.params.xy_stride = safeGetUIValue(app.xystrideEditField, 32);
end

% Temporal filter - this was causing the error
if isprop(app, 'temporalfilterCheckBox')
    try
        % Check if the property exists and has a value
        if isprop(app.temporalfilterCheckBox, 'Value')
            val = app.temporalfilterCheckBox.Value;
            if ~isempty(val) && islogical(val)
                HD.params.temporal_filter = val;
            else
                HD.params.temporal_filter = false;
            end
        else
            HD.params.temporal_filter = false;
        end
    catch
        HD.params.temporal_filter = false;
    end
else
    HD.params.temporal_filter = false;
end

if isprop(app, 'temporalfilterEditField')
    try
        if isprop(app.temporalfilterEditField, 'Value')
            val = app.temporalfilterEditField.Value;
            if ~isempty(val)
                HD.params.temporal_filter_value = val;
            else
                HD.params.temporal_filter_value = 0;
            end
        else
            HD.params.temporal_filter_value = 0;
        end
    catch
        HD.params.temporal_filter_value = 0;
    end
end

% Phase registration
if isprop(app, 'phaseregistrationCheckBox')
    HD.params.phase_registration = safeGetCheckbox(app.phaseregistrationCheckBox, false);
end

if isprop(app, 'rephasingCheckBox')
    HD.params.rephasing = safeGetCheckbox(app.rephasingCheckBox, false);
end

if isprop(app, 'iterativeregistrationCheckBox')
    HD.params.iterative_registration = safeGetCheckbox(app.iterativeregistrationCheckBox, false);
end

if isprop(app, 'showrefCheckBox')
    HD.params.show_ref = safeGetCheckbox(app.showrefCheckBox, false);
end

end