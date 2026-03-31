function classtogui(HD, app)
% handles all command transfer from HD to app

% Helper function to safely set numeric edit field values
function safeSetNumeric(uiField, value)

    try

        if isprop(uiField, 'Value') && ~isempty(uiField)

            if isempty(value)
                value = 0; % Default value for empty
            end

            uiField.Value = value;
        end

    catch ME
        % Silently fail - don't crash the GUI
        % fprintf('Warning: Could not set value for %s\n', inputname(1));
    end

end

% Helper function to safely set checkbox values
function safeSetCheckbox(uiCheckbox, value)

    try

        if isprop(uiCheckbox, 'Value') && ~isempty(uiCheckbox)

            if isempty(value)
                value = false;
            end

            uiCheckbox.Value = logical(value);
        end

    catch
        % Silently fail
    end

end

% Helper function to safely set dropdown values
function safeSetDropdown(uiDropdown, value, items)

    try

        if isprop(uiDropdown, 'Value') && ~isempty(uiDropdown)

            if isempty(value)

                if nargin >= 3 && ~isempty(items)
                    value = items{1};
                else
                    value = '';
                end

            end

            % Check if value is in the items list
            if isprop(uiDropdown, 'Items') && ~isempty(uiDropdown.Items)

                if ~ismember(value, uiDropdown.Items)
                    value = uiDropdown.Items{1};
                end

            end

            uiDropdown.Value = value;
        end

    catch
        % Silently fail
    end

end

