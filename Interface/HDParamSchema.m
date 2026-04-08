function schema = HDParamSchema()
% HDParamSchema  Single source of truth for all HD <-> GUI parameter mappings.
%
% Returns a struct array where each entry describes one parameter:
%
%   .param      - field name in HD.params
%   .widget     - property name on the app object  ('' = no widget)
%   .type       - 'numeric' | 'checkbox' | 'dropdown' | 'range2' | 'listbox'
%   .default    - value used when the source is empty or missing
%
% Adding a new parameter means adding one row here — nothing else changes.

s = struct( ...
    'param', {}, ...
    'widget', {}, ...
    'type', {}, ...
    'default', {} ...
);

% ---- acquisition / hardware -------------------------------------------
s(end + 1) = entry('fs', 'fs', 'numeric', 0);
s(end + 1) = entry('lambda', 'lambda', 'numeric', 0);
s(end + 1) = entry('ppx', 'ppx', 'numeric', 0);
s(end + 1) = entry('ppy', 'ppy', 'numeric', 0);

% ---- parallel processing -----------------------------------------------
s(end + 1) = entry('parforArg', 'parforArg', 'numeric', 10);

% ---- batch -----------------------------------------------------------------
s(end + 1) = entry('batchSize', 'batchSize', 'numeric', 512);
s(end + 1) = entry('batchStride', 'batchStride', 'numeric', 512);
s(end + 1) = entry('refBatchSize', 'refBatchSize', 'numeric', 512);
s(end + 1) = entry('framePosition', 'framePosition', 'numeric', 1);

% ---- image types -----------------------------------------------------------
s(end + 1) = entry('imageTypes', 'imageTypesListBox', 'listbox', ...
    {{'power_Doppler', 'color_Doppler', 'directional_Doppler', ...
      'moment_0', 'moment_1', 'moment_2', 'FH_modulus_mean'}});

% ---- registration ----------------------------------------------------------
s(end + 1) = entry('imageRegistration', 'imageRegistration', 'checkbox', false);
s(end + 1) = entry('registrationDiskRatio', 'registrationDiskRatio', 'numeric', 0.8);
s(end + 1) = entry('applyautofocusfromref', 'AutofocusFromRef', 'checkbox', false);

% ---- spatial ---------------------------------------------------------------
s(end + 1) = entry('spatialFilter', 'spatialFilter', 'checkbox', false);
s(end + 1) = entry('spatialFilterRange1', 'spatialFilterRange1', 'numeric', 0);
s(end + 1) = entry('spatialFilterRange2', 'spatialFilterRange2', 'numeric', 1);
s(end + 1) = entry('spatialTransformation', 'spatialTransformation', 'dropdown', 'Fresnel');
s(end + 1) = entry('spatialPropagation', 'spatialPropagation', 'numeric', 0);
s(end + 1) = entry('PaddingNum', 'PaddingNum', 'numeric', 0);

% ---- SVD -------------------------------------------------------------------
s(end + 1) = entry('svd_filter', 'svd_filter', 'checkbox', false);
s(end + 1) = entry('svdThreshold', 'svdThreshold', 'numeric', 0);
s(end + 1) = entry('svdStride', 'svdStride', 'numeric', 1);

% ---- time transform --------------------------------------------------------
s(end + 1) = entry('timeTransform', 'timeTransform', 'dropdown', 'FFT');
s(end + 1) = entry('frequencyRange1', 'frequencyRange1', 'numeric', 0);
s(end + 1) = entry('frequencyRange2', 'frequencyRange2', 'numeric', 100);
s(end + 1) = entry('frequencyRangeInter1', 'frequencyRangeInter1', 'numeric', 7);
s(end + 1) = entry('frequencyRangeInter2', 'frequencyRangeInter2', 'numeric', 7);
s(end + 1) = entry('indexRange1', 'indexRange1', 'numeric', 1);
s(end + 1) = entry('indexRange2', 'indexRange2', 'numeric', 100);

% ---- image post-processing -------------------------------------------------
s(end + 1) = entry('flatfield_gw', 'flat_field_gw', 'numeric', 0);
s(end + 1) = entry('flip_y', 'flip_y', 'checkbox', false);
s(end + 1) = entry('flip_x', 'flip_x', 'checkbox', false);
s(end + 1) = entry('square', 'square', 'checkbox', false);
s(end + 1) = entry('ImproveContrast', 'ImproveContrast', 'checkbox', false);
s(end + 1) = entry('CornerCompensation', 'CornerCompensation', 'checkbox', false);

% ---- advanced (AdvancedPanel app) ------------------------------------------
s(end + 1) = entry('phase_registration', 'phaseregistrationCheckBox', 'checkbox', false);
s(end + 1) = entry('rephasing', 'rephasingCheckBox', 'checkbox', false);
s(end + 1) = entry('iterative_registration', 'iterativeregistrationCheckBox', 'checkbox', false);
s(end + 1) = entry('show_ref', 'showrefCheckBox', 'checkbox', false);

schema = s;
end

% ---------------------------------------------------------------------------
function e = entry(param, widget, type, default)
% Wrap a single row as a scalar struct so the array stays consistent.
e = struct('param', param, 'widget', widget, 'type', type, 'default', default);
end
