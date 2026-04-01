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
    HD.params.framePosition = round(safeGetUIValue(app.positioninfileSlider, 1));
end

% Registration parameters
if isprop(app, 'registrationDiskRatio')
    HD.params.registrationDiskRatio = safeGetUIValue(app.registrationDiskRatio, 0.8);
end

% Handle image types as a cell array
if isprop(app, 'Image_typesListBox') && isprop(app.Image_typesListBox, 'Value')
    value = app.Image_typesListBox.Value;

    if ~isempty(value)
        HD.params.image_types = value;
    end

end

% Image registration
if isprop(app, 'imageRegistration')
    HD.params.imageRegistration = safeGetCheckbox(app.imageRegistration, false);
end

% Spatial filtering parameters
if isprop(app, 'spatialFilter')
    HD.params.spatialFilter = safeGetCheckbox(app.spatialFilter, false);
end

if isprop(app, 'spatialFilterRange1') && isprop(app, 'spatialFilterRange2')
    val1 = safeGetUIValue(app.spatialFilterRange1, 0);
    val2 = safeGetUIValue(app.spatialFilterRange2, 1);
    HD.params.spatialFilterRange = [val1, val2];
end

if isprop(app, 'spatialTransformation')
    HD.params.spatialTransformation = safeGetUIValue(app.spatialTransformation, 'Fresnel');
end

if isprop(app, 'spatialPropagation')
    HD.params.spatialPropagation = safeGetUIValue(app.spatialPropagation, 0);
end

if isprop(app, 'PaddingNum')
    HD.params.PaddingNum = safeGetUIValue(app.PaddingNum, 0);
end

% SVD parameters
if isprop(app, 'svd_filter')
    HD.params.svd_filter = safeGetCheckbox(app.svd_filter, false);
end

if isprop(app, 'svdThreshold')
    HD.params.svdThreshold = safeGetUIValue(app.svdThreshold, 0);
end

% Time transformation parameters
if isprop(app, 'timeTransform')
    HD.params.timeTransform = safeGetUIValue(app.timeTransform, 'FFT');
end

if isprop(app, 'frequencyRange1') && isprop(app, 'frequencyRange2')
    val1 = safeGetUIValue(app.frequencyRange1, 0);
    val2 = safeGetUIValue(app.frequencyRange2, 100);
    HD.params.frequencyRange = [val1, val2];
end

if isprop(app, 'frequencyRangeInter1') && isprop(app, 'frequencyRangeInter2')
    val1 = safeGetUIValue(app.frequencyRangeInter1, 0);
    val2 = safeGetUIValue(app.frequencyRangeInter2, 100);
    HD.params.frequencyRangeInter = [val1, val2];
end

if isprop(app, 'indexRange1') && isprop(app, 'indexRange2')
    val1 = safeGetUIValue(app.indexRange1, 1);
    val2 = safeGetUIValue(app.indexRange2, 100);
    HD.params.indexRange = [val1, val2];
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

if isprop(app, 'applyShackHartmannfromRef')
    HD.params.applyShackHartmannfromRef = safeGetCheckbox(app.applyShackHartmannfromRef, false);
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

        if isprop(app, 'NumberOfIteration')
            HD.params.ShackHartmannCorrection.N_iterate = safeGetUIValue(app.NumberOfIteration, 3);
        end

        if isprop(app, 'ZernikeProjectionCheckBox')
            HD.params.ShackHartmannCorrection.ZernikeProjection = safeGetCheckbox(app.ZernikeProjectionCheckBox, true);
        end

        if isprop(app, 'shackHartmannZernikeRanks')
            HD.params.ShackHartmannCorrection.zernikeranks = safeGetUIValue(app.shackHartmannZernikeRanks, 2);
        end

        if isprop(app, 'SubApNumPositions')
            HD.params.ShackHartmannCorrection.subapnumpositions = safeGetUIValue(app.SubApNumPositions, 5);
        end

        if isprop(app, 'imageSubApSizeRatio')
            HD.params.ShackHartmannCorrection.imagesubapsizeratio = safeGetUIValue(app.imageSubApSizeRatio, 5);
        end

        if isprop(app, 'subApMargin')
            HD.params.ShackHartmannCorrection.subaperturemargin = safeGetUIValue(app.subApMargin, 0.15);
        end

        if isprop(app, 'referenceimageDropDown')
            HD.params.ShackHartmannCorrection.referenceimage = safeGetUIValue(app.referenceimageDropDown, 'central subaperture');
        end

        if isprop(app, 'CalibrationFactor')
            HD.params.ShackHartmannCorrection.calibrationfactor = safeGetUIValue(app.CalibrationFactor, 60);
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

if isprop(app, 'SVDThresholdCheckBox')
    HD.params.svdThreshold_enable = safeGetCheckbox(app.SVDThresholdCheckBox, false);
end

if isprop(app, 'SVDThreshold')
    HD.params.svdThreshold_value = safeGetUIValue(app.SVDThreshold, 64);
end

if isprop(app, 'svdStride')
    HD.params.svdStride = safeGetUIValue(app.svdStride, 1);
end

% Local filtering parameters
if isprop(app, 'spatialCheckBox')
    HD.params.local_spatialFilter = safeGetCheckbox(app.spatialCheckBox, false);
end

if isprop(app, 'temporalCheckBox')
    HD.params.local_temporalFilter = safeGetCheckbox(app.temporalCheckBox, false);
end

if isprop(app, 'phi1')
    HD.params.local_phi1 = safeGetUIValue(app.phi1, 0);
end

if isprop(app, 'phi1')
    HD.params.local_phi2 = safeGetUIValue(app.phi1, 0);
end

if isprop(app, 'nu1')
    HD.params.local_nu1 = safeGetUIValue(app.nu1, 0);
end

if isprop(app, 'nu2')
    HD.params.local_nu2 = safeGetUIValue(app.nu2, 0);
end

if isprop(app, 'unitCellsinLattice')
    HD.params.unit_cells = safeGetUIValue(app.unitCellsinLattice, 8);
end

if isprop(app, 'r1')
    HD.params.r1 = safeGetUIValue(app.r1, 3);
end

if isprop(app, 'xyStride')
    HD.params.xy_stride = safeGetUIValue(app.xyStride, 32);
end

% Temporal filter - this was causing the error
if isprop(app, 'temporalfilterCheckBox')

    try
        % Check if the property exists and has a value
        if isprop(app.temporalfilterCheckBox, 'Value')
            val = app.temporalfilterCheckBox.Value;

            if ~isempty(val) && islogical(val)
                HD.params.temporalFilter = val;
            else
                HD.params.temporalFilter = false;
            end

        else
            HD.params.temporalFilter = false;
        end

    catch
        HD.params.temporalFilter = false;
    end

else
    HD.params.temporalFilter = false;
end

if isprop(app, 'temporalFilter')

    try

        if isprop(app.temporalFilter, 'Value')
            val = app.temporalFilter.Value;

            if ~isempty(val)
                HD.params.temporalFilter_value = val;
            else
                HD.params.temporalFilter_value = 0;
            end

        else
            HD.params.temporalFilter_value = 0;
        end

    catch
        HD.params.temporalFilter_value = 0;
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