% Basic parameters
if ~isempty(HD) && ~isempty(HD.params)
    safeSetNumeric(app.fs, HD.params.fs);
    safeSetNumeric(app.lambda, HD.params.lambda);
    safeSetNumeric(app.ppx, HD.params.ppx);
    safeSetNumeric(app.ppy, HD.params.ppy);

    % Image dimensions (if file is loaded)
    if ~isempty(HD.file)
        safeSetNumeric(app.Nx, double(HD.file.Nx));
        safeSetNumeric(app.Ny, double(HD.file.Ny));

        % Update slider limits and value
        if isfield(HD.file, 'num_frames')

            try
                app.positioninfileSlider.Limits = double([0 HD.file.num_frames]);
                safeSetNumeric(app.positioninfileSlider, double(HD.params.frame_position));
            catch
                % Silently fail
            end

        end

        % Update frame position numeric field if it exists
        if isprop(app, 'framePosition')
            safeSetNumeric(app.framePosition, double(HD.params.frame_position));
        end

    end

    % Parallel processing
    safeSetNumeric(app.parfor_arg, HD.params.parfor_arg);

    % Batch parameters
    safeSetNumeric(app.batchSize, HD.params.batchSize);
    safeSetNumeric(app.refBatchSize, HD.params.refBatchSize);
    safeSetNumeric(app.batchStride, HD.params.batchStride);

    % Registration parameters
    if isprop(app, 'registration_disc_ratio')
        safeSetNumeric(app.registration_disc_ratio, HD.params.registration_disc_ratio);
    end

    if isprop(app, 'image_registration')
        safeSetCheckbox(app.image_registration, HD.params.image_registration);
    end

    % Image types list
    if isprop(app.Image_typesListBox, 'Items')
        % Get available image types from ImageTypeList2
        try
            imageTypes = properties(ImageTypeList2);
            app.Image_typesListBox.Items = imageTypes;
        catch
            % If ImageTypeList2 is not available, use default list
            app.Image_typesListBox.Items = {'power_Doppler', 'color_Doppler', 'directional_Doppler', ...
                'moment_0', 'moment_1', 'moment_2', 'FH_modulus_mean'};
        end

        if ~isempty(HD.params.image_types)
            % Get current items in the list box
            currentItems = app.Image_typesListBox.Items;

            % Find which items exist in both
            validItems = intersect(HD.params.image_types, currentItems);

            % Set value only if there are valid items
            if ~isempty(validItems)
                app.Image_typesListBox.Value = validItems;
            else
                % Optional: clear selection or set to empty
                app.Image_typesListBox.Value = {};
            end
        end

    end

    % Spatial filtering
    if isprop(app, 'spatialFilter')
        safeSetCheckbox(app.spatialFilter, HD.params.spatialFilter);
    end

    if isprop(app, 'spatialFilterRange1') && isprop(app, 'spatialFilterRange2')

        if length(HD.params.spatialFilterRange) >= 2
            safeSetNumeric(app.spatialFilterRange1, HD.params.spatialFilterRange(1));
            safeSetNumeric(app.spatialFilterRange2, HD.params.spatialFilterRange(2));
        end

    end

    % Spatial transformation
    if isprop(app, 'spatial_transformation')
        items = ["Fresnel", "angular spectrum", "twin image removal", "None"];
        app.spatial_transformation.Items = items;
        safeSetDropdown(app.spatial_transformation, HD.params.spatial_transformation, items);
    end

    if isprop(app, 'spatial_propagation')
        safeSetNumeric(app.spatial_propagation, HD.params.spatial_propagation);
    end

    if isprop(app, 'Padding_num')
        safeSetNumeric(app.Padding_num, HD.params.Padding_num);
    end

    % SVD filters
    if isprop(app, 'svd_filter')
        safeSetCheckbox(app.svd_filter, HD.params.svd_filter);
    end

    % SVD thresholds
    if isprop(app, 'svdThreshold')
        safeSetNumeric(app.svdThreshold, HD.params.svdThreshold);
    end

    % Time transformation
    if isprop(app, 'time_transform')
        items = ["FFT", "PCA", "ICA", "Wavelet_Morlet", "autocorrelation", "intercorrelation", "phase difference", "None"];
        app.time_transform.Items = items;
        safeSetDropdown(app.time_transform, HD.params.time_transform, items);
    end

    if isprop(app, 'frequencyRange1') && isprop(app, 'frequencyRange2')

        if length(HD.params.frequencyRange) >= 2
            safeSetNumeric(app.frequencyRange1, HD.params.frequencyRange(1));
            safeSetNumeric(app.frequencyRange2, HD.params.frequencyRange(2));
        end

    end

    if isprop(app, 'frequencyRangeInter1') && isprop(app, 'frequencyRangeInter2')

        if length(HD.params.frequencyRangeInter) >= 2
            safeSetNumeric(app.frequencyRangeInter1, HD.params.frequencyRangeInter(1));
            safeSetNumeric(app.frequencyRangeInter2, HD.params.frequencyRangeInter(2));
        end

    end

    if isprop(app, 'indexRange1') && isprop(app, 'indexRange2')

        if length(HD.params.indexRange) >= 2
            safeSetNumeric(app.indexRange1, HD.params.indexRange(1));
            safeSetNumeric(app.indexRange2, HD.params.indexRange(2));
        end

    end

    % Flat field correction
    if isprop(app, 'flat_field_gw')
        safeSetNumeric(app.flat_field_gw, HD.params.flatfield_gw);
    end

    % Image transformations
    if isprop(app, 'flip_y')
        safeSetCheckbox(app.flip_y, HD.params.flip_y);
    end

    if isprop(app, 'flip_x')
        safeSetCheckbox(app.flip_x, HD.params.flip_x);
    end

    if isprop(app, 'square')
        safeSetCheckbox(app.square, HD.params.square);
    end

    % Registration options
    if isprop(app, 'AutofocusFromRef')
        safeSetCheckbox(app.AutofocusFromRef, HD.params.applyautofocusfromref);
    end

    if isprop(app, 'applyshackhartmannfromref')
        safeSetCheckbox(app.applyshackhartmannfromref, HD.params.applyshackhartmannfromref);
    end

    % Shack-Hartmann correction
    if isprop(app, 'ShackHartmannCheckBox')
        safeSetCheckbox(app.ShackHartmannCheckBox, ~isempty(HD.params.ShackHartmannCorrection));
    end

    if ~isempty(HD.params.ShackHartmannCorrection)

        if isprop(app, 'IterativeCheckBox')
            safeSetCheckbox(app.IterativeCheckBox, HD.params.ShackHartmannCorrection.iterate);
        end

        if isprop(app, 'NumberOfIteration')
            safeSetNumeric(app.NumberOfIteration, HD.params.ShackHartmannCorrection.N_iterate);
        end

        if isprop(app, 'ZernikeProjectionCheckBox')
            safeSetCheckbox(app.ZernikeProjectionCheckBox, HD.params.ShackHartmannCorrection.ZernikeProjection);
        end

        if isprop(app, 'shackHartmannZernikeRanks')
            safeSetNumeric(app.shackHartmannZernikeRanks, HD.params.ShackHartmannCorrection.zernikeranks);
        end

        if isprop(app, 'SubApNumPositions')
            safeSetNumeric(app.SubApNumPositions, HD.params.ShackHartmannCorrection.subapnumpositions);
        end

        if isprop(app, 'imageSubApSizeRatio')
            safeSetNumeric(app.imageSubApSizeRatio, HD.params.ShackHartmannCorrection.imagesubapsizeratio);
        end

        if isprop(app, 'subApMargin')
            safeSetNumeric(app.subApMargin, HD.params.ShackHartmannCorrection.subaperturemargin);
        end

        if isprop(app, 'referenceimageDropDown')
            items = {'central subaperture', 'resized image'};
            safeSetDropdown(app.referenceimageDropDown, HD.params.ShackHartmannCorrection.referenceimage, items);
        end

        if isprop(app, 'CalibrationFactor')
            safeSetNumeric(app.CalibrationFactor, HD.params.ShackHartmannCorrection.calibrationfactor);
        end

        if isprop(app, 'ConvergenceThreshold')
            safeSetNumeric(app.ConvergenceThreshold, HD.params.ShackHartmannCorrection.convergencethreshold);
        end

        if isprop(app, 'onlydefocusCheckBox')
            safeSetCheckbox(app.onlydefocusCheckBox, HD.params.ShackHartmannCorrection.onlydefocus);
        end

    end

    % Additional advanced processing parameters
    if isprop(app, 'SVDThresholdCheckBox')
        safeSetCheckbox(app.SVDThresholdCheckBox, HD.params.svdThreshold_enable);
    end

    if isprop(app, 'SVDThreshold')
        safeSetNumeric(app.SVDThreshold, HD.params.svdThreshold_value);
    end

    if isprop(app, 'svdStride')
        safeSetNumeric(app.svdStride, HD.params.svdStride);
    end

    % Local filtering parameters
    if isprop(app, 'spatialCheckBox')
        safeSetCheckbox(app.spatialCheckBox, HD.params.local_spatialFilter);
    end

    if isprop(app, 'temporalCheckBox')
        safeSetCheckbox(app.temporalCheckBox, HD.params.local_temporalFilter);
    end

    if isprop(app, 'phi1')
        safeSetNumeric(app.phi1, HD.params.local_phi1);
    end

    if isprop(app, 'phi1')
        safeSetNumeric(app.phi1, HD.params.local_phi2);
    end

    if isprop(app, 'nu1')
        safeSetNumeric(app.nu1, HD.params.local_nu1);
    end

    if isprop(app, 'nu2')
        safeSetNumeric(app.nu2, HD.params.local_nu2);
    end

    if isprop(app, 'unitCellsinLattice')
        safeSetNumeric(app.unitCellsinLattice, HD.params.unit_cells);
    end

    if isprop(app, 'r1')
        safeSetNumeric(app.r1, HD.params.r1);
    end

    if isprop(app, 'xyStride')
        safeSetNumeric(app.xyStride, HD.params.xy_stride);
    end

    % Temporal filter
    if isprop(app, 'temporalfilterCheckBox')
        safeSetCheckbox(app.temporalfilterCheckBox, HD.params.temporalFilter);
    end

    if isprop(app, 'temporalFilter')
        safeSetNumeric(app.temporalFilter, HD.params.temporalFilter_value);
    end

    % Phase registration
    if isprop(app, 'phaseregistrationCheckBox')
        safeSetCheckbox(app.phaseregistrationCheckBox, HD.params.phase_registration);
    end

    if isprop(app, 'rephasingCheckBox')
        safeSetCheckbox(app.rephasingCheckBox, HD.params.rephasing);
    end

    if isprop(app, 'iterativeregistrationCheckBox')
        safeSetCheckbox(app.iterativeregistrationCheckBox, HD.params.iterative_registration);
    end

    if isprop(app, 'showrefCheckBox')
        safeSetCheckbox(app.showrefCheckBox, HD.params.show_ref);
    end

    % Update UI enable states based on current settings
    if isprop(app, 'updateTimeTransformControls')

        try
            app.updateTimeTransformControls();
        catch
            % Silently fail
        end

    end

    % Update current file panel title if file is loaded
    if ~isempty(HD.file) && isfield(HD.file, 'path') && isprop(app, 'CurrentFilePanel')

        try
            app.CurrentFilePanel.Title = ['Current File : ' HD.file.path];
        catch
            % Silently fail
        end

    end

end

end
