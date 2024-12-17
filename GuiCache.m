classdef GuiCache
    % A class to store parameters from GUI
    % so that during computations, values are fetched from cache instead of GUI
    % so that the user can modify the values in the GUI without messing
    % everything up
    properties (Access = public)

        %% File selection
        % misc info collected on the file 
        fs double % sampling frequency
        wavelength double % laser central wavelength
        pix_width double
        pix_height double
        Nx double
        Ny double

        % calculation parameters
        parrallel_mode char % parrallelization mode
        nb_workers double % ...

        %% Video rendering

        output_video char
        ref_batch_size double
        batch_stride double
        DX double
        DY double
        low_memory logical
        save_raw logical
        rephasing logical
        registration logical
        registration_via_phase logical
        iterative_registration logical
        temporal_filter_flag logical
        temporal_filter double
        registration_disc logical
        registration_disc_ratio double

        % color image parameters
        color_f1 double
        color_f2 double
        color_f3 double
        
        %% Advanced Processing
        SVD logical
        SVDx logical
        SVDx_nb_subap double
        SVD_threshold logical
        SVD_threshold_value double

        % local filtering

        local_temporal logical
        phi1 double
        phi2 double
        local_spatial logical
        nu1 double
        nu2 double

        % dark field parameters
        xystride double
        num_unit_cells_x double
        r1 double
        

        %% Aberration compensation
        aberration_compensation logical

        % iterative optimization parameters
        iterative_aberration_compensation double
        optimization_zernike_ranks double
        mask_num_iter double
        zernikes_tol double
        max_constraint double

        % shack-hartmann parameters
        shack_hartmann_aberration_compensation double
        shack_hartmann_zernike_ranks double
        image_subapertures_size_ratio double
        num_subapertures_positions double
        subaperture_margin double
        SubAp_PCA double
        minSubAp_PCA double
        maxSubAp_PCA double
        zernike_projection double
        shack_hartmann_ref_image double

    end

    methods (Access = public)

        function obj = GuiCache(app)
            % Contructor function 
            % fetch all the GUI parameters from the app GUI (and internal variables)
            % to the class object
            %
            % : bufferize (and lock during computation) current paremeter values from front end

            %% File selection
            obj.fs = app.Fs/1000;
            obj.wavelength = app.wavelengthEditField.Value;
            obj.pix_width = app.pix_width; % TODO should be .Value
            obj.pix_height = app.pix_height; % TODO should be .Value
            obj.parrallel_mode = app.ParallelismDropDown.Value;%strrep(app.ParallelismDropDown.Value, ' ', '_');
            obj.nb_workers = app.numworkersSpinner.Value;
            obj.Nx = app.Nx;
            obj.Ny = app.Ny;

            %% Video rendering
            obj.output_video = (strrep(app.outputvideoDropDown.Value, ' ', '_')); % replaces all ' ' with '_'
            obj.ref_batch_size = app.refbatchsizeEditField.Value;
            obj.batch_stride = app.batchstrideEditField.Value;
            obj.DX = app.DX; % TODO should be .Value
            obj.DY = app.DY; % TODO should be .Value
            obj.low_memory = app.lowmemoryCheckBox.Value;
            obj.save_raw = app.saverawvideosCheckBox.Value;
            obj.rephasing = app.rephasingCheckBox.Value;
            obj.registration = app.imageregistrationCheckBox.Value;
            obj.registration_via_phase = app.phaseregistrationCheckBox.Value;
            obj.iterative_registration = app.iterativeregistrationCheckBox.Value;
            obj.temporal_filter_flag = app.temporalfilterCheckBox.Value;
            obj.temporal_filter = app.temporalfilterEditField.Value;
            % obj.show_ref = app.ShowrefCheckBox.Value;

            %% Image rendering
            obj.spatial_transformation = app.spatialTransformationDropDown.Value; % Fresnel or angular spectrum...&obj.
            obj.z = app.z_reconstruction;
            obj.z_retina = app.zretinaEditField.Value;
            obj.z_iris = app.zirisEditField.Value;
            obj.z_switch = app.Switch.Value;
            obj.preview_choice = strrep(app.ImageChoiceDropDown.Value, ' ', '_'); % replaces all ' ' with '_'
            obj.time_transform = app.time_transform; % here the object time_transform considering it is live updated in the app
            obj.blur = app.blurEditField.Value;
            obj.batch_size = app.batchsizeEditField.Value;
            obj.position_in_file = app.positioninfileSlider.Value;
            obj.output_videos = (strrep(app.outputvideoDropDown.Value, ' ', '_'));
            obj.low_memory = app.lowmemoryCheckBox.Value;
            obj.rephasing = app.rephasingCheckBox.Value;
            obj.save_raw = app.saverawvideosCheckBox.Value;
            obj.registration_disc = app.registrationdiscCheckBox.Value;
            obj.registration_disc_ratio = app.regDiscRatioEditField.Value;

            obj.color_f1 = app.compositef1EditField.Value;
            obj.color_f2 = app.compositef2EditField.Value;
            obj.color_f3 = app.compositef3EditField.Value;
            obj.low_frequency = app.lowfrequencyCheckBox.Value;

            %% Advanced Processing

            obj.SVD = app.SVDCheckBox.Value;
            obj.SVDx = app.SVDxCheckBox.Value;
            obj.SVDx_nb_subap = app.SVDx_SubApEditField.Value;
            obj.SVD_threshold = app.SVDTresholdCheckBox.Value;
            obj.SVD_threshold_value = app.SVDTresholdEditField.Value;

            obj.local_spatial = app.spatialCheckBox.Value;
            obj.phi1 = app.phi1EditField;
            obj.phi2 = app.phi2EditField;
            obj.local_temporal = app.temporalCheckBox.Value;
            obj.nu1 = app.nu1EditField;
            obj.nu2 = app.nu2EditField;

            obj.xystride = app.xystrideEditField.Value;
            obj.num_unit_cells_x = app.unitcellsinlatticeEditField.Value;
            obj.r1 = app.r1EditField.Value;

            %% Aberration compensation

            obj.aberration_compensation = app.IterativeoptimizationCheckBox.Value;
            % iterative optimization parameters
            obj.iterative_aberration_compensation = app.IterativeoptimizationCheckBox.Value;
            obj.optimization_zernike_ranks = app.optimizationzernikeranksEditField.Value;
            obj.mask_num_iter = app.masknumiterEditField.Value;
            obj.zernikes_tol = app.zernikestolEditField.Value;
            obj.max_constraint = app.maxconstraintEditField.Value;
            % shack-hartmann parameters
            obj.shack_hartmann_aberration_compensation = app.ShackHartmannCheckBox.Value;
            obj.shack_hartmann_zernike_ranks = app.shackhartmannzernikeranksEditField.Value;
            obj.image_subapertures_size_ratio = app.imagesubapsizeratioEditField.Value;
            obj.num_subapertures_positions = app.subapnumpositionsEditField.Value;
            obj.subaperture_margin = app.subaperturemarginEditField.Value;
            obj.SubAp_PCA = app.SubAp_PCACheckBox.Value;
            obj.minSubAp_PCA = app.minSubAp_PCAEditField.Value;
            obj.maxSubAp_PCA = app.maxSubAp_PCAEditField.Value;
            obj.zernike_projection = app.ZernikeProjectionCheckBox.Value;
            obj.shack_hartmann_ref_image = app.referenceimageDropDown.Value;
            obj.notes = app.NotesTextArea.Value;

        end

        function load2Gui(obj, app)
            % set gui parameters from cache

            app.batchsizeEditField.Value = loadGUIVariable(obj.batch_size);
            app.max_PCAEditField.Limits = loadGUIVariable([0 double(app.batchsizeEditField.Value)]);
            app.spatialTransformationDropDown.Value = loadGUIVariable(obj.spatialTransformation);
            app.refbatchsizeEditField.Value = loadGUIVariable(obj.ref_batch_size);
            app.batchstrideEditField.Value = loadGUIVariable(obj.batch_stride);
            app.Switch.Value = loadGUIVariable(obj.z_switch);
            app.zretinaEditField.Value = loadGUIVariable(obj.z_retina);
            app.zirisEditField.Value = loadGUIVariable(obj.z_iris);
            app.time_transform = loadGUIVariable(obj.time_transform);
            app.blurEditField.Value = loadGUIVariable(obj.blur);
            app.ImageChoiceDropDown.Value = loadGUIVariable(strrep(obj.imageChoice, '_', ' '));
            app.timetransformDropDown.Value = loadGUIVariable(obj.time_transform.type);
            app.SVDCheckBox.Value = loadGUIVariable(obj.SVD);
            app.f1EditField.Value = loadGUIVariable(obj.time_transform.f1);
            app.f2EditField.Value = loadGUIVariable(obj.time_transform.f2);
            app.min_PCAEditField.Value = loadGUIVariable(obj.time_transform.min_PCA);
            app.max_PCAEditField.Value = loadGUIVariable(obj.time_transform.max_PCA);
            app.imageregistrationCheckBox.Value = loadGUIVariable(obj.registration);
            app.iterativeregistrationCheckBox.Value = loadGUIVariable(obj.iterative_registration);
            app.wavelengthEditField.Value = loadGUIVariable(obj.wavelength);
            app.outputvideoDropDown.Value = loadGUIVariable(strrep(obj.output_videos, '_', ' '));
            app.lowmemoryCheckBox.Value = loadGUIVariable(obj.low_memory);
            app.rephasingCheckBox.Value = loadGUIVariable(obj.rephasing);
            app.NotesTextArea.Value = loadGUIVariable(obj.notes);
            app.positioninfileSlider.Value = loadGUIVariable(obj.position_in_file);
            app.EditField.Value = loadGUIVariable(obj.position_in_file);
            app.IterativeoptimizationCheckBox.Value = loadGUIVariable(obj.iterative_aberration_compensation);
            app.masknumiterEditField.Value = loadGUIVariable(obj.mask_num_iter);
            app.ShackHartmannCheckBox.Value = loadGUIVariable(obj.shack_hartmann_aberration_compensation);
            app.ZernikeProjectionCheckBox.Value = loadGUIVariable(obj.zernike_projection);
            app.referenceimageDropDown.Value = loadGUIVariable(obj.shack_hartmann_ref_image);
            app.shackhartmannzernikeranksEditField.Value = loadGUIVariable(obj.shack_hartmann_zernike_ranks);
            app.imagesubapsizeratioEditField.Value = loadGUIVariable(obj.image_subapertures_size_ratio);
            app.subapnumpositionsEditField.Value = loadGUIVariable(obj.num_subapertures_positions);
            app.subaperturemarginEditField.Value = loadGUIVariable(obj.subaperture_margin);
            app.SubAp_PCACheckBox.Value = loadGUIVariable(obj.SubAp_PCA);
            app.minSubAp_PCAEditField.Value = loadGUIVariable(obj.minSubAp_PCA);
            app.maxSubAp_PCAEditField.Value = loadGUIVariable(obj.maxSubAp_PCA);
            app.compositef1EditField.Value = loadGUIVariable(obj.color_f1);
            app.compositef2EditField.Value = loadGUIVariable(obj.color_f2);
            app.compositef3EditField.Value = loadGUIVariable(obj.color_f3);
            app.lowfrequencyCheckBox.Value = loadGUIVariable(obj.low_frequency);
            app.saverawvideosCheckBox.Value = loadGUIVariable(obj.save_raw);


        end

    end

end
