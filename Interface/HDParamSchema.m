classdef HDParamSchema
% HDParamSchema  Single source of truth for HD <-> GUI parameter mappings.
%
%   defaults = HDParamSchema.getDefaults();       % struct of param -> default
%   fullSchema = HDParamSchema.getFullSchema();   % full schema array
%
%   HDParamSchema.classtogui(HD, app);            % push HD.params -> GUI
%   HDParamSchema.guitoclass(HD, app);            % push GUI -> HD.params

properties (Constant, Access = private)
    Schema = HDParamSchema.buildSchema() % built once, shared forever
end

methods (Static)

    function defaults = getDefaults()
        % Returns a struct with all param names and their default values.
        defaults = struct();

        for k = 1:numel(HDParamSchema.Schema)
            defaults.(HDParamSchema.Schema(k).param) = HDParamSchema.Schema(k).default;
        end

    end

    function s = getFullSchema()
        % Returns the complete schema array.
        s = HDParamSchema.Schema;
    end

    function classtogui(HD, app)
        % Push HD.params -> app UI.
        if isempty(HD) || isempty(HD.params)
            return
        end

        schema = HDParamSchema.Schema;

        for k = 1:numel(schema)
            e = schema(k);

            if ~HDParamSchema.widgetExists(app, e.widget)
                continue
            end

            value = HDParamSchema.getParam(HD.params, e.param, e.default);

            switch e.type
                case 'numeric'
                    HDParamSchema.setNumeric(app.(e.widget), value);
                case 'checkbox'
                    HDParamSchema.setCheckbox(app.(e.widget), value);
                case 'dropdown'
                    HDParamSchema.setDropdown(app.(e.widget), value);
                case 'range2'

                    if numel(value) >= 2
                        HDParamSchema.setNumeric(app.(e.widget{1}), value(1));
                        HDParamSchema.setNumeric(app.(e.widget{2}), value(2));
                    end

                case 'listbox'
                    HDParamSchema.setListbox(app.(e.widget), value);
            end

        end

        % Special handling for image dimensions from HD.file
        if ~isempty(HD.file)
            HDParamSchema.setNumeric(app.Nx, double(HD.file.Nx));
            HDParamSchema.setNumeric(app.Ny, double(HD.file.Ny));

            if isfield(HD.file, 'num_frames')

                try
                    app.positioninfileSlider.Limits = double([1 HD.file.num_frames - HD.params.batchSize + 1]);
                    HDParamSchema.setNumeric(app.positioninfileSlider, double(HD.params.framePosition));
                catch
                end

            end

        end

    end

    function guitoclass(HD, app)
        % Push app UI -> HD.params.
        if isempty(HD)
            return
        end

        schema = HDParamSchema.Schema;

        for k = 1:numel(schema)
            e = schema(k);

            if ~HDParamSchema.widgetExists(app, e.widget)
                continue
            end

            switch e.type
                case 'numeric'
                    HD.params.(e.param) = HDParamSchema.getNumeric(app.(e.widget), e.default);
                case 'checkbox'
                    HD.params.(e.param) = HDParamSchema.getCheckbox(app.(e.widget), e.default);
                case 'dropdown'
                    HD.params.(e.param) = HDParamSchema.getDropdown(app.(e.widget), e.default);
                case 'listbox'
                    HD.params.(e.param) = HDParamSchema.getListbox(app.(e.widget), e.default);
            end

        end

        if isprop(app, 'positioninfileSlider')
            HD.params.framePosition = round(app.positioninfileSlider.Value);
        end

    end

end

