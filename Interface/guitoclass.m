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
if isprop(app, 'imageTypesListBox') && isprop(app.imageTypesListBox, 'Value')
    value = app.imageTypesListBox.Value;

    if ~isempty(value)
        HD.params.imageTypes = value;
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

% Advanced processing parameters

if isprop(app, 'svdStride')
    HD.params.svdStride = safeGetUIValue(app.svdStride, 1);
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
