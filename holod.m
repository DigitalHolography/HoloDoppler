classdef holod < matlab.apps.AppBase

    % Properties that correspond to app components
    properties (Access = public)
        HoloDopplerUIFigure            matlab.ui.Figure
        GridLayout4                    matlab.ui.container.GridLayout
        ImageRight                     matlab.ui.control.Image
        ImageLeft                      matlab.ui.control.Image
        CurrentFilePanel               matlab.ui.container.Panel
        GridLayout                     matlab.ui.container.GridLayout
        GridLayout2                    matlab.ui.container.GridLayout
        GridLayout3                    matlab.ui.container.GridLayout
        ImagerenderingPanel            matlab.ui.container.Panel
        spatialfilterratiohigh         matlab.ui.control.NumericEditField
        compositef3EditFieldLabel_5    matlab.ui.control.Label
        spatialfilterratio             matlab.ui.control.NumericEditField
        compositef3EditFieldLabel_4    matlab.ui.control.Label
        numFreqEditField               matlab.ui.control.NumericEditField
        scan3D                         matlab.ui.control.Button
        ShowSpectrumButton             matlab.ui.control.Button
        spatialTransformationDropDown  matlab.ui.control.DropDown
        spatialtransformationLabel     matlab.ui.control.Label
        compositef1EditField           matlab.ui.control.NumericEditField
        compositef3EditFieldLabel_3    matlab.ui.control.Label
        compositef2EditField           matlab.ui.control.NumericEditField
        compositef3EditFieldLabel_2    matlab.ui.control.Label
        maxEditFieldLabel_2            matlab.ui.control.Label
        savelamp                       matlab.ui.control.Lamp
        AutofocusButton                matlab.ui.control.Button
        SavepreviewButton              matlab.ui.control.Button
        renderLamp                     matlab.ui.control.Lamp
        showSpatialFilterCheckBox      matlab.ui.control.CheckBox
        RenderpreviewButton            matlab.ui.control.Button
        batchsizeEditField             matlab.ui.control.NumericEditField
        batchsizeEditFieldLabel        matlab.ui.control.Label
        num_batches                    matlab.ui.control.Label
        Switch                         matlab.ui.control.Switch
        zirisEditField                 matlab.ui.control.NumericEditField
        zretinaEditField               matlab.ui.control.NumericEditField
        positioninfileSlider           matlab.ui.control.Slider
        positioninfileSliderLabel      matlab.ui.control.Label
        EditField                      matlab.ui.control.NumericEditField
        max_PCAEditField               matlab.ui.control.NumericEditField
        maxEditFieldLabel              matlab.ui.control.Label
        min_PCAEditField               matlab.ui.control.NumericEditField
        minEditFieldLabel              matlab.ui.control.Label
        timetransformDropDown          matlab.ui.control.DropDown
        timetransformDropDownLabel     matlab.ui.control.Label
        blurEditField                  matlab.ui.control.NumericEditField
        blurEditFieldLabel             matlab.ui.control.Label
        ImageChoiceDropDown            matlab.ui.control.DropDown
        compositef3EditField           matlab.ui.control.NumericEditField
        compositef3EditFieldLabel      matlab.ui.control.Label
        f2EditField                    matlab.ui.control.NumericEditField
        f2EditFieldLabel               matlab.ui.control.Label
        f1EditField                    matlab.ui.control.NumericEditField
        f1EditFieldLabel               matlab.ui.control.Label
        AberrationcompensationPanel    matlab.ui.container.Panel
        imagesubapsizeratioEditField   matlab.ui.control.NumericEditField
        imagesubapsizeratioEditFieldLabel  matlab.ui.control.Label
        subapnumpositionsEditField     matlab.ui.control.NumericEditField
        subapnumpositionsEditFieldLabel  matlab.ui.control.Label
        referenceimageDropDown         matlab.ui.control.DropDown
        referenceimageDropDownLabel    matlab.ui.control.Label
        ZernikeProjectionCheckBox      matlab.ui.control.CheckBox
        savecoefsCheckBox              matlab.ui.control.CheckBox
        rangeYEditField                matlab.ui.control.NumericEditField
        rangeYEditFieldLabel           matlab.ui.control.Label
        rangeZEditField                matlab.ui.control.NumericEditField
        rangeZEditFieldLabel           matlab.ui.control.Label
        volumesizeEditField            matlab.ui.control.NumericEditField
        volumesizeEditFieldLabel       matlab.ui.control.Label
        maxSubAp_PCAEditField          matlab.ui.control.NumericEditField
        maxEditField_2Label            matlab.ui.control.Label
        minSubAp_PCAEditField          matlab.ui.control.NumericEditField
        minEditField_2Label            matlab.ui.control.Label
        SubAp_PCACheckBox              matlab.ui.control.CheckBox
        PreviewLabel                   matlab.ui.control.Label
        masknumiterEditField           matlab.ui.control.NumericEditField
        masknumiterEditFieldLabel      matlab.ui.control.Label
        maxconstraintEditField         matlab.ui.control.NumericEditField
        maxconstraintEditFieldLabel    matlab.ui.control.Label
        zernikestolEditField           matlab.ui.control.NumericEditField
        toleranceLabel                 matlab.ui.control.Label
        optimizationzernikeranksEditField  matlab.ui.control.NumericEditField
        zernikeranksEditField_2Label   matlab.ui.control.Label
        IterativeoptimizationCheckBox  matlab.ui.control.CheckBox
        subaperturemarginEditField     matlab.ui.control.NumericEditField
        subaperturemarginEditFieldLabel  matlab.ui.control.Label
        shackhartmannzernikeranksEditField  matlab.ui.control.NumericEditField
        zernikeranksEditFieldLabel     matlab.ui.control.Label
        ShackHartmannCheckBox          matlab.ui.control.CheckBox
        Label_2                        matlab.ui.control.Label
        UIAxes_aberrationPreview       matlab.ui.control.UIAxes
        AdvancedProcessingPanel        matlab.ui.container.Panel
        SVDTresholdEditFieldLabel_2    matlab.ui.control.Label
        SVDStrideEditField             matlab.ui.control.NumericEditField
        SVDThresholdCheckBox           matlab.ui.control.CheckBox
        SVDTresholdEditFieldLabel      matlab.ui.control.Label
        SVDThresholdEditField          matlab.ui.control.NumericEditField
        SVDxCheckBox                   matlab.ui.control.CheckBox
        SVDx_SubApEditField            matlab.ui.control.NumericEditField
        SVDx_SubApEditFieldLabel       matlab.ui.control.Label
        xystrideEditField              matlab.ui.control.NumericEditField
        xystrideEditFieldLabel         matlab.ui.control.Label
        r1EditField                    matlab.ui.control.NumericEditField
        r1EditFieldLabel               matlab.ui.control.Label
        unitcellsinlatticeEditField    matlab.ui.control.NumericEditField
        unitcellsinlatticeEditFieldLabel  matlab.ui.control.Label
        nu2EditField                   matlab.ui.control.NumericEditField
        nu2EditFieldLabel              matlab.ui.control.Label
        nu1EditField                   matlab.ui.control.NumericEditField
        nu1EditFieldLabel              matlab.ui.control.Label
        phi2EditField                  matlab.ui.control.NumericEditField
        phi2EditFieldLabel             matlab.ui.control.Label
        phi1EditField                  matlab.ui.control.NumericEditField
        phi1EditFieldLabel             matlab.ui.control.Label
        LocalfilteringLabel            matlab.ui.control.Label
        temporalCheckBox               matlab.ui.control.CheckBox
        spatialCheckBox                matlab.ui.control.CheckBox
        SVDCheckBox                    matlab.ui.control.CheckBox
        FileselectionPanel             matlab.ui.container.Panel
        ppx                            matlab.ui.control.NumericEditField
        wavelengthEditFieldLabel_2     matlab.ui.control.Label
        ppy                            matlab.ui.control.NumericEditField
        setUpDropDown                  matlab.ui.control.DropDown
        Label                          matlab.ui.control.Label
        numworkersSpinner              matlab.ui.control.Spinner
        numworkersSpinnerLabel         matlab.ui.control.Label
        NotesTextArea                  matlab.ui.control.TextArea
        NotesTextAreaLabel             matlab.ui.control.Label
        fsEditField                    matlab.ui.control.NumericEditField
        fsEditFieldLabel               matlab.ui.control.Label
        ParallelismDropDown            matlab.ui.control.DropDown
        wavelengthEditField            matlab.ui.control.NumericEditField
        wavelengthEditFieldLabel       matlab.ui.control.Label
        LoadfileButton                 matlab.ui.control.Button
        VideorenderingPanel            matlab.ui.container.Panel
        DxEditFieldLabel_2             matlab.ui.control.Label
        regDiscRatioEditField          matlab.ui.control.NumericEditField
        registrationdiscCheckBox       matlab.ui.control.CheckBox
        refbatchsizeEditField          matlab.ui.control.NumericEditField
        refbatchsizeEditFieldLabel     matlab.ui.control.Label
        DyEditField                    matlab.ui.control.NumericEditField
        DyEditFieldLabel               matlab.ui.control.Label
        DxEditField                    matlab.ui.control.NumericEditField
        DxEditFieldLabel               matlab.ui.control.Label
        batchstrideEditField           matlab.ui.control.NumericEditField
        batchstrideEditFieldLabel      matlab.ui.control.Label
        imageregistrationCheckBox      matlab.ui.control.CheckBox
        SaveconfigButton               matlab.ui.control.Button
        showrefCheckBox                matlab.ui.control.CheckBox
        iterativeregistrationCheckBox  matlab.ui.control.CheckBox
        saveconfigLamp                 matlab.ui.control.Lamp
        ApplytoallfilesCheckBox        matlab.ui.control.CheckBox
        ImagerenderingButton           matlab.ui.control.Button
        FoldermanagementButton         matlab.ui.control.Button
        temporalfilterEditField        matlab.ui.control.NumericEditField
        temporalfilterCheckBox         matlab.ui.control.CheckBox
        phaseregistrationCheckBox      matlab.ui.control.CheckBox
        outputvideoDropDown            matlab.ui.control.DropDown
        outputvideoDropDownLabel       matlab.ui.control.Label
        rephasingCheckBox              matlab.ui.control.CheckBox
    end


    properties (Access = public)

        HD 
        % skip callbacks if no file_M0 is loaded
        nb_cpu_cores

        file_loaded

        filename % current file_M0 loaded
        filepath
        extension % .raw or .cine
        interferogram_stream

        % data related to current displayed frame
        frame_batch

        % misc proxy data
        Nx
        Ny
        Fs
        z_reconstruction
        z_retina
        z_iris
        pix_width
        pix_height
        blur
        kernelAngularSpectrum
        kernelFresnel
        FH
        SH
        var_ImageTypeList
        hologram
        phasePlane %aberration correction preview
        DX % x circshift for registration
        DY % y circshift for registration

        mask % logical mask to select a sub part of the image

        spatial_filter_mask

        image_registration



        % misc
        cache % cache containing all parameters
        rephasing_data % data containing correction phase computed previously

        SubAp_PCA
        time_transform

        drawer_list = {}
    end

    properties (Access = private)
        DialogApp % Dialog box app
        poolobj
    end

    methods (Access = private)
        
        

        
        function parfor_arg = numCPUCores(app, safety_ratio) % FIXME safety_ratio 0.1 ?
            %             safety_ration = 0.1;
            FH = app.FH;
            s = whos('FH');
            [user, sys] = memory;
            a = sys.PhysicalMemory.Available; % total physical CPU memory
            user.MaxPossibleArrayBytes; % includes swap disk
            user.MemAvailableAllArrays; % includes swap disk
            nbytes_FH_SVD = s.bytes;
            if app.SVDCheckBox.Value
                nbytes_FH_SVD = s.bytes * 2; % reserved CPU memory in case of FH + SVD
            end
            fprintf('nBytes_FH_SVD: %d Bytes\n', nbytes_FH_SVD);
            fprintf('Physical memory available: %d Bytes\n', a);
            parfor_arg = max(floor(safety_ratio * a / nbytes_FH_SVD), 1);
            fprintf('Numbers of CPU cores: %d\n', parfor_arg);
        end

        
    end
    methods (Access = public)
        function compute_kernel(app, use_gpu)
            app.kernelAngularSpectrum = propagation_kernelAngularSpectrum(app.Nx, app.Ny, app.z_reconstruction, app.wavelengthEditField.Value, app.pix_width, app.pix_height, use_gpu);
            app.kernelFresnel = propagation_kernelFresnel(app.Nx, app.Ny, app.z_reconstruction, app.wavelengthEditField.Value, app.pix_width, app.pix_height, use_gpu);
        end

        

        function reconstructWithPreviousSettings(app, YesOrNo)
            if YesOrNo == 1
                % app.interferogram_stream.footer = ;
                batchSize = app.interferogram_stream.footer.computeSettings.imageRendering.batchSize;

                app.zretinaEditField.Value = app.interferogram_stream.footer.computeSettings.imageRendering.zDistance;
                app.positioninfileSlider.Limits = [0, double(app.interferogram_stream.num_frames-batchSize)];
                app.positioninfileSlider.Value = min(app.positioninfileSlider.Value, app.positioninfileSlider.Limits(2));
                app.EditField.Limits = [0, max(double(app.interferogram_stream.num_frames-batchSize), 1)];
                app.EditField.Value = min(app.EditField.Value, app.EditField.Limits(2));
                app.frame_batch = app.interferogram_stream.read_frame_batch(batchSize, 0);
                app.compute_kernel(false);
                %% read the values from the footer and use them for reconstruction
            end
            %% set the reconstruction values
        end

        


        

        function show_aberration_correction(app)
            if ~app.file_loaded
                return;
            end

            if app.ShackHartmannCheckBox.Value
                imshow(mat2gray(app.phasePlane), 'Parent', app.UIAxes_aberrationPreview,...
                    'XData', [1 app.UIAxes_aberrationPreview.Position(3)], ...
                    'YData', [1 app.UIAxes_aberrationPreview.Position(4)]);
            end
        end
        
        
    end

    % Callbacks that handle component events
    methods (Access = private)

        % Code that executes after component creation
        function startupFcn(app)
            if exist("version.txt",'file')
                v = readlines('version.txt');
                fprintf("==========================================\n " + ...
                    "Welcome to HoloDoppler %s\n" + ...
                    "------------------------------------------\n" + ...
                    "Developed by the DigitalHolographyFoundation\n" + ...
                    "==========================================\n",v(1));
            end
            % add subfolders to path
            
            %addpath('call_backs'); % dossier à ajouter au research path matlab pour utiliser correctement l'application
            %addpath('call_backs\pack');
            addpath('AberrationCorrection',"New Folder\","ReaderClasses\");
            app.HD = HoloDopplerClass();
            classtogui(app.HD,app);
            %app.var_ImageTypeList = ImageTypeList();
            app.HoloDopplerUIFigure.Name = ['HoloDoppler ',char(v(1))];
            displaySplashScreen();
            % set app constants
            app.blur = 35;
            app.file_loaded = false;
            app.DX = 0;
            app.DY = 0;

            
        end

        % Button pushed function: LoadfileButton
        function LoadfileButtonPushed(app, event)
            %% open file and manage file extension
            f = figure('Renderer', 'painters', 'Position', [-100 -100 0 0]); %create a dummy figure so that uigetfile doesn't minimize our GUI
            if (isempty(app.filepath))
                [fname, fpath] = uigetfile('*.raw;*.cine;*.holo');
            else
                [fname, fpath] = uigetfile(strcat(app.filepath, "*.raw;*.cine;*.holo"));
            end
            delete(f); %delete the dummy figure
            if fname == 0
                return
            end
            %config = fetch_config(fpath, fname);
            
            %Loadfile(app,fname, fpath, config);
            app.HD.Loadfile(fullfile(fpath , fname));
        end

        % Value changed function: zretinaEditField
        function zretinaEditFieldValueChanged(app, event)
            zChanged(app);
        end

        % Value changed function: f1EditField
        function f1EditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            app.time_transform.f1 = app.f1EditField.Value;
        end

        % Value changed function: f2EditField
        function f2EditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            app.time_transform.f2 = app.f2EditField.Value;
        end

        % Value changed function: wavelengthEditField
        function wavelengthEditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            app.compute_kernel(false);
        end

        % Value changed function: batchsizeEditField
        function batchsizeEditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end
            app.renderLamp.Color = [1, 0, 0];
            drawnow;

            app.positioninfileSlider.Limits = [0, double(app.interferogram_stream.num_frames-app.batchsizeEditField.Value)];
            app.positioninfileSlider.Value = min(app.positioninfileSlider.Value, app.positioninfileSlider.Limits(2));
            app.EditField.Limits = [0, double(app.interferogram_stream.num_frames-app.batchsizeEditField.Value)];
            app.EditField.Value = min(app.EditField.Value, app.EditField.Limits(2));
            app.max_PCAEditField.Limits = [0, double(app.batchsizeEditField.Value)];

            app.frame_batch = app.interferogram_stream.read_frame_batch(app.batchsizeEditField.Value, 0);

            app.renderLamp.Color = [0, 1, 0];
            drawnow;
        end

        % Button pushed function: ImagerenderingButton
        function ImagerenderingButtonPushed(app, event)
            if strcmp(app.ParallelismDropDown.Value,"LightGPU")
                LightRendervideoGPU(app);
            else
                Rendervideo(app);
            end
        end

        % Button pushed function: AutofocusButton
        function AutofocusButtonPushed(app, event)
            Autofocus(app);
        end

        % Close request function: HoloDopplerUIFigure
        function HoloDopplerUIFigureCloseRequest(app, event)
            delete(app)
        end

        % Value changed function: positioninfileSlider
        function positioninfileSliderValueChanged(app, event)
            value = app.positioninfileSlider.Value;
            app.EditField.Value = value;

            if ~app.file_loaded
                return
            end

            Renderpreview(app)
            app.renderLamp.Color = [1, 0, 0];

            drawnow;

            app.compute_kernel(false);
            app.renderLamp.Color = [0, 1, 0];
            drawnow;
        end

        % Value changed function: DxEditField
        function DxEditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end
            value = app.DxEditField.Value;

            x_shift = floor(app.Nx * value);
            app.DX = x_shift;
        end

        % Value changed function: DyEditField
        function DyEditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end
            value = app.DyEditField.Value;

            y_shift = floor(app.Ny * value);
            app.DY = y_shift;
        end

        % Callback function
        function compositef1EditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end
            %
            %             color_f1 = app.compositef1EditField.Value;
            %             color_f2 = app.compositef2EditField.Value;
            %             color_f3 = app.compositef3EditField.Value;

            %             if ~app.showSpatialFilterCheckBox.Value
            %                 app.LowfrequencyrangeLabel.Text = sprintf('Low frequency range: %d..%d', color_f1, color_f2);
            %                 app.HighfrequencyrangeLabel.Text = sprintf('High frequency range: %d..%d', color_f2, color_f3);
            %             else
            %                 app.LowfrequencyrangeLabel.Text = sprintf('Low frequency range: %d..%d', color_f2, color_f3);
            %                 app.HighfrequencyrangeLabel.Text = sprintf('High frequency range: %d..%d', color_f1, color_f2);
            %             end
        end

        % Callback function
        function compositef2EditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end
            %
            %             color_f1 = app.compositef1EditField.Value;
            %             color_f2 = app.compositef2EditField.Value;
            %             color_f3 = app.compositef3EditField.Value;

            %             if ~app.showSpatialFilterCheckBox.Value
            %                 app.LowfrequencyrangeLabel.Text = sprintf('Low frequency range: %d..%d', color_f1, color_f2);
            %                 app.HighfrequencyrangeLabel.Text = sprintf('High frequency range: %d..%d', color_f2, color_f3);
            %             else
            %                 app.LowfrequencyrangeLabel.Text = sprintf('Low frequency range: %d..%d', color_f2, color_f3);
            %                 app.HighfrequencyrangeLabel.Text = sprintf('High frequency range: %d..%d', color_f1, color_f2);
            %             end
        end

        % Value changed function: compositef3EditField
        function compositef3EditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            % color_f1 = app.compositef1EditField.Value;
            % color_f2 = app.compositef2EditField.Value;
            % color_f3 = app.compositef3EditField.Value;

            %             if ~app.showSpatialFilterCheckBox.Value
            %                 app.LowfrequencyrangeLabel.Text = sprintf('Low frequency range: %d..%d', color_f1, color_f2);
            %                 app.HighfrequencyrangeLabel.Text = sprintf('High frequency range: %d..%d', color_f2, color_f3);
            %             else
            %                 app.LowfrequencyrangeLabel.Text = sprintf('Low frequency range: %d..%d', color_f2, color_f3);
            %                 app.HighfrequencyrangeLabel.Text = sprintf('High frequency range: %d..%d', color_f1, color_f2);
            %             end
        end

        % Value changed function: showSpatialFilterCheckBox
        function showSpatialFilterCheckBoxValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            % color_f1 = app.compositef1EditField.Value;
            % color_f2 = app.compositef2EditField.Value;
            % color_f3 = app.compositef3EditField.Value;

            %             if ~app.showSpatialFilterCheckBox.Value
            %                 app.LowfrequencyrangeLabel.Text = sprintf('Low frequency range: %d..%d', color_f1, color_f2);
            %                 app.HighfrequencyrangeLabel.Text = sprintf('High frequency range: %d..%d', color_f2, color_f3);
            %             else
            %                 app.LowfrequencyrangeLabel.Text = sprintf('Low frequency range: %d..%d', color_f2, color_f3);
            %                 app.HighfrequencyrangeLabel.Text = sprintf('High frequency range: %d..%d', color_f1, color_f2);
            %             end
        end

        % Value changed function: EditField
        function EditFieldValueChanged(app, event)
            value = app.EditField.Value;
            app.positioninfileSlider.Value = value;app.rephasing_data

            if ~app.file_loaded
                return
            end

            app.frame_batch = app.interferogram_stream.read_frame_batch(app.batchsizeEditField.Value, floor(app.positioninfileSlider.Value));
            app.compute_kernel(false);
        end

        % Value changed function: rephasingCheckBox
        function rephasingCheckBoxValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            if app.rephasingCheckBox.Value
                try
                    [rephasing_data, rephasing_found] = fetch_rephasing_data(app.filepath, app.filename, app.extension);
                catch
                    rephasing_data = [];
                    rephasing_found = false;
                end

                if rephasing_found
                    app.rephasing_data = rephasing_data;

                    app.NotesTextArea.Value = {''};
                    for i = 1:numel(rephasing_data)
                        r = rephasing_data(i);
                        reg = ~isempty(r.aberration_correction.rephasing_zernike_coefs);
                        shack = ~isempty(r.aberration_correction.shack_hartmann_zernike_coefs);
                        opt = ~isempty(r.aberration_correction.iterative_opt_zernike_coefs);
                        text = sprintf('Run %d:\nsize = %d, stride = %d, reg = %s, shack = %s, opt = %s', i, r.batch_size, r.batch_stride, string(reg), string(shack), string(opt));

                        % compute mean correction
                        if shack
                            mean_1 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(1,:));
                            mean_2 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(2,:));
                            mean_3 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(3,:));
                        end

                        if opt
                            mean_1 = mean(r.aberration_correction.iterative_opt_zernike_coefs(1,:));
                            mean_2 = mean(r.aberration_correction.iterative_opt_zernike_coefs(2,:));
                            mean_3 = mean(r.aberration_correction.iterative_opt_zernike_coefs(3,:));
                        end

                        if shack && opt
                            mean_1 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(1,:) + r.aberration_correction.iterative_opt_zernike_coefs(1,:));
                            mean_2 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(2,:) + r.aberration_correction.iterative_opt_zernike_coefs(2,:));
                            mean_3 = mean(r.aberration_correction.shack_hartmann_zernike_coefs(3,:) + r.aberration_correction.iterative_opt_zernike_coefs(3,:));
                        end

                        if shack || opt
                            text = sprintf('%s\nastig 1 = %0.1f, defocus = %0.1f, astig 2 = %0.1f', text, mean_1, mean_2, mean_3);
                        end

                        text = sprintf('%s\n',text);

                        app.NotesTextArea.Value = [{text}; app.NotesTextArea.Value];
                    end
                    app.NotesTextArea.Value = [{'Rephasing found:'}; app.NotesTextArea.Value];
                else
                    app.rephasing_data = [];
                    app.NotesTextArea.Value = {''};
                end
            end
        end

        % Value changed function: ImageChoiceDropDown
        function ImageChoiceDropDownValueChanged(app, event)
            value = app.ImageChoiceDropDown.Value;

            switch value
                case 'power Doppler'
                    app.f1EditField.Visible = true;
                    app.f2EditField.Visible = true;

                    app.compositef1EditField.Visible = false;
                    app.compositef2EditField.Visible = false;
                    app.compositef3EditField.Visible = false;
                    app.compositef3EditFieldLabel.Visible = false;

                    %                     app.LowfrequencyrangeLabel.Visible = false;
                    %                     app.HighfrequencyrangeLabel.Visible = false;

                case 'color Doppler'
                    app.f1EditField.Visible = false;
                    app.f2EditField.Visible = false;

                    app.compositef1EditField.Visible = true;
                    app.compositef2EditField.Visible = true;
                    app.compositef3EditField.Visible = true;
                    app.compositef3EditFieldLabel.Visible = true;

                    %                     app.LowfrequencyrangeLabel.Visible = true;
                    %                     app.HighfrequencyrangeLabel.Visible = true;

                case 'directional Doppler'
                    app.f1EditField.Visible = true;
                    app.f2EditField.Visible = true;

                    app.compositef1EditField.Visible = false;
                    app.compositef2EditField.Visible = false;
                    app.compositef3EditField.Visible = false;
                    app.compositef3EditFieldLabel.Visible = false;

                    %                     app.LowfrequencyrangeLabel.Visible = false;
                    %                     app.HighfrequencyrangeLabel.Visible = false;

                case 'velocity estimate'
                    app.f1EditField.Visible = true;
                    app.f2EditField.Visible = true;

                    app.compositef1EditField.Visible = false;
                    app.compositef2EditField.Visible = false;
                    app.compositef3EditField.Visible = false;
                    app.compositef3EditFieldLabel.Visible = false;

                    %                     app.LowfrequencyrangeLabel.Visible = false;
                    %                     app.HighfrequencyrangeLabel.Visible = false;

                case 'phase variation'
                    app.f1EditField.Visible = true;
                    app.f2EditField.Visible = true;

                    app.compositef1EditField.Visible = false;
                    app.compositef2EditField.Visible = false;
                    app.compositef3EditField.Visible = false;
                    app.compositef3EditFieldLabel.Visible = false;

                    %                     app.LowfrequencyrangeLabel.Visible = false;
                    %                     app.HighfrequencyrangeLabel.Visible = false;

                case 'dark field image'
                    app.f1EditField.Visible = true;
                    app.f2EditField.Visible = true;

                    app.compositef1EditField.Visible = false;
                    app.compositef2EditField.Visible = false;
                    app.compositef3EditField.Visible = false;
                    app.compositef3EditFieldLabel.Visible = false;

                    %                     app.LowfrequencyrangeLabel.Visible = false;
                    %                     app.HighfrequencyrangeLabel.Visible = false;

                case 'spectrogram'
                    app.f1EditField.Visible = true;
                    app.f2EditField.Visible = true;

                    app.compositef1EditField.Visible = false;
                    app.compositef2EditField.Visible = false;
                    app.compositef3EditField.Visible = false;
                    app.compositef3EditFieldLabel.Visible = false;

                    %                     app.LowfrequencyrangeLabel.Visible = false;
                    %                     app.HighfrequencyrangeLabel.Visible = false;
                otherwise
                    % unreachable
            end
        end

        % Value changed function: blurEditField
        function blurEditFieldValueChanged(app, event)
            value = app.blurEditField.Value;
            app.blur = value;

            if ~app.file_loaded
                return
            end
        end

        % Value changed function: spatialTransformationDropDown
        function spatialTransformationChanged(app, event)
            app.compute_kernel(false);
        end

        % Value changed function: setUpDropDown
        function setUpChanged(app, event)
            app.rangeYEditField.Visible = false;
            app.rangeYEditFieldLabel.Visible = false;
            app.rangeZEditField.Visible = false;
            app.rangeZEditFieldLabel.Visible = false;
            app.volumesizeEditField.Visible = false;
            app.volumesizeEditFieldLabel.Visible = false;
            app.outputvideoDropDown.Enable = true;
        end

        % Button pushed function: SaveconfigButton
        function SaveconfigButtonPushed(app, event)
            app.saveconfigLamp.Color = [1, 0, 0];
            drawnow;
            config = GuiCache(app);
            if app.ApplytoallfilesCheckBox.Value
                files = dir(fullfile(app.filepath, '*.holo'));
                files = cat(1, files, dir(fullfile(app.filepath, '*.cine')));
                files = cat(1, files, dir(fullfile(app.filepath, '*.raw')));
                for n = 1:length(files)
                    [~, file_name, ~] = fileparts(files(n).name);
                    file_name = sprintf("%s-config", file_name);
                    [file_name, suffix] = get_last_file_name(app.filepath, file_name, 'mat');
                    save(sprintf('%s%s_%d.mat', app.filepath, file_name, suffix + 1), "config");
                end
            else
                [~, file_name, ~] = fileparts(app.filename);
                file_name = sprintf("%s-config", file_name);
                [file_name, suffix] = get_last_file_name(app.filepath, file_name, 'mat');
                save(sprintf('%s%s_%d.mat', app.filepath, file_name, suffix + 1), "config");
            end
            app.saveconfigLamp.Color = [0, 1, 0];
        end

        % Callback function
        function PCACheckBoxValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            app.PCA.Value = app.PCACheckBox.Value;
            app.PCA.min = app.min_PCAEditField.Value;
            app.PCA.max = app.max_PCAEditField.Value;
        end

        % Value changed function: SubAp_PCACheckBox
        function SubAp_PCACheckBoxValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            app.SubAp_PCA.Value = app.SubAp_PCACheckBox.Value;
            app.SubAp_PCA.min = app.minSubAp_PCAEditField.Value;
            app.SubAp_PCA.max = app.maxSubAp_PCAEditField.Value;
        end

        % Value changed function: minSubAp_PCAEditField
        function minSubApPCAEditField_2ValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            app.SubAp_PCA.min = app.minSubAp_PCAEditField.Value;
        end

        % Value changed function: maxSubAp_PCAEditField
        function maxSubAp_PCAEditField_2_2ValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            app.SubAp_PCA.max = app.maxSubAp_PCAEditField.Value;
        end

        % Value changed function: min_PCAEditField
        function min_PCAEditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            app.time_transform.min_PCA = app.min_PCAEditField.Value;
        end

        % Value changed function: max_PCAEditField
        function max_PCAEditFieldValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            app.time_transform.max_PCA = app.max_PCAEditField.Value;
        end

        % Value changed function: timetransformDropDown
        function TimeTransform(app, event)
            value = app.timetransformDropDown.Value;

            switch value
                case 'FFT'
                    app.time_transform.type = 'FFT';
                    % for now this is range of interest
                    app.time_transform.f1 = app.f1EditField.Value;
                    app.time_transform.f2 = app.f2EditField.Value;

                    app.ImageChoiceDropDown.Visible = true;
                    app.f1EditField.Visible = true;
                    app.f2EditField.Visible = true;
                    app.f1EditFieldLabel.Visible = true;
                    app.f2EditFieldLabel.Visible = true;

                    app.min_PCAEditField.Visible = false;
                    app.max_PCAEditField.Visible = false;
                    app.minEditFieldLabel.Visible = false;
                    app.maxEditFieldLabel.Visible = false;

                    if (strcmp(app.ImageChoiceDropDown.Value, 'color Doppler'))
                        app.f1EditField.Visible = false;
                        app.f2EditField.Visible = false;
                        app.f1EditFieldLabel.Visible = false;
                        app.f2EditFieldLabel.Visible = false;
                        app.compositef1EditField.Visible = true;
                        app.compositef1EditFieldLabel.Visible = true;
                        app.compositef2EditField.Visible = true;
                        app.compositef2EditFieldLabel.Visible = true;
                        app.compositef3EditField.Visible = true;
                        app.compositef3EditFieldLabel.Visible = true;

                        %                         app.LowfrequencyrangeLabel.Visible = true;
                        %                         app.HighfrequencyrangeLabel.Visible = true;
                    end

                case 'PCA'
                    app.time_transform.type = 'PCA';
                    app.time_transform.min_PCA = app.min_PCAEditField.Value;
                    app.time_transform.max_PCA = app.max_PCAEditField.Value;

                    app.ImageChoiceDropDown.Visible = false;
                    app.f1EditField.Visible = false;
                    app.f2EditField.Visible = false;
                    app.f1EditFieldLabel.Visible = false;
                    app.f2EditFieldLabel.Visible = false;

                    app.min_PCAEditField.Visible = true;
                    app.max_PCAEditField.Visible = true;
                    app.minEditFieldLabel.Visible = true;
                    app.maxEditFieldLabel.Visible = true;

                    app.compositef1EditField.Visible = false;
                    app.compositef2EditField.Visible = false;
                    app.compositef3EditField.Visible = false;
                    app.compositef3EditFieldLabel.Visible = false;

                    %                     app.LowfrequencyrangeLabel.Visible = false;
                    %                     app.HighfrequencyrangeLabel.Visible = false;
            end
        end

        % Value changed function: Switch
        function ZSwitchValueChanged(app, event)
            if ~app.file_loaded
                return
            end

            if app.Switch.Value == "z_iris"
                app.z_reconstruction = app.zirisEditField.Value;
            else
                app.z_reconstruction = app.zretinaEditField.Value;
            end

            app.compute_kernel(false);
        end

        % Value changed function: zirisEditField
        function zirisEditFieldValueChanged(app, event)
            zChanged(app);
        end

        % Value changed function: outputvideoDropDown
        function outputVideo(app, event)
            value = app.outputvideoDropDown.Value;
            if strcmp(value,'dark field')
                app.Switch.Value = 'z_retina';
                ZSwitchValueChanged(app, event);
            end
        end

        % Button pushed function: RenderpreviewButton
        function RenderpreviewButtonPushed(app, event)
            Renderpreview(app);
        end

        % Window key press function: HoloDopplerUIFigure
        function HoloDopplerUIFigureWindowKeyPress(app, event)
            switch event.Key
                case 'return'
                    app.RenderpreviewButtonPushed();
            end
        end

        % Button pushed function: FoldermanagementButton
        function FoldermanagementButtonPushed(app, event)
            d = dialog('Position', [300, 300, 750, 90 + length(app.drawer_list) * 14],...
                'Color', [0.2, 0.2, 0.2],...
                'Name', 'Folder management',...
                'Resize', 'on',...
                'WindowStyle', 'normal');

            txt = uicontrol('Parent', d,...
                'Style', 'text',...
                'FontName', 'Helvetica',...
                'BackgroundColor', [0.2, 0.2, 0.2],...
                'ForegroundColor', [0.8, 0.8, 0.8],...
                'Position', [20, 70, 710, length(app.drawer_list) * 14],...
                'HorizontalAlignment', 'left',...
                'String', app.drawer_list);

            uicontrol('Parent', d,...
                'Position', [20, 20, 100, 25],...
                'FontName', 'Helvetica',...
                'BackgroundColor', [0.5, 0.5, 0.5],...
                'ForegroundColor', [0.9 0.9 0.9],...
                'FontWeight', 'bold',...
                'String', 'Select folder',...
                'Callback', @select);

            uicontrol('Parent', d,...
                'Position', [140, 20, 100, 25],...
                'FontName', 'Helvetica',...
                'BackgroundColor', [0.5, 0.5, 0.5],...
                'ForegroundColor', [0.9 0.9 0.9],...
                'FontWeight', 'bold',...
                'String', 'Clear list',...
                'Callback', @clear_drawer);

            uicontrol('Parent', d,...
                'Position', [260, 20, 100, 25],...
                'FontName', 'Helvetica',...
                'BackgroundColor', [0.5, 0.5, 0.5],...
                'ForegroundColor', [0.9 0.9 0.9],...
                'FontWeight', 'bold',...
                'String', 'Render',...
                'Callback', @render);

            uiwait(d);

            function select(~, ~)
                selected_dir = uigetdir();
                if (selected_dir)
                    app.drawer_list{end + 1} = strcat(selected_dir, '\');
                end
                txt.String = app.drawer_list;
                d.Position(4) = 100 + length(app.drawer_list) * 14;
                txt.Position(4) = length(app.drawer_list) * 14;
            end

            function clear_drawer(~, ~)
                app.drawer_list = {};
                txt.String = app.drawer_list;
                d.Position(4) = 100 + length(app.drawer_list) * 14;
                txt.Position(4) = length(app.drawer_list) * 14;
            end

            function render(~, ~)
                file_list = {};
                for it_1 = 1:length(app.drawer_list) % Circles through the folders added by the user
                    FolderInfo = dir(app.drawer_list{it_1});
                    for it_2 = 1:length(FolderInfo) % Circles through the files of said folder
                        if (regexp(FolderInfo(it_2).name, "^[A-Za-z0-9_]+\.(holo|cine|raw)$")) % If the file is processable
                            config_list = get_all_config_file(app.drawer_list{it_1}, FolderInfo(it_2).name); % Get config files
                            if (~isempty(config_list))
                                file_list{end + 1} = {app.drawer_list{it_1}, FolderInfo(it_2).name, config_list}; %#ok<AGROW>
                            end
                        end
                    end
                end

                for i = 1:length(file_list)
                    if (~isempty(file_list{i}{3}))
                        for j = 1:length(file_list{i}{3})
                            config = load(fullfile(file_list{i}{1}, file_list{i}{3}{j}));
                            Loadfile(app,file_list{i}{2}, file_list{i}{1}, config.config);
                            app.ImagerenderingButtonPushed();
                        end
                    end
                end
            end
            delete(d);
        end

        % Button pushed function: SavepreviewButton
        function SavePreview(app, event)
            Savepreview(app);
        end

        % Value changed function: SVDThresholdCheckBox
        function SVDThresholdCheckBoxValueChanged(app, event)
            
            if app.SVDThresholdCheckBox.Value
                app.SVDThresholdEditField.Enable = true;
                
                app.SVDThresholdEditField.Value = round(app.f1EditField.Value * app.batchsizeEditField.Value / app.fsEditField.Value)*2 + 1;
            else
                app.SVDThresholdEditField.Enable = false;
            end
            
            
            
        end

        % Value changed function: rangeZEditField
        function rangeZEditFieldValueChanged(app, event)
            value = app.rangeZEditField.Value;
            
        end

        % Value changed function: rangeYEditField
        function rangeYEditFieldValueChanged(app, event)
            value = app.rangeYEditField.Value;
            
        end

        % Image clicked function: ImageLeft
        function ImageLeftClicked(app, event)
            figure(332)
            imshow(app.ImageLeft.ImageSource);
            h=drawfreehand();
            try
                app.mask = createMask(h);
            end
        end

        % Image clicked function: ImageRight
        function ImageRightClicked(app, event)
            
        end

        % Value changed function: imageregistrationCheckBox
        function imageregistrationCheckBoxValueChanged(app, event)
            value = app.imageregistrationCheckBox.Value;
            app.refbatchsizeEditField.Enable = value;
        end

        % Button pushed function: ShowSpectrumButton
        function ShowSpectrumButtonPushed(app, event)
            Show_spectrum(app);
        end

        % Value changed function: SVDThresholdEditField
        function SVDThresholdEditFieldValueChanged(app, event)
            value = app.SVDThresholdEditField.Value;
            if value > app.batchsizeEditField.Value 
                app.SVDThresholdEditField.Value = app.batchsizeEditField.Value ;
                disp("SVD Threshold should be smaller than the batch size.")
            end
        end

        % Button pushed function: scan3D
        function scan3DButtonPushed(app, event)
            Show_3D_scan(app);
        end

        % Value changed function: regDiscRatioEditField, 
        % ...and 1 other component
        function registrationdiscCheckBoxValueChanged(app, event)
            value = app.registrationdiscCheckBox.Value;
            show_ref_disc(app,value);
        end

        % Value changed function: spatialfilterratio
        function spatialfilterratioValueChanged(app, event)
            app.spatial_filter_mask = diskMask(app.Nx, app.Ny, app.spatialfilterratio.Value);
        end

        % Value changed function: ppx, ppy
        function ppxValueChanged(app, event)
            app.pix_height = app.ppy.Value;
            app.pix_width = app.ppx.Value;
            zChanged(app);
        end
    end

    % Component initialization
    methods (Access = private)

        % Create UIFigure and components
        function createComponents(app)

            % Get the file path for locating images
            pathToMLAPP = fileparts(mfilename('fullpath'));

            % Create HoloDopplerUIFigure and hide until all components are created
            app.HoloDopplerUIFigure = uifigure('Visible', 'off');
            app.HoloDopplerUIFigure.Color = [0.149 0.149 0.149];
            app.HoloDopplerUIFigure.Position = [210 56 1260 900];
            app.HoloDopplerUIFigure.Name = 'HoloDoppler';
            app.HoloDopplerUIFigure.Icon = fullfile(pathToMLAPP, 'holowaves_logo_temp.png');
            app.HoloDopplerUIFigure.CloseRequestFcn = createCallbackFcn(app, @HoloDopplerUIFigureCloseRequest, true);
            app.HoloDopplerUIFigure.WindowKeyPressFcn = createCallbackFcn(app, @HoloDopplerUIFigureWindowKeyPress, true);

            % Create GridLayout4
            app.GridLayout4 = uigridlayout(app.HoloDopplerUIFigure);
            app.GridLayout4.ColumnWidth = {'1.2x', '2x', '2x'};
            app.GridLayout4.RowHeight = {'1x', 420};
            app.GridLayout4.RowSpacing = 5;
            app.GridLayout4.Padding = [0 3.20001220703125 0 3.20001220703125];
            app.GridLayout4.BackgroundColor = [0.2 0.2 0.2];

            % Create FileselectionPanel
            app.FileselectionPanel = uipanel(app.GridLayout4);
            app.FileselectionPanel.Tooltip = {'Select a reconstruction algorithm that minimizes memory footprint during post processing'};
            app.FileselectionPanel.ForegroundColor = [0.8 0.8 0.8];
            app.FileselectionPanel.TitlePosition = 'centertop';
            app.FileselectionPanel.Title = 'File selection';
            app.FileselectionPanel.BackgroundColor = [0.2 0.2 0.2];
            app.FileselectionPanel.Layout.Row = [1 2];
            app.FileselectionPanel.Layout.Column = 1;

            % Create VideorenderingPanel
            app.VideorenderingPanel = uipanel(app.FileselectionPanel);
            app.VideorenderingPanel.ForegroundColor = [0.902 0.902 0.902];
            app.VideorenderingPanel.Title = 'Video rendering';
            app.VideorenderingPanel.BackgroundColor = [0.2 0.2 0.2];
            app.VideorenderingPanel.Position = [10 237 244 433];

            % Create rephasingCheckBox
            app.rephasingCheckBox = uicheckbox(app.VideorenderingPanel);
            app.rephasingCheckBox.ValueChangedFcn = createCallbackFcn(app, @rephasingCheckBoxValueChanged, true);
            app.rephasingCheckBox.Text = 'rephasing';
            app.rephasingCheckBox.FontColor = [0.902 0.902 0.902];
            app.rephasingCheckBox.Position = [38 106 75 22];
            app.rephasingCheckBox.Value = true;

            % Create outputvideoDropDownLabel
            app.outputvideoDropDownLabel = uilabel(app.VideorenderingPanel);
            app.outputvideoDropDownLabel.HorizontalAlignment = 'right';
            app.outputvideoDropDownLabel.FontColor = [0.902 0.902 0.902];
            app.outputvideoDropDownLabel.Position = [29 382 71 22];
            app.outputvideoDropDownLabel.Text = 'output video';

            % Create outputvideoDropDown
            app.outputvideoDropDown = uidropdown(app.VideorenderingPanel);
            app.outputvideoDropDown.Items = {'power Doppler', 'moments', 'all videos', 'choroid'};
            app.outputvideoDropDown.ValueChangedFcn = createCallbackFcn(app, @outputVideo, true);
            app.outputvideoDropDown.FontColor = [0.9412 0.9412 0.9412];
            app.outputvideoDropDown.BackgroundColor = [0.502 0.502 0.502];
            app.outputvideoDropDown.Position = [111 381 112 23];
            app.outputvideoDropDown.Value = 'moments';

            % Create phaseregistrationCheckBox
            app.phaseregistrationCheckBox = uicheckbox(app.VideorenderingPanel);
            app.phaseregistrationCheckBox.Visible = 'off';
            app.phaseregistrationCheckBox.Tooltip = {'Activates video registration. Check this if the video is too shaky.'};
            app.phaseregistrationCheckBox.Text = 'phase registration';
            app.phaseregistrationCheckBox.FontColor = [0.902 0.902 0.902];
            app.phaseregistrationCheckBox.Position = [119 106 117 22];

            % Create temporalfilterCheckBox
            app.temporalfilterCheckBox = uicheckbox(app.VideorenderingPanel);
            app.temporalfilterCheckBox.Text = 'temporal filter';
            app.temporalfilterCheckBox.FontColor = [0.902 0.902 0.902];
            app.temporalfilterCheckBox.Position = [38 45 95 22];

            % Create temporalfilterEditField
            app.temporalfilterEditField = uieditfield(app.VideorenderingPanel, 'numeric');
            app.temporalfilterEditField.Limits = [1 Inf];
            app.temporalfilterEditField.FontColor = [0.8 0.8 0.8];
            app.temporalfilterEditField.BackgroundColor = [0.149 0.149 0.149];
            app.temporalfilterEditField.Tooltip = {'Laser wavelength in nanometers'};
            app.temporalfilterEditField.Position = [141 44 54 22];
            app.temporalfilterEditField.Value = 2;

            % Create FoldermanagementButton
            app.FoldermanagementButton = uibutton(app.VideorenderingPanel, 'push');
            app.FoldermanagementButton.ButtonPushedFcn = createCallbackFcn(app, @FoldermanagementButtonPushed, true);
            app.FoldermanagementButton.BackgroundColor = [0.502 0.502 0.502];
            app.FoldermanagementButton.FontColor = [0.902 0.902 0.902];
            app.FoldermanagementButton.Position = [5 313 123 23];
            app.FoldermanagementButton.Text = 'Folder management';

            % Create ImagerenderingButton
            app.ImagerenderingButton = uibutton(app.VideorenderingPanel, 'push');
            app.ImagerenderingButton.ButtonPushedFcn = createCallbackFcn(app, @ImagerenderingButtonPushed, true);
            app.ImagerenderingButton.BackgroundColor = [0.502 0.502 0.502];
            app.ImagerenderingButton.FontColor = [0.902 0.902 0.902];
            app.ImagerenderingButton.Position = [135 312 103 23];
            app.ImagerenderingButton.Text = 'Image rendering';

            % Create ApplytoallfilesCheckBox
            app.ApplytoallfilesCheckBox = uicheckbox(app.VideorenderingPanel);
            app.ApplytoallfilesCheckBox.Text = 'Apply to all files';
            app.ApplytoallfilesCheckBox.FontColor = [0.9412 0.9412 0.9412];
            app.ApplytoallfilesCheckBox.Position = [118 349 105 22];

            % Create saveconfigLamp
            app.saveconfigLamp = uilamp(app.VideorenderingPanel);
            app.saveconfigLamp.Position = [226 355 12 12];

            % Create iterativeregistrationCheckBox
            app.iterativeregistrationCheckBox = uicheckbox(app.VideorenderingPanel);
            app.iterativeregistrationCheckBox.Tooltip = {'''Activates video registration. Check this if the video is too shaky.'''};
            app.iterativeregistrationCheckBox.Text = 'iterative registration';
            app.iterativeregistrationCheckBox.FontColor = [0.902 0.902 0.902];
            app.iterativeregistrationCheckBox.Position = [38 66 131 22];

            % Create showrefCheckBox
            app.showrefCheckBox = uicheckbox(app.VideorenderingPanel);
            app.showrefCheckBox.Text = 'show ref';
            app.showrefCheckBox.FontColor = [0.902 0.902 0.902];
            app.showrefCheckBox.Position = [38 25 67 22];

            % Create SaveconfigButton
            app.SaveconfigButton = uibutton(app.VideorenderingPanel, 'push');
            app.SaveconfigButton.ButtonPushedFcn = createCallbackFcn(app, @SaveconfigButtonPushed, true);
            app.SaveconfigButton.BackgroundColor = [0.502 0.502 0.502];
            app.SaveconfigButton.FontColor = [0.902 0.902 0.902];
            app.SaveconfigButton.Position = [7 348 100 22];
            app.SaveconfigButton.Text = 'Save config';

            % Create imageregistrationCheckBox
            app.imageregistrationCheckBox = uicheckbox(app.VideorenderingPanel);
            app.imageregistrationCheckBox.ValueChangedFcn = createCallbackFcn(app, @imageregistrationCheckBoxValueChanged, true);
            app.imageregistrationCheckBox.Text = 'image registration';
            app.imageregistrationCheckBox.FontColor = [0.902 0.902 0.902];
            app.imageregistrationCheckBox.Position = [38 85 117 22];
            app.imageregistrationCheckBox.Value = true;

            % Create batchstrideEditFieldLabel
            app.batchstrideEditFieldLabel = uilabel(app.VideorenderingPanel);
            app.batchstrideEditFieldLabel.HorizontalAlignment = 'center';
            app.batchstrideEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.batchstrideEditFieldLabel.Position = [12 246 84 22];
            app.batchstrideEditFieldLabel.Text = 'batch stride';

            % Create batchstrideEditField
            app.batchstrideEditField = uieditfield(app.VideorenderingPanel, 'numeric');
            app.batchstrideEditField.Limits = [1 Inf];
            app.batchstrideEditField.ValueDisplayFormat = '%.0f';
            app.batchstrideEditField.FontColor = [0.8 0.8 0.8];
            app.batchstrideEditField.BackgroundColor = [0.149 0.149 0.149];
            app.batchstrideEditField.Tooltip = {'Number of interferograms to skip between two images. Increase for a shorter video.'};
            app.batchstrideEditField.Position = [95 246 100 22];
            app.batchstrideEditField.Value = 512;

            % Create DxEditFieldLabel
            app.DxEditFieldLabel = uilabel(app.VideorenderingPanel);
            app.DxEditFieldLabel.HorizontalAlignment = 'center';
            app.DxEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.DxEditFieldLabel.Position = [39 215 25 22];
            app.DxEditFieldLabel.Text = 'Dx';

            % Create DxEditField
            app.DxEditField = uieditfield(app.VideorenderingPanel, 'numeric');
            app.DxEditField.Limits = [-1 1.01];
            app.DxEditField.ValueChangedFcn = createCallbackFcn(app, @DxEditFieldValueChanged, true);
            app.DxEditField.FontColor = [0.8 0.8 0.8];
            app.DxEditField.BackgroundColor = [0.149 0.149 0.149];
            app.DxEditField.Tooltip = {''};
            app.DxEditField.Position = [95 215 100 22];

            % Create DyEditFieldLabel
            app.DyEditFieldLabel = uilabel(app.VideorenderingPanel);
            app.DyEditFieldLabel.HorizontalAlignment = 'center';
            app.DyEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.DyEditFieldLabel.Position = [39 182 25 22];
            app.DyEditFieldLabel.Text = 'Dy';

            % Create DyEditField
            app.DyEditField = uieditfield(app.VideorenderingPanel, 'numeric');
            app.DyEditField.Limits = [-1 1.01];
            app.DyEditField.ValueChangedFcn = createCallbackFcn(app, @DyEditFieldValueChanged, true);
            app.DyEditField.FontColor = [0.8 0.8 0.8];
            app.DyEditField.BackgroundColor = [0.149 0.149 0.149];
            app.DyEditField.Tooltip = {''};
            app.DyEditField.Position = [95 182 100 22];

            % Create refbatchsizeEditFieldLabel
            app.refbatchsizeEditFieldLabel = uilabel(app.VideorenderingPanel);
            app.refbatchsizeEditFieldLabel.HorizontalAlignment = 'center';
            app.refbatchsizeEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.refbatchsizeEditFieldLabel.Position = [10 276 77 22];
            app.refbatchsizeEditFieldLabel.Text = 'ref batch size';

            % Create refbatchsizeEditField
            app.refbatchsizeEditField = uieditfield(app.VideorenderingPanel, 'numeric');
            app.refbatchsizeEditField.Limits = [1 Inf];
            app.refbatchsizeEditField.FontColor = [0.8 0.8 0.8];
            app.refbatchsizeEditField.BackgroundColor = [0.149 0.149 0.149];
            app.refbatchsizeEditField.Tooltip = {'Number of interferograms used to generate a single image. Increase value for better video quality.'};
            app.refbatchsizeEditField.Position = [95 276 100 22];
            app.refbatchsizeEditField.Value = 1024;

            % Create registrationdiscCheckBox
            app.registrationdiscCheckBox = uicheckbox(app.VideorenderingPanel);
            app.registrationdiscCheckBox.ValueChangedFcn = createCallbackFcn(app, @registrationdiscCheckBoxValueChanged, true);
            app.registrationdiscCheckBox.Text = 'registration disc';
            app.registrationdiscCheckBox.FontColor = [0.902 0.902 0.902];
            app.registrationdiscCheckBox.Position = [38 4 106 22];
            app.registrationdiscCheckBox.Value = true;

            % Create regDiscRatioEditField
            app.regDiscRatioEditField = uieditfield(app.VideorenderingPanel, 'numeric');
            app.regDiscRatioEditField.Limits = [0 1000];
            app.regDiscRatioEditField.ValueChangedFcn = createCallbackFcn(app, @registrationdiscCheckBoxValueChanged, true);
            app.regDiscRatioEditField.FontColor = [0.8 0.8 0.8];
            app.regDiscRatioEditField.BackgroundColor = [0.149 0.149 0.149];
            app.regDiscRatioEditField.Tooltip = {'Laser wavelength in nanometers'};
            app.regDiscRatioEditField.Position = [184 4 54 22];
            app.regDiscRatioEditField.Value = 0.7;

            % Create DxEditFieldLabel_2
            app.DxEditFieldLabel_2 = uilabel(app.VideorenderingPanel);
            app.DxEditFieldLabel_2.HorizontalAlignment = 'center';
            app.DxEditFieldLabel_2.FontColor = [0.8 0.8 0.8];
            app.DxEditFieldLabel_2.Position = [153 4 28 22];
            app.DxEditFieldLabel_2.Text = 'ratio';

            % Create LoadfileButton
            app.LoadfileButton = uibutton(app.FileselectionPanel, 'push');
            app.LoadfileButton.ButtonPushedFcn = createCallbackFcn(app, @LoadfileButtonPushed, true);
            app.LoadfileButton.BackgroundColor = [0.502 0.502 0.502];
            app.LoadfileButton.FontColor = [0.902 0.902 0.902];
            app.LoadfileButton.Position = [30 837 100 22];
            app.LoadfileButton.Text = 'Load file';

            % Create wavelengthEditFieldLabel
            app.wavelengthEditFieldLabel = uilabel(app.FileselectionPanel);
            app.wavelengthEditFieldLabel.HorizontalAlignment = 'center';
            app.wavelengthEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.wavelengthEditFieldLabel.Position = [40 771 84 22];
            app.wavelengthEditFieldLabel.Text = 'wavelength';

            % Create wavelengthEditField
            app.wavelengthEditField = uieditfield(app.FileselectionPanel, 'numeric');
            app.wavelengthEditField.Limits = [0 Inf];
            app.wavelengthEditField.ValueChangedFcn = createCallbackFcn(app, @wavelengthEditFieldValueChanged, true);
            app.wavelengthEditField.FontColor = [0.8 0.8 0.8];
            app.wavelengthEditField.BackgroundColor = [0.149 0.149 0.149];
            app.wavelengthEditField.Tooltip = {'Laser wavelength in nanometers'};
            app.wavelengthEditField.Position = [123 772 100 22];
            app.wavelengthEditField.Value = 8.52e-07;

            % Create ParallelismDropDown
            app.ParallelismDropDown = uidropdown(app.FileselectionPanel);
            app.ParallelismDropDown.Items = {'CPU multithread', 'LightGPU', 'GPU parallelization', 'CPU singlethread', 'CPU/GPU rendering/optim'};
            app.ParallelismDropDown.FontColor = [0.9412 0.9412 0.9412];
            app.ParallelismDropDown.BackgroundColor = [0.502 0.502 0.502];
            app.ParallelismDropDown.Position = [29 712 124 22];
            app.ParallelismDropDown.Value = 'CPU multithread';

            % Create fsEditFieldLabel
            app.fsEditFieldLabel = uilabel(app.FileselectionPanel);
            app.fsEditFieldLabel.HorizontalAlignment = 'right';
            app.fsEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.fsEditFieldLabel.Position = [63 799 21 22];
            app.fsEditFieldLabel.Text = 'fs';

            % Create fsEditField
            app.fsEditField = uieditfield(app.FileselectionPanel, 'numeric');
            app.fsEditField.Limits = [0 Inf];
            app.fsEditField.Editable = 'off';
            app.fsEditField.FontColor = [0.8 0.8 0.8];
            app.fsEditField.BackgroundColor = [0.149 0.149 0.149];
            app.fsEditField.Tooltip = {'Sampling frequency (kHz)'};
            app.fsEditField.Position = [123 799 100 22];
            app.fsEditField.Value = 75;

            % Create NotesTextAreaLabel
            app.NotesTextAreaLabel = uilabel(app.FileselectionPanel);
            app.NotesTextAreaLabel.BackgroundColor = [0.2 0.2 0.2];
            app.NotesTextAreaLabel.HorizontalAlignment = 'right';
            app.NotesTextAreaLabel.FontColor = [0.8 0.8 0.8];
            app.NotesTextAreaLabel.Position = [10 204 37 22];
            app.NotesTextAreaLabel.Text = 'Notes';

            % Create NotesTextArea
            app.NotesTextArea = uitextarea(app.FileselectionPanel);
            app.NotesTextArea.FontColor = [0.8 0.8 0.8];
            app.NotesTextArea.BackgroundColor = [0.149 0.149 0.149];
            app.NotesTextArea.Position = [10 87 244 119];

            % Create numworkersSpinnerLabel
            app.numworkersSpinnerLabel = uilabel(app.FileselectionPanel);
            app.numworkersSpinnerLabel.HorizontalAlignment = 'right';
            app.numworkersSpinnerLabel.FontColor = [0.902 0.902 0.902];
            app.numworkersSpinnerLabel.Position = [26 681 74 22];
            app.numworkersSpinnerLabel.Text = 'num workers';

            % Create numworkersSpinner
            app.numworkersSpinner = uispinner(app.FileselectionPanel);
            app.numworkersSpinner.Limits = [-1 32];
            app.numworkersSpinner.FontColor = [0.8 0.8 0.8];
            app.numworkersSpinner.BackgroundColor = [0.149 0.149 0.149];
            app.numworkersSpinner.Position = [109 681 103 22];
            app.numworkersSpinner.Value = 8;

            % Create Label
            app.Label = uilabel(app.FileselectionPanel);
            app.Label.HorizontalAlignment = 'right';
            app.Label.FontColor = [0.902 0.902 0.902];
            app.Label.Position = [122 206 25 22];
            app.Label.Text = '';

            % Create setUpDropDown
            app.setUpDropDown = uidropdown(app.FileselectionPanel);
            app.setUpDropDown.Items = {'Doppler'};
            app.setUpDropDown.ValueChangedFcn = createCallbackFcn(app, @setUpChanged, true);
            app.setUpDropDown.FontColor = [0.902 0.902 0.902];
            app.setUpDropDown.BackgroundColor = [0.502 0.502 0.502];
            app.setUpDropDown.Position = [164 837 90 22];
            app.setUpDropDown.Value = 'Doppler';

            % Create ppy
            app.ppy = uieditfield(app.FileselectionPanel, 'numeric');
            app.ppy.Limits = [0 10];
            app.ppy.ValueChangedFcn = createCallbackFcn(app, @ppxValueChanged, true);
            app.ppy.FontColor = [0.8 0.8 0.8];
            app.ppy.BackgroundColor = [0.149 0.149 0.149];
            app.ppy.Tooltip = {'Number of frequencies intervals you want to have the M0 of.'};
            app.ppy.Position = [211 744 62 22];

            % Create wavelengthEditFieldLabel_2
            app.wavelengthEditFieldLabel_2 = uilabel(app.FileselectionPanel);
            app.wavelengthEditFieldLabel_2.HorizontalAlignment = 'center';
            app.wavelengthEditFieldLabel_2.FontColor = [0.8 0.8 0.8];
            app.wavelengthEditFieldLabel_2.Position = [45 743 84 22];
            app.wavelengthEditFieldLabel_2.Text = 'pp x y';

            % Create ppx
            app.ppx = uieditfield(app.FileselectionPanel, 'numeric');
            app.ppx.Limits = [0 10];
            app.ppx.ValueChangedFcn = createCallbackFcn(app, @ppxValueChanged, true);
            app.ppx.FontColor = [0.8 0.8 0.8];
            app.ppx.BackgroundColor = [0.149 0.149 0.149];
            app.ppx.Tooltip = {'Number of frequencies intervals you want to have the M0 of.'};
            app.ppx.Position = [128 744 67 22];

            % Create CurrentFilePanel
            app.CurrentFilePanel = uipanel(app.GridLayout4);
            app.CurrentFilePanel.Tooltip = {''};
            app.CurrentFilePanel.ForegroundColor = [0.8 0.8 0.8];
            app.CurrentFilePanel.Title = 'Current file';
            app.CurrentFilePanel.BackgroundColor = [0.2 0.2 0.2];
            app.CurrentFilePanel.Layout.Row = 2;
            app.CurrentFilePanel.Layout.Column = [2 3];

            % Create GridLayout
            app.GridLayout = uigridlayout(app.CurrentFilePanel);
            app.GridLayout.ColumnWidth = {'1x', '1x', '1x'};
            app.GridLayout.RowHeight = {'0.8x'};
            app.GridLayout.BackgroundColor = [0.2 0.2 0.2];

            % Create AdvancedProcessingPanel
            app.AdvancedProcessingPanel = uipanel(app.GridLayout);
            app.AdvancedProcessingPanel.ForegroundColor = [0.902 0.902 0.902];
            app.AdvancedProcessingPanel.Title = 'Advanced Processing';
            app.AdvancedProcessingPanel.BackgroundColor = [0.2 0.2 0.2];
            app.AdvancedProcessingPanel.Layout.Row = 1;
            app.AdvancedProcessingPanel.Layout.Column = 2;

            % Create SVDCheckBox
            app.SVDCheckBox = uicheckbox(app.AdvancedProcessingPanel);
            app.SVDCheckBox.Tooltip = {'Enable SVD hologram filtering in hologram construction'};
            app.SVDCheckBox.Text = 'SVD';
            app.SVDCheckBox.FontColor = [0.902 0.902 0.902];
            app.SVDCheckBox.Position = [21 317 47 22];
            app.SVDCheckBox.Value = true;

            % Create spatialCheckBox
            app.spatialCheckBox = uicheckbox(app.AdvancedProcessingPanel);
            app.spatialCheckBox.Text = 'spatial';
            app.spatialCheckBox.FontColor = [0.8 0.8 0.8];
            app.spatialCheckBox.Position = [19 234 92 22];

            % Create temporalCheckBox
            app.temporalCheckBox = uicheckbox(app.AdvancedProcessingPanel);
            app.temporalCheckBox.Text = 'temporal';
            app.temporalCheckBox.FontColor = [0.8 0.8 0.8];
            app.temporalCheckBox.Position = [19 261 87 23];

            % Create LocalfilteringLabel
            app.LocalfilteringLabel = uilabel(app.AdvancedProcessingPanel);
            app.LocalfilteringLabel.FontColor = [0.8 0.8 0.8];
            app.LocalfilteringLabel.Position = [19 285 83 22];
            app.LocalfilteringLabel.Text = 'Local filtering';

            % Create phi1EditFieldLabel
            app.phi1EditFieldLabel = uilabel(app.AdvancedProcessingPanel);
            app.phi1EditFieldLabel.HorizontalAlignment = 'right';
            app.phi1EditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.phi1EditFieldLabel.Position = [102 258 28 22];
            app.phi1EditFieldLabel.Text = 'phi1';

            % Create phi1EditField
            app.phi1EditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.phi1EditField.Position = [134 258 21 21];

            % Create phi2EditFieldLabel
            app.phi2EditFieldLabel = uilabel(app.AdvancedProcessingPanel);
            app.phi2EditFieldLabel.HorizontalAlignment = 'right';
            app.phi2EditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.phi2EditFieldLabel.Position = [173 261 28 22];
            app.phi2EditFieldLabel.Text = 'phi2';

            % Create phi2EditField
            app.phi2EditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.phi2EditField.Position = [205 261 21 21];

            % Create nu1EditFieldLabel
            app.nu1EditFieldLabel = uilabel(app.AdvancedProcessingPanel);
            app.nu1EditFieldLabel.HorizontalAlignment = 'right';
            app.nu1EditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.nu1EditFieldLabel.Position = [107 230 26 22];
            app.nu1EditFieldLabel.Text = 'nu1';

            % Create nu1EditField
            app.nu1EditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.nu1EditField.Position = [135 230 21 21];

            % Create nu2EditFieldLabel
            app.nu2EditFieldLabel = uilabel(app.AdvancedProcessingPanel);
            app.nu2EditFieldLabel.HorizontalAlignment = 'right';
            app.nu2EditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.nu2EditFieldLabel.Position = [175 230 26 22];
            app.nu2EditFieldLabel.Text = 'nu2';

            % Create nu2EditField
            app.nu2EditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.nu2EditField.FontColor = [0.149 0.149 0.149];
            app.nu2EditField.Position = [205 230 21 21];

            % Create unitcellsinlatticeEditFieldLabel
            app.unitcellsinlatticeEditFieldLabel = uilabel(app.AdvancedProcessingPanel);
            app.unitcellsinlatticeEditFieldLabel.HorizontalAlignment = 'right';
            app.unitcellsinlatticeEditFieldLabel.FontColor = [0.902 0.902 0.902];
            app.unitcellsinlatticeEditFieldLabel.Position = [18 170 110 22];
            app.unitcellsinlatticeEditFieldLabel.Text = '# unit cells in lattice';

            % Create unitcellsinlatticeEditField
            app.unitcellsinlatticeEditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.unitcellsinlatticeEditField.Limits = [0 Inf];
            app.unitcellsinlatticeEditField.Position = [135 170 29 22];
            app.unitcellsinlatticeEditField.Value = 8;

            % Create r1EditFieldLabel
            app.r1EditFieldLabel = uilabel(app.AdvancedProcessingPanel);
            app.r1EditFieldLabel.HorizontalAlignment = 'right';
            app.r1EditFieldLabel.FontColor = [0.902 0.902 0.902];
            app.r1EditFieldLabel.Position = [102 140 25 22];
            app.r1EditFieldLabel.Text = 'r1';

            % Create r1EditField
            app.r1EditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.r1EditField.Limits = [0 Inf];
            app.r1EditField.Position = [135 138 29 23];
            app.r1EditField.Value = 3;

            % Create xystrideEditFieldLabel
            app.xystrideEditFieldLabel = uilabel(app.AdvancedProcessingPanel);
            app.xystrideEditFieldLabel.HorizontalAlignment = 'right';
            app.xystrideEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.xystrideEditFieldLabel.Position = [59 108 50 22];
            app.xystrideEditFieldLabel.Text = 'xy stride';

            % Create xystrideEditField
            app.xystrideEditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.xystrideEditField.Position = [124 105 41 27];
            app.xystrideEditField.Value = 32;

            % Create SVDx_SubApEditFieldLabel
            app.SVDx_SubApEditFieldLabel = uilabel(app.AdvancedProcessingPanel);
            app.SVDx_SubApEditFieldLabel.HorizontalAlignment = 'right';
            app.SVDx_SubApEditFieldLabel.FontColor = [0.902 0.902 0.902];
            app.SVDx_SubApEditFieldLabel.Position = [160 317 79 22];
            app.SVDx_SubApEditFieldLabel.Text = 'SVDx_SubAp';

            % Create SVDx_SubApEditField
            app.SVDx_SubApEditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.SVDx_SubApEditField.Limits = [0 20];
            app.SVDx_SubApEditField.Position = [247 317 26 22];
            app.SVDx_SubApEditField.Value = 3;

            % Create SVDxCheckBox
            app.SVDxCheckBox = uicheckbox(app.AdvancedProcessingPanel);
            app.SVDxCheckBox.Text = 'SVDx';
            app.SVDxCheckBox.FontColor = [0.902 0.902 0.902];
            app.SVDxCheckBox.Position = [85 317 53 22];

            % Create SVDThresholdEditField
            app.SVDThresholdEditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.SVDThresholdEditField.Limits = [0 Inf];
            app.SVDThresholdEditField.ValueChangedFcn = createCallbackFcn(app, @SVDThresholdEditFieldValueChanged, true);
            app.SVDThresholdEditField.Enable = 'off';
            app.SVDThresholdEditField.Position = [247 291 26 22];
            app.SVDThresholdEditField.Value = 64;

            % Create SVDTresholdEditFieldLabel
            app.SVDTresholdEditFieldLabel = uilabel(app.AdvancedProcessingPanel);
            app.SVDTresholdEditFieldLabel.HorizontalAlignment = 'right';
            app.SVDTresholdEditFieldLabel.FontColor = [0.902 0.902 0.902];
            app.SVDTresholdEditFieldLabel.Position = [153 291 86 22];
            app.SVDTresholdEditFieldLabel.Text = 'SVD Threshold';

            % Create SVDThresholdCheckBox
            app.SVDThresholdCheckBox = uicheckbox(app.AdvancedProcessingPanel);
            app.SVDThresholdCheckBox.ValueChangedFcn = createCallbackFcn(app, @SVDThresholdCheckBoxValueChanged, true);
            app.SVDThresholdCheckBox.Text = '';
            app.SVDThresholdCheckBox.FontColor = [0.902 0.902 0.902];
            app.SVDThresholdCheckBox.Position = [137 293 25 22];

            % Create SVDStrideEditField
            app.SVDStrideEditField = uieditfield(app.AdvancedProcessingPanel, 'numeric');
            app.SVDStrideEditField.Limits = [0 Inf];
            app.SVDStrideEditField.Tooltip = {'Sub sampling parameter for faster SVD calculations. Defaults to 1 -> full image, 2 -> one pixel on two, ...'};
            app.SVDStrideEditField.Position = [256 30 26 22];
            app.SVDStrideEditField.Value = 1;

            % Create SVDTresholdEditFieldLabel_2
            app.SVDTresholdEditFieldLabel_2 = uilabel(app.AdvancedProcessingPanel);
            app.SVDTresholdEditFieldLabel_2.HorizontalAlignment = 'right';
            app.SVDTresholdEditFieldLabel_2.FontColor = [0.902 0.902 0.902];
            app.SVDTresholdEditFieldLabel_2.Position = [184 30 64 22];
            app.SVDTresholdEditFieldLabel_2.Text = 'SVD Stride';

            % Create AberrationcompensationPanel
            app.AberrationcompensationPanel = uipanel(app.GridLayout);
            app.AberrationcompensationPanel.ForegroundColor = [0.8 0.8 0.8];
            app.AberrationcompensationPanel.Title = 'Aberration compensation';
            app.AberrationcompensationPanel.BackgroundColor = [0.2 0.2 0.2];
            app.AberrationcompensationPanel.Layout.Row = 1;
            app.AberrationcompensationPanel.Layout.Column = 3;

            % Create UIAxes_aberrationPreview
            app.UIAxes_aberrationPreview = uiaxes(app.AberrationcompensationPanel);
            app.UIAxes_aberrationPreview.CLim = [0 1];
            app.UIAxes_aberrationPreview.XColor = [0.15 0.15 0.15];
            app.UIAxes_aberrationPreview.XTick = [];
            app.UIAxes_aberrationPreview.YTick = [];
            app.UIAxes_aberrationPreview.LineWidth = 2;
            app.UIAxes_aberrationPreview.Color = [0.149 0.149 0.149];
            app.UIAxes_aberrationPreview.Position = [103 47 88 85];

            % Create Label_2
            app.Label_2 = uilabel(app.AberrationcompensationPanel);
            app.Label_2.VerticalAlignment = 'top';
            app.Label_2.FontColor = [0.8 0.8 0.8];
            app.Label_2.Position = [9 332 229 21];
            app.Label_2.Text = {''; ''};

            % Create ShackHartmannCheckBox
            app.ShackHartmannCheckBox = uicheckbox(app.AberrationcompensationPanel);
            app.ShackHartmannCheckBox.Tooltip = {'Perform aberration compensation with Shack Hartmann simulation'};
            app.ShackHartmannCheckBox.Text = 'Shack Hartmann';
            app.ShackHartmannCheckBox.FontColor = [0.902 0.902 0.902];
            app.ShackHartmannCheckBox.Position = [12 285 111 22];

            % Create zernikeranksEditFieldLabel
            app.zernikeranksEditFieldLabel = uilabel(app.AberrationcompensationPanel);
            app.zernikeranksEditFieldLabel.HorizontalAlignment = 'center';
            app.zernikeranksEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.zernikeranksEditFieldLabel.Position = [9 230 77 22];
            app.zernikeranksEditFieldLabel.Text = 'zernike ranks';

            % Create shackhartmannzernikeranksEditField
            app.shackhartmannzernikeranksEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.shackhartmannzernikeranksEditField.Limits = [2 6];
            app.shackhartmannzernikeranksEditField.RoundFractionalValues = 'on';
            app.shackhartmannzernikeranksEditField.FontColor = [0.8 0.8 0.8];
            app.shackhartmannzernikeranksEditField.BackgroundColor = [0.149 0.149 0.149];
            app.shackhartmannzernikeranksEditField.Tooltip = {'Number of zernike ranks to use for aberration correction'};
            app.shackhartmannzernikeranksEditField.Position = [142 230 43 22];
            app.shackhartmannzernikeranksEditField.Value = 2;

            % Create subaperturemarginEditFieldLabel
            app.subaperturemarginEditFieldLabel = uilabel(app.AberrationcompensationPanel);
            app.subaperturemarginEditFieldLabel.HorizontalAlignment = 'center';
            app.subaperturemarginEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.subaperturemarginEditFieldLabel.Position = [9 161 110 22];
            app.subaperturemarginEditFieldLabel.Text = 'subaperture margin';

            % Create subaperturemarginEditField
            app.subaperturemarginEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.subaperturemarginEditField.Limits = [0 Inf];
            app.subaperturemarginEditField.FontColor = [0.8 0.8 0.8];
            app.subaperturemarginEditField.BackgroundColor = [0.149 0.149 0.149];
            app.subaperturemarginEditField.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
            app.subaperturemarginEditField.Position = [142 161 43 22];
            app.subaperturemarginEditField.Value = 0.3;

            % Create IterativeoptimizationCheckBox
            app.IterativeoptimizationCheckBox = uicheckbox(app.AberrationcompensationPanel);
            app.IterativeoptimizationCheckBox.Tooltip = {'Activate aberration compensation via image entropy optimization. This might significantly increase the computation time.'};
            app.IterativeoptimizationCheckBox.Text = 'Iterative optimization';
            app.IterativeoptimizationCheckBox.FontColor = [0.902 0.902 0.902];
            app.IterativeoptimizationCheckBox.Position = [149 335 132 22];

            % Create zernikeranksEditField_2Label
            app.zernikeranksEditField_2Label = uilabel(app.AberrationcompensationPanel);
            app.zernikeranksEditField_2Label.HorizontalAlignment = 'right';
            app.zernikeranksEditField_2Label.FontColor = [0.8 0.8 0.8];
            app.zernikeranksEditField_2Label.Visible = 'off';
            app.zernikeranksEditField_2Label.Position = [159 302 75 14];
            app.zernikeranksEditField_2Label.Text = 'zernike ranks';

            % Create optimizationzernikeranksEditField
            app.optimizationzernikeranksEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.optimizationzernikeranksEditField.Limits = [2 Inf];
            app.optimizationzernikeranksEditField.FontColor = [0.8 0.8 0.8];
            app.optimizationzernikeranksEditField.BackgroundColor = [0.149 0.149 0.149];
            app.optimizationzernikeranksEditField.Visible = 'off';
            app.optimizationzernikeranksEditField.Tooltip = {'Number of zernike ranks that constitue the aberration projection polynomial space'};
            app.optimizationzernikeranksEditField.Position = [239 298 43 22];
            app.optimizationzernikeranksEditField.Value = 2;

            % Create toleranceLabel
            app.toleranceLabel = uilabel(app.AberrationcompensationPanel);
            app.toleranceLabel.HorizontalAlignment = 'center';
            app.toleranceLabel.FontColor = [0.8 0.8 0.8];
            app.toleranceLabel.Visible = 'off';
            app.toleranceLabel.Position = [179 242 55 22];
            app.toleranceLabel.Text = 'tolerance';

            % Create zernikestolEditField
            app.zernikestolEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.zernikestolEditField.Limits = [0 Inf];
            app.zernikestolEditField.FontColor = [0.8 0.8 0.8];
            app.zernikestolEditField.BackgroundColor = [0.149 0.149 0.149];
            app.zernikestolEditField.Visible = 'off';
            app.zernikestolEditField.Tooltip = {''};
            app.zernikestolEditField.Position = [239 242 43 22];
            app.zernikestolEditField.Value = 0.05;

            % Create maxconstraintEditFieldLabel
            app.maxconstraintEditFieldLabel = uilabel(app.AberrationcompensationPanel);
            app.maxconstraintEditFieldLabel.HorizontalAlignment = 'center';
            app.maxconstraintEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.maxconstraintEditFieldLabel.Visible = 'off';
            app.maxconstraintEditFieldLabel.Position = [149 218 86 18];
            app.maxconstraintEditFieldLabel.Text = 'max constraint';

            % Create maxconstraintEditField
            app.maxconstraintEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.maxconstraintEditField.Limits = [1 Inf];
            app.maxconstraintEditField.RoundFractionalValues = 'on';
            app.maxconstraintEditField.FontColor = [0.8 0.8 0.8];
            app.maxconstraintEditField.BackgroundColor = [0.149 0.149 0.149];
            app.maxconstraintEditField.Visible = 'off';
            app.maxconstraintEditField.Tooltip = {''};
            app.maxconstraintEditField.Position = [239 216 43 22];
            app.maxconstraintEditField.Value = 10;

            % Create masknumiterEditFieldLabel
            app.masknumiterEditFieldLabel = uilabel(app.AberrationcompensationPanel);
            app.masknumiterEditFieldLabel.HorizontalAlignment = 'center';
            app.masknumiterEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.masknumiterEditFieldLabel.Visible = 'off';
            app.masknumiterEditFieldLabel.Position = [156 270 81 22];
            app.masknumiterEditFieldLabel.Text = 'mask num iter';

            % Create masknumiterEditField
            app.masknumiterEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.masknumiterEditField.Limits = [1 Inf];
            app.masknumiterEditField.RoundFractionalValues = 'on';
            app.masknumiterEditField.FontColor = [0.8 0.8 0.8];
            app.masknumiterEditField.BackgroundColor = [0.149 0.149 0.149];
            app.masknumiterEditField.Visible = 'off';
            app.masknumiterEditField.Tooltip = {''};
            app.masknumiterEditField.Position = [239 270 43 22];
            app.masknumiterEditField.Value = 1;

            % Create PreviewLabel
            app.PreviewLabel = uilabel(app.AberrationcompensationPanel);
            app.PreviewLabel.FontColor = [0.8 0.8 0.8];
            app.PreviewLabel.Position = [17 81 96 42];
            app.PreviewLabel.Text = {'astig_1 : 0.0'; 'defocus: 0.0'; 'astig_2 : 0.0'};

            % Create SubAp_PCACheckBox
            app.SubAp_PCACheckBox = uicheckbox(app.AberrationcompensationPanel);
            app.SubAp_PCACheckBox.ValueChangedFcn = createCallbackFcn(app, @SubAp_PCACheckBoxValueChanged, true);
            app.SubAp_PCACheckBox.Text = 'SubAp_PCA';
            app.SubAp_PCACheckBox.FontColor = [1 1 1];
            app.SubAp_PCACheckBox.Position = [10 337 89 22];

            % Create minEditField_2Label
            app.minEditField_2Label = uilabel(app.AberrationcompensationPanel);
            app.minEditField_2Label.HorizontalAlignment = 'right';
            app.minEditField_2Label.FontColor = [1 1 1];
            app.minEditField_2Label.Position = [9 314 25 22];
            app.minEditField_2Label.Text = 'min';

            % Create minSubAp_PCAEditField
            app.minSubAp_PCAEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.minSubAp_PCAEditField.Limits = [1 Inf];
            app.minSubAp_PCAEditField.ValueChangedFcn = createCallbackFcn(app, @minSubApPCAEditField_2ValueChanged, true);
            app.minSubAp_PCAEditField.Position = [41 317 24 16];
            app.minSubAp_PCAEditField.Value = 1;

            % Create maxEditField_2Label
            app.maxEditField_2Label = uilabel(app.AberrationcompensationPanel);
            app.maxEditField_2Label.HorizontalAlignment = 'right';
            app.maxEditField_2Label.FontColor = [1 1 1];
            app.maxEditField_2Label.Position = [73 314 28 22];
            app.maxEditField_2Label.Text = 'max';

            % Create maxSubAp_PCAEditField
            app.maxSubAp_PCAEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.maxSubAp_PCAEditField.Limits = [1 Inf];
            app.maxSubAp_PCAEditField.ValueChangedFcn = createCallbackFcn(app, @maxSubAp_PCAEditField_2_2ValueChanged, true);
            app.maxSubAp_PCAEditField.Position = [108 317 24 16];
            app.maxSubAp_PCAEditField.Value = 16;

            % Create volumesizeEditFieldLabel
            app.volumesizeEditFieldLabel = uilabel(app.AberrationcompensationPanel);
            app.volumesizeEditFieldLabel.HorizontalAlignment = 'right';
            app.volumesizeEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.volumesizeEditFieldLabel.Visible = 'off';
            app.volumesizeEditFieldLabel.Position = [157 53 69 22];
            app.volumesizeEditFieldLabel.Text = 'volume size';

            % Create volumesizeEditField
            app.volumesizeEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.volumesizeEditField.Limits = [1 Inf];
            app.volumesizeEditField.Visible = 'off';
            app.volumesizeEditField.Position = [231 54 31 21];
            app.volumesizeEditField.Value = 256;

            % Create rangeZEditFieldLabel
            app.rangeZEditFieldLabel = uilabel(app.AberrationcompensationPanel);
            app.rangeZEditFieldLabel.HorizontalAlignment = 'right';
            app.rangeZEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.rangeZEditFieldLabel.Visible = 'off';
            app.rangeZEditFieldLabel.Position = [180 26 44 22];
            app.rangeZEditFieldLabel.Text = 'rangeZ';

            % Create rangeZEditField
            app.rangeZEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.rangeZEditField.Limits = [1 Inf];
            app.rangeZEditField.ValueChangedFcn = createCallbackFcn(app, @rangeZEditFieldValueChanged, true);
            app.rangeZEditField.Visible = 'off';
            app.rangeZEditField.Position = [232 25 30 22];
            app.rangeZEditField.Value = 1;

            % Create rangeYEditFieldLabel
            app.rangeYEditFieldLabel = uilabel(app.AberrationcompensationPanel);
            app.rangeYEditFieldLabel.HorizontalAlignment = 'right';
            app.rangeYEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.rangeYEditFieldLabel.Visible = 'off';
            app.rangeYEditFieldLabel.Position = [14 26 44 22];
            app.rangeYEditFieldLabel.Text = 'rangeY';

            % Create rangeYEditField
            app.rangeYEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.rangeYEditField.Limits = [1 Inf];
            app.rangeYEditField.ValueChangedFcn = createCallbackFcn(app, @rangeYEditFieldValueChanged, true);
            app.rangeYEditField.Visible = 'off';
            app.rangeYEditField.Position = [66 25 30 22];
            app.rangeYEditField.Value = 1;

            % Create savecoefsCheckBox
            app.savecoefsCheckBox = uicheckbox(app.AberrationcompensationPanel);
            app.savecoefsCheckBox.Text = 'save coefs';
            app.savecoefsCheckBox.FontColor = [0.8 0.8 0.8];
            app.savecoefsCheckBox.Position = [14 51 90 22];

            % Create ZernikeProjectionCheckBox
            app.ZernikeProjectionCheckBox = uicheckbox(app.AberrationcompensationPanel);
            app.ZernikeProjectionCheckBox.Tooltip = {'Perform aberration compensation with Shack Hartmann simulation'};
            app.ZernikeProjectionCheckBox.Text = 'Zernike Projection';
            app.ZernikeProjectionCheckBox.FontColor = [0.902 0.902 0.902];
            app.ZernikeProjectionCheckBox.Position = [13 255 119 22];

            % Create referenceimageDropDownLabel
            app.referenceimageDropDownLabel = uilabel(app.AberrationcompensationPanel);
            app.referenceimageDropDownLabel.HorizontalAlignment = 'right';
            app.referenceimageDropDownLabel.FontColor = [0.902 0.902 0.902];
            app.referenceimageDropDownLabel.Position = [7 135 92 22];
            app.referenceimageDropDownLabel.Text = 'reference image';

            % Create referenceimageDropDown
            app.referenceimageDropDown = uidropdown(app.AberrationcompensationPanel);
            app.referenceimageDropDown.Items = {'central subaperture', 'resized image'};
            app.referenceimageDropDown.FontColor = [0.9412 0.9412 0.9412];
            app.referenceimageDropDown.BackgroundColor = [0.502 0.502 0.502];
            app.referenceimageDropDown.Position = [114 135 135 18];
            app.referenceimageDropDown.Value = 'central subaperture';

            % Create subapnumpositionsEditFieldLabel
            app.subapnumpositionsEditFieldLabel = uilabel(app.AberrationcompensationPanel);
            app.subapnumpositionsEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.subapnumpositionsEditFieldLabel.Position = [12 207 115 22];
            app.subapnumpositionsEditFieldLabel.Text = 'subap num positions';

            % Create subapnumpositionsEditField
            app.subapnumpositionsEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.subapnumpositionsEditField.Limits = [1 20];
            app.subapnumpositionsEditField.RoundFractionalValues = 'on';
            app.subapnumpositionsEditField.FontColor = [0.8 0.8 0.8];
            app.subapnumpositionsEditField.BackgroundColor = [0.149 0.149 0.149];
            app.subapnumpositionsEditField.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
            app.subapnumpositionsEditField.Position = [142 207 43 22];
            app.subapnumpositionsEditField.Value = 5;

            % Create imagesubapsizeratioEditFieldLabel
            app.imagesubapsizeratioEditFieldLabel = uilabel(app.AberrationcompensationPanel);
            app.imagesubapsizeratioEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.imagesubapsizeratioEditFieldLabel.Position = [12 184 125 22];
            app.imagesubapsizeratioEditFieldLabel.Text = 'image subap size ratio';

            % Create imagesubapsizeratioEditField
            app.imagesubapsizeratioEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
            app.imagesubapsizeratioEditField.Limits = [1 20];
            app.imagesubapsizeratioEditField.RoundFractionalValues = 'on';
            app.imagesubapsizeratioEditField.FontColor = [0.8 0.8 0.8];
            app.imagesubapsizeratioEditField.BackgroundColor = [0.149 0.149 0.149];
            app.imagesubapsizeratioEditField.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
            app.imagesubapsizeratioEditField.Position = [142 184 43 22];
            app.imagesubapsizeratioEditField.Value = 5;

            % Create GridLayout2
            app.GridLayout2 = uigridlayout(app.GridLayout);
            app.GridLayout2.ColumnWidth = {'1x'};
            app.GridLayout2.RowHeight = {'1x'};
            app.GridLayout2.Padding = [0 0 0 0];
            app.GridLayout2.Layout.Row = 1;
            app.GridLayout2.Layout.Column = 1;
            app.GridLayout2.BackgroundColor = [0.2 0.2 0.2];

            % Create GridLayout3
            app.GridLayout3 = uigridlayout(app.GridLayout2);
            app.GridLayout3.ColumnWidth = {'1x'};
            app.GridLayout3.RowHeight = {'1x'};
            app.GridLayout3.Padding = [0 0 0 0];
            app.GridLayout3.Layout.Row = 1;
            app.GridLayout3.Layout.Column = 1;
            app.GridLayout3.BackgroundColor = [0.2 0.2 0.2];

            % Create ImagerenderingPanel
            app.ImagerenderingPanel = uipanel(app.GridLayout3);
            app.ImagerenderingPanel.ForegroundColor = [0.8 0.8 0.8];
            app.ImagerenderingPanel.Title = 'Image rendering';
            app.ImagerenderingPanel.BackgroundColor = [0.2 0.2 0.2];
            app.ImagerenderingPanel.Layout.Row = 1;
            app.ImagerenderingPanel.Layout.Column = 1;

            % Create f1EditFieldLabel
            app.f1EditFieldLabel = uilabel(app.ImagerenderingPanel);
            app.f1EditFieldLabel.HorizontalAlignment = 'center';
            app.f1EditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.f1EditFieldLabel.Position = [151 175 38 22];
            app.f1EditFieldLabel.Text = 'f1';

            % Create f1EditField
            app.f1EditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.f1EditField.Limits = [0 Inf];
            app.f1EditField.ValueChangedFcn = createCallbackFcn(app, @f1EditFieldValueChanged, true);
            app.f1EditField.FontColor = [0.8 0.8 0.8];
            app.f1EditField.BackgroundColor = [0.149 0.149 0.149];
            app.f1EditField.Tooltip = {'Frequency lower integration bound in kHz.'};
            app.f1EditField.Position = [182 174 52 22];
            app.f1EditField.Value = 8;

            % Create f2EditFieldLabel
            app.f2EditFieldLabel = uilabel(app.ImagerenderingPanel);
            app.f2EditFieldLabel.HorizontalAlignment = 'center';
            app.f2EditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.f2EditFieldLabel.Position = [151 151 38 22];
            app.f2EditFieldLabel.Text = 'f2';

            % Create f2EditField
            app.f2EditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.f2EditField.Limits = [0 Inf];
            app.f2EditField.ValueChangedFcn = createCallbackFcn(app, @f2EditFieldValueChanged, true);
            app.f2EditField.FontColor = [0.8 0.8 0.8];
            app.f2EditField.BackgroundColor = [0.149 0.149 0.149];
            app.f2EditField.Tooltip = {'Frequency upper integration bound in kHz.'};
            app.f2EditField.Position = [182 150 52 22];
            app.f2EditField.Value = 30;

            % Create compositef3EditFieldLabel
            app.compositef3EditFieldLabel = uilabel(app.ImagerenderingPanel);
            app.compositef3EditFieldLabel.HorizontalAlignment = 'center';
            app.compositef3EditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.compositef3EditFieldLabel.Visible = 'off';
            app.compositef3EditFieldLabel.Position = [157 125 25 22];
            app.compositef3EditFieldLabel.Text = 'f3';

            % Create compositef3EditField
            app.compositef3EditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.compositef3EditField.Limits = [0 Inf];
            app.compositef3EditField.ValueChangedFcn = createCallbackFcn(app, @compositef3EditFieldValueChanged, true);
            app.compositef3EditField.FontColor = [0.8 0.8 0.8];
            app.compositef3EditField.BackgroundColor = [0.149 0.149 0.149];
            app.compositef3EditField.Visible = 'off';
            app.compositef3EditField.Tooltip = {'Frequency upper integration bound in kHz.'};
            app.compositef3EditField.Position = [182 124 52 22];
            app.compositef3EditField.Value = 30;

            % Create ImageChoiceDropDown
            app.ImageChoiceDropDown = uidropdown(app.ImagerenderingPanel);
            app.ImageChoiceDropDown.Items = {'power Doppler', 'color Doppler', 'directional Doppler', 'velocity estimate', 'phase variation'};
            app.ImageChoiceDropDown.ValueChangedFcn = createCallbackFcn(app, @ImageChoiceDropDownValueChanged, true);
            app.ImageChoiceDropDown.FontColor = [0.9412 0.9412 0.9412];
            app.ImageChoiceDropDown.BackgroundColor = [0.502 0.502 0.502];
            app.ImageChoiceDropDown.Position = [7 160 124 22];
            app.ImageChoiceDropDown.Value = 'power Doppler';

            % Create blurEditFieldLabel
            app.blurEditFieldLabel = uilabel(app.ImagerenderingPanel);
            app.blurEditFieldLabel.HorizontalAlignment = 'right';
            app.blurEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.blurEditFieldLabel.Position = [29 110 26 22];
            app.blurEditFieldLabel.Text = 'blur';

            % Create blurEditField
            app.blurEditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.blurEditField.Limits = [0 Inf];
            app.blurEditField.ValueChangedFcn = createCallbackFcn(app, @blurEditFieldValueChanged, true);
            app.blurEditField.FontColor = [0.8 0.8 0.8];
            app.blurEditField.BackgroundColor = [0.149 0.149 0.149];
            app.blurEditField.Tooltip = {'Magnitude of gaussian filter'};
            app.blurEditField.Position = [64 110 38 22];
            app.blurEditField.Value = 35;

            % Create timetransformDropDownLabel
            app.timetransformDropDownLabel = uilabel(app.ImagerenderingPanel);
            app.timetransformDropDownLabel.HorizontalAlignment = 'right';
            app.timetransformDropDownLabel.FontColor = [0.902 0.902 0.902];
            app.timetransformDropDownLabel.Position = [4 204 82 22];
            app.timetransformDropDownLabel.Text = 'time transform';

            % Create timetransformDropDown
            app.timetransformDropDown = uidropdown(app.ImagerenderingPanel);
            app.timetransformDropDown.Items = {'FFT', 'PCA'};
            app.timetransformDropDown.ValueChangedFcn = createCallbackFcn(app, @TimeTransform, true);
            app.timetransformDropDown.FontColor = [0.902 0.902 0.902];
            app.timetransformDropDown.BackgroundColor = [0.502 0.502 0.502];
            app.timetransformDropDown.Position = [95 206 60 19];
            app.timetransformDropDown.Value = 'FFT';

            % Create minEditFieldLabel
            app.minEditFieldLabel = uilabel(app.ImagerenderingPanel);
            app.minEditFieldLabel.HorizontalAlignment = 'right';
            app.minEditFieldLabel.FontColor = [1 1 1];
            app.minEditFieldLabel.Visible = 'off';
            app.minEditFieldLabel.Position = [164 204 25 22];
            app.minEditFieldLabel.Text = 'min';

            % Create min_PCAEditField
            app.min_PCAEditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.min_PCAEditField.Limits = [1 Inf];
            app.min_PCAEditField.ValueChangedFcn = createCallbackFcn(app, @min_PCAEditFieldValueChanged, true);
            app.min_PCAEditField.Visible = 'off';
            app.min_PCAEditField.Position = [196 208 33 16];
            app.min_PCAEditField.Value = 1;

            % Create maxEditFieldLabel
            app.maxEditFieldLabel = uilabel(app.ImagerenderingPanel);
            app.maxEditFieldLabel.HorizontalAlignment = 'right';
            app.maxEditFieldLabel.FontColor = [1 1 1];
            app.maxEditFieldLabel.Visible = 'off';
            app.maxEditFieldLabel.Position = [234 205 28 22];
            app.maxEditFieldLabel.Text = 'max';

            % Create max_PCAEditField
            app.max_PCAEditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.max_PCAEditField.Limits = [1 Inf];
            app.max_PCAEditField.ValueChangedFcn = createCallbackFcn(app, @max_PCAEditFieldValueChanged, true);
            app.max_PCAEditField.Visible = 'off';
            app.max_PCAEditField.Position = [269 208 30 17];
            app.max_PCAEditField.Value = 16;

            % Create EditField
            app.EditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.EditField.Limits = [0 Inf];
            app.EditField.RoundFractionalValues = 'on';
            app.EditField.ValueDisplayFormat = '%.0f';
            app.EditField.ValueChangedFcn = createCallbackFcn(app, @EditFieldValueChanged, true);
            app.EditField.FontColor = [0.8 0.8 0.8];
            app.EditField.BackgroundColor = [0.149 0.149 0.149];
            app.EditField.Tooltip = {''};
            app.EditField.Position = [155 17 65 22];

            % Create positioninfileSliderLabel
            app.positioninfileSliderLabel = uilabel(app.ImagerenderingPanel);
            app.positioninfileSliderLabel.HorizontalAlignment = 'right';
            app.positioninfileSliderLabel.FontColor = [0.902 0.902 0.902];
            app.positioninfileSliderLabel.Position = [57 8 78 19];
            app.positioninfileSliderLabel.Text = {'position in file'; ''};

            % Create positioninfileSlider
            app.positioninfileSlider = uislider(app.ImagerenderingPanel);
            app.positioninfileSlider.Limits = [0 1];
            app.positioninfileSlider.MajorTicks = [];
            app.positioninfileSlider.ValueChangedFcn = createCallbackFcn(app, @positioninfileSliderValueChanged, true);
            app.positioninfileSlider.MinorTicks = [];
            app.positioninfileSlider.Tooltip = {'Change value to display a different video timestamp in the gui.'};
            app.positioninfileSlider.Position = [65 43 158 3];

            % Create zretinaEditField
            app.zretinaEditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.zretinaEditField.ValueChangedFcn = createCallbackFcn(app, @zretinaEditFieldValueChanged, true);
            app.zretinaEditField.FontColor = [0.8 0.8 0.8];
            app.zretinaEditField.BackgroundColor = [0.149 0.149 0.149];
            app.zretinaEditField.Tooltip = {'Reconstruction distance in mm. Can be computed automatically with the ''Autofocus'' button.'};
            app.zretinaEditField.Position = [17 299 47 22];
            app.zretinaEditField.Value = 0.22;

            % Create zirisEditField
            app.zirisEditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.zirisEditField.Limits = [0 Inf];
            app.zirisEditField.ValueChangedFcn = createCallbackFcn(app, @zirisEditFieldValueChanged, true);
            app.zirisEditField.FontColor = [0.8 0.8 0.8];
            app.zirisEditField.BackgroundColor = [0.149 0.149 0.149];
            app.zirisEditField.Tooltip = {'Reconstruction distance in mm. Can be computed automatically with the ''Autofocus'' button.'};
            app.zirisEditField.Position = [205 299 52 22];
            app.zirisEditField.Value = 0.22;

            % Create Switch
            app.Switch = uiswitch(app.ImagerenderingPanel, 'slider');
            app.Switch.Items = {'z_retina', 'z_iris'};
            app.Switch.ValueChangedFcn = createCallbackFcn(app, @ZSwitchValueChanged, true);
            app.Switch.FontColor = [0.8 0.8 0.8];
            app.Switch.Position = [119 300 47 21];
            app.Switch.Value = 'z_retina';

            % Create num_batches
            app.num_batches = uilabel(app.ImagerenderingPanel);
            app.num_batches.FontColor = [0.902 0.902 0.902];
            app.num_batches.Position = [217 22 111 22];
            app.num_batches.Text = '';

            % Create batchsizeEditFieldLabel
            app.batchsizeEditFieldLabel = uilabel(app.ImagerenderingPanel);
            app.batchsizeEditFieldLabel.HorizontalAlignment = 'center';
            app.batchsizeEditFieldLabel.FontColor = [0.8 0.8 0.8];
            app.batchsizeEditFieldLabel.Position = [19 65 76 22];
            app.batchsizeEditFieldLabel.Text = 'batch size';

            % Create batchsizeEditField
            app.batchsizeEditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.batchsizeEditField.Limits = [1 2048];
            app.batchsizeEditField.ValueChangedFcn = createCallbackFcn(app, @batchsizeEditFieldValueChanged, true);
            app.batchsizeEditField.FontColor = [0.8 0.8 0.8];
            app.batchsizeEditField.BackgroundColor = [0.149 0.149 0.149];
            app.batchsizeEditField.Tooltip = {'Number of interferograms used to generate a single image. Increase value for better video quality.'};
            app.batchsizeEditField.Position = [94 65 48 22];
            app.batchsizeEditField.Value = 512;

            % Create RenderpreviewButton
            app.RenderpreviewButton = uibutton(app.ImagerenderingPanel, 'push');
            app.RenderpreviewButton.ButtonPushedFcn = createCallbackFcn(app, @RenderpreviewButtonPushed, true);
            app.RenderpreviewButton.BackgroundColor = [0.502 0.502 0.502];
            app.RenderpreviewButton.FontColor = [0.902 0.902 0.902];
            app.RenderpreviewButton.Position = [137 264 104 22];
            app.RenderpreviewButton.Text = 'Render preview';

            % Create showSpatialFilterCheckBox
            app.showSpatialFilterCheckBox = uicheckbox(app.ImagerenderingPanel);
            app.showSpatialFilterCheckBox.ValueChangedFcn = createCallbackFcn(app, @showSpatialFilterCheckBoxValueChanged, true);
            app.showSpatialFilterCheckBox.Text = 'show';
            app.showSpatialFilterCheckBox.FontColor = [0.902 0.902 0.902];
            app.showSpatialFilterCheckBox.Position = [248 138 50 22];

            % Create renderLamp
            app.renderLamp = uilamp(app.ImagerenderingPanel);
            app.renderLamp.Position = [255 271 12 12];

            % Create SavepreviewButton
            app.SavepreviewButton = uibutton(app.ImagerenderingPanel, 'push');
            app.SavepreviewButton.ButtonPushedFcn = createCallbackFcn(app, @SavePreview, true);
            app.SavepreviewButton.BackgroundColor = [0.502 0.502 0.502];
            app.SavepreviewButton.FontColor = [0.9412 0.9412 0.9412];
            app.SavepreviewButton.Position = [137 235 104 22];
            app.SavepreviewButton.Text = 'Save preview';

            % Create AutofocusButton
            app.AutofocusButton = uibutton(app.ImagerenderingPanel, 'push');
            app.AutofocusButton.ButtonPushedFcn = createCallbackFcn(app, @AutofocusButtonPushed, true);
            app.AutofocusButton.BackgroundColor = [0.502 0.502 0.502];
            app.AutofocusButton.FontColor = [0.902 0.902 0.902];
            app.AutofocusButton.Position = [19 264 104 22];
            app.AutofocusButton.Text = 'Autofocus';

            % Create savelamp
            app.savelamp = uilamp(app.ImagerenderingPanel);
            app.savelamp.Position = [256 240 12 12];

            % Create maxEditFieldLabel_2
            app.maxEditFieldLabel_2 = uilabel(app.ImagerenderingPanel);
            app.maxEditFieldLabel_2.HorizontalAlignment = 'right';
            app.maxEditFieldLabel_2.FontColor = [1 1 1];
            app.maxEditFieldLabel_2.Visible = 'off';
            app.maxEditFieldLabel_2.Position = [263 175 28 22];
            app.maxEditFieldLabel_2.Text = 'max';

            % Create compositef3EditFieldLabel_2
            app.compositef3EditFieldLabel_2 = uilabel(app.ImagerenderingPanel);
            app.compositef3EditFieldLabel_2.HorizontalAlignment = 'center';
            app.compositef3EditFieldLabel_2.FontColor = [0.8 0.8 0.8];
            app.compositef3EditFieldLabel_2.Visible = 'off';
            app.compositef3EditFieldLabel_2.Position = [157 150 25 22];
            app.compositef3EditFieldLabel_2.Text = 'f2';

            % Create compositef2EditField
            app.compositef2EditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.compositef2EditField.Limits = [0 Inf];
            app.compositef2EditField.FontColor = [0.8 0.8 0.8];
            app.compositef2EditField.BackgroundColor = [0.149 0.149 0.149];
            app.compositef2EditField.Visible = 'off';
            app.compositef2EditField.Tooltip = {'Frequency upper integration bound in kHz.'};
            app.compositef2EditField.Position = [182 149 52 22];
            app.compositef2EditField.Value = 30;

            % Create compositef3EditFieldLabel_3
            app.compositef3EditFieldLabel_3 = uilabel(app.ImagerenderingPanel);
            app.compositef3EditFieldLabel_3.HorizontalAlignment = 'center';
            app.compositef3EditFieldLabel_3.FontColor = [0.8 0.8 0.8];
            app.compositef3EditFieldLabel_3.Visible = 'off';
            app.compositef3EditFieldLabel_3.Position = [157 176 25 22];
            app.compositef3EditFieldLabel_3.Text = 'f1';

            % Create compositef1EditField
            app.compositef1EditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.compositef1EditField.Limits = [0 Inf];
            app.compositef1EditField.FontColor = [0.8 0.8 0.8];
            app.compositef1EditField.BackgroundColor = [0.149 0.149 0.149];
            app.compositef1EditField.Visible = 'off';
            app.compositef1EditField.Tooltip = {'Frequency upper integration bound in kHz.'};
            app.compositef1EditField.Position = [182 175 52 22];
            app.compositef1EditField.Value = 30;

            % Create spatialtransformationLabel
            app.spatialtransformationLabel = uilabel(app.ImagerenderingPanel);
            app.spatialtransformationLabel.HorizontalAlignment = 'right';
            app.spatialtransformationLabel.FontColor = [0.8 0.8 0.8];
            app.spatialtransformationLabel.Position = [29 332 120 22];
            app.spatialtransformationLabel.Text = 'spatial transformation';

            % Create spatialTransformationDropDown
            app.spatialTransformationDropDown = uidropdown(app.ImagerenderingPanel);
            app.spatialTransformationDropDown.Items = {'Fresnel', 'angular spectrum'};
            app.spatialTransformationDropDown.ValueChangedFcn = createCallbackFcn(app, @spatialTransformationChanged, true);
            app.spatialTransformationDropDown.FontColor = [0.902 0.902 0.902];
            app.spatialTransformationDropDown.BackgroundColor = [0.502 0.502 0.502];
            app.spatialTransformationDropDown.Position = [164 332 90 22];
            app.spatialTransformationDropDown.Value = 'Fresnel';

            % Create ShowSpectrumButton
            app.ShowSpectrumButton = uibutton(app.ImagerenderingPanel, 'push');
            app.ShowSpectrumButton.ButtonPushedFcn = createCallbackFcn(app, @ShowSpectrumButtonPushed, true);
            app.ShowSpectrumButton.BackgroundColor = [0.502 0.502 0.502];
            app.ShowSpectrumButton.FontColor = [0.902 0.902 0.902];
            app.ShowSpectrumButton.Position = [19 234 104 23];
            app.ShowSpectrumButton.Text = 'Show Spectrum';

            % Create scan3D
            app.scan3D = uibutton(app.ImagerenderingPanel, 'push');
            app.scan3D.ButtonPushedFcn = createCallbackFcn(app, @scan3DButtonPushed, true);
            app.scan3D.BackgroundColor = [0.502 0.502 0.502];
            app.scan3D.FontColor = [0.902 0.902 0.902];
            app.scan3D.Tooltip = {'3D Scan on a  20cm   range centered on the current z'};
            app.scan3D.Position = [266 299 33 23];
            app.scan3D.Text = '<->';

            % Create numFreqEditField
            app.numFreqEditField = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.numFreqEditField.Limits = [1 Inf];
            app.numFreqEditField.FontColor = [0.8 0.8 0.8];
            app.numFreqEditField.BackgroundColor = [0.149 0.149 0.149];
            app.numFreqEditField.Tooltip = {'Number of frequencies intervals you want to have the M0 of.'};
            app.numFreqEditField.Position = [183 91 52 22];
            app.numFreqEditField.Value = 1;

            % Create compositef3EditFieldLabel_4
            app.compositef3EditFieldLabel_4 = uilabel(app.ImagerenderingPanel);
            app.compositef3EditFieldLabel_4.HorizontalAlignment = 'center';
            app.compositef3EditFieldLabel_4.FontColor = [0.8 0.8 0.8];
            app.compositef3EditFieldLabel_4.Position = [151 91 32 22];
            app.compositef3EditFieldLabel_4.Text = '#freq';

            % Create spatialfilterratio
            app.spatialfilterratio = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.spatialfilterratio.Limits = [0 10];
            app.spatialfilterratio.ValueChangedFcn = createCallbackFcn(app, @spatialfilterratioValueChanged, true);
            app.spatialfilterratio.FontColor = [0.8 0.8 0.8];
            app.spatialfilterratio.BackgroundColor = [0.149 0.149 0.149];
            app.spatialfilterratio.Tooltip = {'Number of frequencies intervals you want to have the M0 of.'};
            app.spatialfilterratio.Position = [85 134 46 22];

            % Create compositef3EditFieldLabel_5
            app.compositef3EditFieldLabel_5 = uilabel(app.ImagerenderingPanel);
            app.compositef3EditFieldLabel_5.HorizontalAlignment = 'center';
            app.compositef3EditFieldLabel_5.FontColor = [0.8 0.8 0.8];
            app.compositef3EditFieldLabel_5.Position = [12 135 66 22];
            app.compositef3EditFieldLabel_5.Text = 'spatial filter';

            % Create spatialfilterratiohigh
            app.spatialfilterratiohigh = uieditfield(app.ImagerenderingPanel, 'numeric');
            app.spatialfilterratiohigh.Limits = [0 1000];
            app.spatialfilterratiohigh.FontColor = [0.8 0.8 0.8];
            app.spatialfilterratiohigh.BackgroundColor = [0.149 0.149 0.149];
            app.spatialfilterratiohigh.Tooltip = {'Laser wavelength in nanometers'};
            app.spatialfilterratiohigh.Position = [137 134 27 22];
            app.spatialfilterratiohigh.Value = 0.7;

            % Create ImageLeft
            app.ImageLeft = uiimage(app.GridLayout4);
            app.ImageLeft.ImageClickedFcn = createCallbackFcn(app, @ImageLeftClicked, true);
            app.ImageLeft.Layout.Row = 1;
            app.ImageLeft.Layout.Column = 2;

            % Create ImageRight
            app.ImageRight = uiimage(app.GridLayout4);
            app.ImageRight.ScaleMethod = 'stretch';
            app.ImageRight.ImageClickedFcn = createCallbackFcn(app, @ImageRightClicked, true);
            app.ImageRight.Layout.Row = 1;
            app.ImageRight.Layout.Column = 3;

            % Show the figure after all components are created
            app.HoloDopplerUIFigure.Visible = 'on';
        end
    end

    % App creation and deletion
    methods (Access = public)

        % Construct app
        function app = holod

            % Create UIFigure and components
            createComponents(app)

            % Register the app with App Designer
            registerApp(app, app.HoloDopplerUIFigure)

            % Execute the startup function
            runStartupFcn(app, @startupFcn)

            if nargout == 0
                clear app
            end
        end

        % Code that executes before app deletion
        function delete(app)

            % Delete UIFigure when app is deleted
            delete(app.HoloDopplerUIFigure)
        end
    end
end