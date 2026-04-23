classdef HDParamSchema
% HDParamSchema  Single source of truth for HD <-> GUI parameter mappings.
%                All GUI access goes through app.getWidgetValue / app.setWidgetValue.

methods (Static)

    function defaults = getDefaults()
        defaults = struct();
        schema = HDParamSchema.getFullSchema();

        for k = 1:numel(schema)
            defaults.(schema(k).param) = schema(k).default;
        end

    end

    function s = getFullSchema()
        % Return the full schema array. Built once and cached in persistent.
        persistent schemaCache

        if isempty(schemaCache)
            schemaCache = HDParamSchema.buildSchema();
        end

        s = schemaCache;
    end

    function classtogui(HD, app)
        % Push HD.params -> app UI
        if isempty(HD) || isempty(HD.params)
            return
        end

        schema = HDParamSchema.getFullSchema();

        for k = 1:numel(schema)
            e = schema(k);

            if isempty(e.widget)
                continue
            end

            if ~isprop(app, e.widget)
                continue
            end

            value = HDParamSchema.getParam(HD.params, e.param, e.default);
            app.setWidgetValue(e.widget, value);
        end

        % ---- Special handling for file‑dependent info ----
        if ~isempty(HD.file)
            app.setWidgetValue('Nx', double(HD.file.Nx));
            app.setWidgetValue('Ny', double(HD.file.Ny));

            if isfield(HD.file, 'num_frames')

                try
                    app.positioninfileSlider.Limits = ...
                        double([1 HD.file.num_frames - HD.params.batchSize + 1]);
                    app.setWidgetValue('positioninfileSlider', double(HD.params.framePosition));
                catch
                end

            end

        end

    end

    function guitoclass(HD, app)
        % Push app UI -> HD.params
        if isempty(HD)
            return
        end

        schema = HDParamSchema.getFullSchema();

        for k = 1:numel(schema)
            e = schema(k);

            if isempty(e.widget)
                continue
            end

            if ~isprop(app, e.widget)
                continue
            end

            value = app.getWidgetValue(e.widget);

            if isempty(value) || (isnumeric(value) && ~isfinite(value))
                value = e.default;
            end

            HD.params.(e.param) = value;
        end

        if isprop(app, 'positioninfileSlider')
            HD.params.framePosition = round(app.getWidgetValue('positioninfileSlider'));
        end

    end

end

methods (Static, Access = private)

    function s = buildSchema()
        s = struct('param', {}, 'widget', {}, 'type', {}, 'default', {});
        % acquisition / hardware
        s(end + 1) = HDParamSchema.entry('fs', 'fs', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('lambda', 'lambda', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('ppx', 'ppx', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('ppy', 'ppy', 'numeric', 0);
        % parallel
        s(end + 1) = HDParamSchema.entry('parforArg', 'parforArg', 'numeric', 10);
        % batch
        s(end + 1) = HDParamSchema.entry('batchSize', 'batchSize', 'numeric', 512);
        s(end + 1) = HDParamSchema.entry('batchStride', 'batchStride', 'numeric', 512);
        s(end + 1) = HDParamSchema.entry('refBatchSize', 'refBatchSize', 'numeric', 512);
        s(end + 1) = HDParamSchema.entry('framePosition', 'framePosition', 'numeric', 1);
        s(end + 1) = HDParamSchema.entry('first_frame', '', 'numeric', 1);
        s(end + 1) = HDParamSchema.entry('end_frame', '', 'numeric', Inf);
        % image types
        s(end + 1) = HDParamSchema.entry('imageTypes', 'imageTypesListBox', 'listbox', {{'power_Doppler', 'moment_0', 'moment_1', 'moment_2'}});
        % registration
        s(end + 1) = HDParamSchema.entry('imageRegistration', 'imageRegistration', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('registrationDiskRatio', 'registrationDiskRatio', 'numeric', 0.8);
        s(end + 1) = HDParamSchema.entry('applyautofocusfromref', 'AutofocusFromRef', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('autofocusRange1', 'autofocusRange1', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('autofocusRange2', 'autofocusRange2', 'numeric', 1);
        % spatial
        s(end + 1) = HDParamSchema.entry('spatialFilter', 'spatialFilter', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('spatialFilterRange1', 'spatialFilterRange1', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('spatialFilterRange2', 'spatialFilterRange2', 'numeric', 1);
        s(end + 1) = HDParamSchema.entry('spatialTransform', 'spatialTransform', 'dropdown', 'Fresnel');
        s(end + 1) = HDParamSchema.entry('spatialPropagation', 'spatialPropagation', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('PaddingNum', 'PaddingNum', 'numeric', 0);
        % SVD
        s(end + 1) = HDParamSchema.entry('svd_filter', 'svd_filter', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('svdThreshold', 'svdThreshold', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('svdStride', 'svdStride', 'numeric', 1);
        % time transform
        s(end + 1) = HDParamSchema.entry('timeTransform', 'timeTransform', 'dropdown', 'FFT');
        s(end + 1) = HDParamSchema.entry('frequencyRange1', 'frequencyRange1', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('frequencyRange2', 'frequencyRange2', 'numeric', 100);
        s(end + 1) = HDParamSchema.entry('indexRange1', 'indexRange1', 'numeric', 1);
        s(end + 1) = HDParamSchema.entry('indexRange2', 'indexRange2', 'numeric', 100);
        % extra
        s(end + 1) = HDParamSchema.entry('frequencyRange_extra', '', 'numeric', -1);
        s(end + 1) = HDParamSchema.entry('frequencyRangeInter1', 'frequencyRangeInter1', 'numeric', 7);
        s(end + 1) = HDParamSchema.entry('frequencyRangeInter2', 'frequencyRangeInter2', 'numeric', 7);
        % post‑processing
        s(end + 1) = HDParamSchema.entry('flatfield_gw', 'flat_field_gw', 'numeric', 0);
        s(end + 1) = HDParamSchema.entry('flip_y', 'flip_y', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('flip_x', 'flip_x', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('square', 'square', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('ImproveContrast', 'ImproveContrast', 'checkbox', false);
        s(end + 1) = HDParamSchema.entry('CornerCompensation', 'CornerCompensation', 'checkbox', false);
        % advanced
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

    function value = getParam(params, name, default)

        if isfield(params, name) && ~isempty(params.(name))
            value = params.(name);
        else
            value = default;
        end

    end

end

end
