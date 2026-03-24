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
        if isprop(app, 'framePositionField')
            safeSetNumeric(app.framePositionField, double(HD.params.frame_position));
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
            app.Image_typesListBox.Value = HD.params.image_types;
        end
    end
    
    % Spatial filtering
    if isprop(app, 'spatial_filter')
        safeSetCheckbox(app.spatial_filter, HD.params.spatial_filter);
    end
    
    if isprop(app, 'hilbert_filter')
        safeSetCheckbox(app.hilbert_filter, HD.params.hilbert_filter);
    end
    
    if isprop(app, 'spatial_filter_range1') && isprop(app, 'spatial_filter_range2')
        if length(HD.params.spatial_filter_range) >= 2
            safeSetNumeric(app.spatial_filter_range1, HD.params.spatial_filter_range(1));
            safeSetNumeric(app.spatial_filter_range2, HD.params.spatial_filter_range(2));
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
    
    if isprop(app, 'svdx_filter')
        safeSetCheckbox(app.svdx_filter, HD.params.svdx_filter);
    end
    
    if isprop(app, 'svdx_t_filter')
        safeSetCheckbox(app.svdx_t_filter, HD.params.svdx_t_filter);
    end
    
    % SVD thresholds
    if isprop(app, 'svd_threshold')
        safeSetNumeric(app.svd_threshold, HD.params.svd_threshold);
    end
    
    if isprop(app, 'svdx_threshold')
        safeSetNumeric(app.svdx_threshold, HD.params.svdx_threshold);
    end
    
    if isprop(app, 'svdx_t_threshold')
        safeSetNumeric(app.svdx_t_threshold, HD.params.svdx_t_threshold);
    end
    
    if isprop(app, 'svdx_Nsub')
        safeSetNumeric(app.svdx_Nsub, HD.params.svdx_Nsub);
    end
    
    if isprop(app, 'svdx_t_Nsub')
        safeSetNumeric(app.svdx_t_Nsub, HD.params.svdx_t_Nsub);
    end
    
    % Time transformation
    if isprop(app, 'time_transform')
        items = ["FFT", "PCA", "ICA", "Wavelet_Morlet", "autocorrelation", "intercorrelation", "phase difference", "None"];
        app.time_transform.Items = items;
        safeSetDropdown(app.time_transform, HD.params.time_transform, items);
    end
    
    if isprop(app, 'time_range1') && isprop(app, 'time_range2')
        if length(HD.params.time_range) >= 2
            safeSetNumeric(app.time_range1, HD.params.time_range(1));
            safeSetNumeric(app.time_range2, HD.params.time_range(2));
        end
    end
    
    if isprop(app, 'index_range1') && isprop(app, 'index_range2')
        if length(HD.params.index_range) >= 2
            safeSetNumeric(app.index_range1, HD.params.index_range(1));
            safeSetNumeric(app.index_range2, HD.params.index_range(2));
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
        
        if isprop(app, 'NumberOfIterationEditField')
            safeSetNumeric(app.NumberOfIterationEditField, HD.params.ShackHartmannCorrection.N_iterate);
        end
        
        if isprop(app, 'ZernikeProjectionCheckBox')
            safeSetCheckbox(app.ZernikeProjectionCheckBox, HD.params.ShackHartmannCorrection.ZernikeProjection);
        end
        
        if isprop(app, 'shackhartmannzernikeranksEditField')
            safeSetNumeric(app.shackhartmannzernikeranksEditField, HD.params.ShackHartmannCorrection.zernikeranks);
        end
        
        if isprop(app, 'subapnumpositionsEditField')
            safeSetNumeric(app.subapnumpositionsEditField, HD.params.ShackHartmannCorrection.subapnumpositions);
        end
        
        if isprop(app, 'imagesubapsizeratioEditField')
            safeSetNumeric(app.imagesubapsizeratioEditField, HD.params.ShackHartmannCorrection.imagesubapsizeratio);
        end
        
        if isprop(app, 'subaperturemarginEditField')
            safeSetNumeric(app.subaperturemarginEditField, HD.params.ShackHartmannCorrection.subaperturemargin);
        end
        
        if isprop(app, 'referenceimageDropDown')
            items = {'central subaperture', 'resized image'};
            safeSetDropdown(app.referenceimageDropDown, HD.params.ShackHartmannCorrection.referenceimage, items);
        end
        
        if isprop(app, 'CalibrationFactorEditField')
            safeSetNumeric(app.CalibrationFactorEditField, HD.params.ShackHartmannCorrection.calibrationfactor);
        end
        
        if isprop(app, 'ConvergenceThreshold')
            safeSetNumeric(app.ConvergenceThreshold, HD.params.ShackHartmannCorrection.convergencethreshold);
        end
        
        if isprop(app, 'onlydefocusCheckBox')
            safeSetCheckbox(app.onlydefocusCheckBox, HD.params.ShackHartmannCorrection.onlydefocus);
        end
    end
    
    % Additional advanced processing parameters
    if isprop(app, 'SVDxCheckBox')
        safeSetCheckbox(app.SVDxCheckBox, HD.params.svdx_enable);
    end
    
    if isprop(app, 'SVDx_SubApEditField')
        safeSetNumeric(app.SVDx_SubApEditField, HD.params.svdx_subap);
    end
    
    if isprop(app, 'SVDThresholdCheckBox')
        safeSetCheckbox(app.SVDThresholdCheckBox, HD.params.svd_threshold_enable);
    end
    
    if isprop(app, 'SVDThresholdEditField')
        safeSetNumeric(app.SVDThresholdEditField, HD.params.svd_threshold_value);
    end
    
    if isprop(app, 'SVDStrideEditField')
        safeSetNumeric(app.SVDStrideEditField, HD.params.svd_stride);
    end
    
    % Local filtering parameters
    if isprop(app, 'spatialCheckBox')
        safeSetCheckbox(app.spatialCheckBox, HD.params.local_spatial_filter);
    end
    
    if isprop(app, 'temporalCheckBox')
        safeSetCheckbox(app.temporalCheckBox, HD.params.local_temporal_filter);
    end
    
    if isprop(app, 'phi1EditField')
        safeSetNumeric(app.phi1EditField, HD.params.local_phi1);
    end
    
    if isprop(app, 'phi2EditField')
        safeSetNumeric(app.phi2EditField, HD.params.local_phi2);
    end
    
    if isprop(app, 'nu1EditField')
        safeSetNumeric(app.nu1EditField, HD.params.local_nu1);
    end
    
    if isprop(app, 'nu2EditField')
        safeSetNumeric(app.nu2EditField, HD.params.local_nu2);
    end
    
    if isprop(app, 'unitcellsinlatticeEditField')
        safeSetNumeric(app.unitcellsinlatticeEditField, HD.params.unit_cells);
    end
    
    if isprop(app, 'r1EditField')
        safeSetNumeric(app.r1EditField, HD.params.r1);
    end
    
    if isprop(app, 'xystrideEditField')
        safeSetNumeric(app.xystrideEditField, HD.params.xy_stride);
    end
    
    % Temporal filter
    if isprop(app, 'temporalfilterCheckBox')
        safeSetCheckbox(app.temporalfilterCheckBox, HD.params.temporal_filter);
    end
    
    if isprop(app, 'temporalfilterEditField')
        safeSetNumeric(app.temporalfilterEditField, HD.params.temporal_filter_value);
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
    
    if isprop(app, 'updateSvdxFilterControls')
        try
            app.updateSvdxFilterControls();
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