methods (Static, Access = private)

    function s = buildSchema()
        % Build the schema array – called once when the class is loaded.
        s = struct('param', {}, 'widget', {}, 'type', {}, 'default', {});

        % ---- acquisition / hardware ----

        s(end + 1) = HDParamSchema.entry('fs', 'fs', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('lambda', 'lambda', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('ppx', 'ppx', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('ppy', 'ppy', 'numeric', 0);

        % ---- parallel processing ----

        s(end + 1) = HDParamSchema.entry('parforArg', 'parforArg', 'numeric', 10);

        % ---- batch ----

        s(end + 1) = HDParamSchema.entry('batchSize', 'batchSize', 'numeric', 512);
        s(end + 1) = HDParamSchema.entry('batchStride', 'batchStride', 'numeric', 512);
        s(end + 1) = HDParamSchema.entry('refBatchSize', 'refBatchSize', 'numeric', 512);
        s(end + 1) = HDParamSchema.entry('framePosition', 'framePosition', 'numeric', 1);
        s(end + 1) = HDParamSchema.entry('first_frame', '', 'numeric', 1);
        s(end + 1) = HDParamSchema.entry('end_frame', '', 'numeric', Inf);

        % ---- image types ----

        s(end + 1) = HDParamSchema.entry('imageTypes', 'imageTypesListBox', 'listbox', ...
            {{'power_Doppler', 'moment_0', 'moment_1', 'moment_2'}});

        % ---- registration ----

        s(end + 1) = HDParamSchema.entry('imageRegistration', 'imageRegistration', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('registrationDiskRatio', 'registrationDiskRatio', 'numeric', 0.8);
        s(end + 1) = HDParamSchema.entry('applyautofocusfromref', 'AutofocusFromRef', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('autofocusRange1', 'autofocusRange1', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('autofocusRange2', 'autofocusRange2', 'numeric', 1);

        % ---- spatial ----

        s(end + 1) = HDParamSchema.entry('spatialFilter', 'spatialFilter', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('spatialFilterRange1', 'spatialFilterRange1', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('spatialFilterRange2', 'spatialFilterRange2', 'numeric', 1);
        s(end + 1) = HDParamSchema.entry('spatialTransformation', 'spatialTransformation', 'dropdown', 'Fresnel');
        s(end + 1) = HDParamSchema.entry('spatialPropagation', 'spatialPropagation', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('PaddingNum', 'PaddingNum', 'numeric', 0);

        % ---- SVD ----

        s(end + 1) = HDParamSchema.entry('svd_filter', 'svd_filter', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('svdThreshold', 'svdThreshold', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('svdStride', 'svdStride', 'numeric', 1);

        % ---- time transform ----

        s(end + 1) = HDParamSchema.entry('timeTransform', 'timeTransform', 'dropdown', 'FFT');
        s(end + 1) = HDParamSchema.entry('frequencyRange1', 'frequencyRange1', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('frequencyRange2', 'frequencyRange2', 'numeric', 100);
        s(end + 1) = HDParamSchema.entry('indexRange1', 'indexRange1', 'numeric', 1);
        s(end + 1) = HDParamSchema.entry('indexRange2', 'indexRange2', 'numeric', 100);

        % ---- color Doppler threshold (AdvancedPanel) ----------------------
        s(end + 1) = HDParamSchema.entry('frequencyRange_extra', '', 'numeric', -1);
        s(end + 1) = HDParamSchema.entry('frequencyRangeInter1', 'frequencyRangeInter1', 'numeric', 7);
        s(end + 1) = HDParamSchema.entry('frequencyRangeInter2', 'frequencyRangeInter2', 'numeric', 7);

        % ---- post-processing ----

        s(end + 1) = HDParamSchema.entry('flatfield_gw', 'flat_field_gw', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('flip_y', 'flip_y', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('flip_x', 'flip_x', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('square', 'square', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('ImproveContrast', 'ImproveContrast', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('CornerCompensation', 'CornerCompensation', 'checkbox', false);

        % ---- advanced ----

        s(end + 1) = HDParamSchema.entry('phase_registration', 'phaseregistrationCheckBox', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('rephasing', 'rephasingCheckBox', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('iterative_registration', 'iterativeregistrationCheckBox', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('show_ref', 'showrefCheckBox', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('bucketsRanges', '', 'numeric', []);
        s(end + 1) = HDParamSchema.entry('buckets_raw', 'bucketsraw', 'checkbox', false);

    end

    function e = entry(param, widget, type, default)
        e = struct('param', param, 'widget', widget, 'type', type, 'default', default);
    end

    % ---------- Widget helpers (unchanged) ----------
    function tf = widgetExists(app, widget)

        if isempty(widget) || (iscell(widget) && any(cellfun(@isempty, widget)))
            tf = false;
            return
        end

        if iscell(widget)
            tf = all(cellfun(@(w) isprop(app, w), widget));
        else
            tf = isprop(app, widget);
        end

    end

    function value = getParam(params, name, default)

        if isfield(params, name) && ~isempty(params.(name))
            value = params.(name);
        else
            value = default;
        end

    end

    function setNumeric(field, value)
        if isempty(value) || ~isnumeric(value), value = 0; end

        try
            field.Value = double(value(1));
        catch ME
            warning('HDParamSchema:setNumeric', 'Could not set numeric field: %s', ME.message);
        end

    end

    function setCheckbox(field, value)
        if isempty(value), value = false; end

        try
            field.Value = logical(value);
        catch ME
            warning('HDParamSchema:setCheckbox', 'Could not set checkbox: %s', ME.message);
        end

    end

    function setDropdown(field, value)
        if isempty(value), value = field.Items{1}; end

        try

            if ismember(value, field.Items)
                field.Value = value;
            else
                warning('HDParamSchema:setDropdown', ...
                    'Value "%s" not in dropdown items — keeping current.', value);
            end

        catch ME
            warning('HDParamSchema:setDropdown', 'Could not set dropdown: %s', ME.message);
        end

    end

    function setListbox(field, value)

        try
            allTypes = properties(ImageTypeList);
        catch
            allTypes = {'power_Doppler', 'color_Doppler', 'directional_Doppler', ...
                            'moment_0', 'moment_1', 'moment_2', 'FH_modulus_mean'};
        end

        field.Items = allTypes;

        if ~isempty(value)
            field.Value = intersect(value, allTypes, 'stable');
        else
            field.Value = {};
        end

    end

    function val = getNumeric(field, default)

        try
            val = double(field.Value);
            if isempty(val) || ~isfinite(val), val = default; end
        catch
            val = default;
        end

    end

    function val = getCheckbox(field, default)

        try
            val = logical(field.Value);
        catch
            val = default;
        end

    end

    function val = getDropdown(field, default)

        try
            val = field.Value;
            if isempty(val), val = default; end
        catch
            val = default;
        end

    end

    function val = getListbox(field, default)

        try
            val = field.Value;
            if isempty(val), val = default; end
        catch
            val = default;
        end

    end

end

end
