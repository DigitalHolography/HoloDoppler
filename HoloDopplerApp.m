classdef HoloDopplerApp < matlab.apps.AppBase

% =========================================================================
% UI component handles — required public by App Designer / registerApp
% =========================================================================
properties (Access = public)
    HoloDopplerUIFigure matlab.ui.Figure

    % ---- top-level layout ----
    RootGrid matlab.ui.container.GridLayout
    PanelPlot matlab.ui.container.Panel
    ImageLeft matlab.ui.control.Image
    ImageRight matlab.ui.control.Image

    % ---- current-file strip (bottom) ----
    CurrentFilePanel matlab.ui.container.Panel
    CurrentFileGrid matlab.ui.container.GridLayout
    RenderingGrid matlab.ui.container.GridLayout
    RenderingInnerGrid matlab.ui.container.GridLayout

    % ---- file selection panel (left column) ----
    FileselectionPanel matlab.ui.container.Panel

    % ---- top grid menu ----
    mainParametersGrid matlab.ui.container.GridLayout
    LoadfileButton matlab.ui.control.Button
    fileLoadedLamp matlab.ui.control.Lamp

    fsLabel matlab.ui.control.Label
    fs matlab.ui.control.NumericEditField

    lambdaLabel matlab.ui.control.Label
    lambda matlab.ui.control.NumericEditField

    pixelPitchLabel matlab.ui.control.Label
    ppx matlab.ui.control.NumericEditField
    ppy matlab.ui.control.NumericEditField

    imageSizeLabel matlab.ui.control.Label
    Nx matlab.ui.control.NumericEditField
    Ny matlab.ui.control.NumericEditField

    numworkersSpinnerLabel matlab.ui.control.Label
    parfor_arg matlab.ui.control.Spinner

    NotesTextAreaLabel matlab.ui.control.Label
    NotesTextArea matlab.ui.control.TextArea

    AdvancedButton matlab.ui.control.Button
    RefreshAppButton matlab.ui.control.Button
    positioninfileSlider matlab.ui.control.Slider
    positioninfileSliderLabel matlab.ui.control.Label
    framePosition matlab.ui.control.NumericEditField

    % ---- batch / video rendering sub-panel ----
    batchPanel matlab.ui.container.Panel
    batchGrid matlab.ui.container.GridLayout
    SaveconfigButton matlab.ui.control.Button
    PlayButton matlab.ui.control.Button
    ShowHistogramButton matlab.ui.control.Button
    VideoRenderingLamp matlab.ui.control.Lamp
    SaveVideoButton matlab.ui.control.Button
    batchSize matlab.ui.control.NumericEditField
    batchSizeLabel matlab.ui.control.Label
    Image_typesListBox matlab.ui.control.ListBox
    registrationDiscLabel matlab.ui.control.Label
    registration_disc_ratio matlab.ui.control.NumericEditField
    refBatchSize matlab.ui.control.NumericEditField
    refBatchSizeLabel matlab.ui.control.Label
    batchStride matlab.ui.control.NumericEditField
    batchStrideLabel matlab.ui.control.Label
    LoadconfigButton matlab.ui.control.Button
    VideoRenderingButton matlab.ui.control.Button
    FoldermanagementButton matlab.ui.control.Button
    temporalFilter matlab.ui.control.NumericEditField
    AutofocusFromRef matlab.ui.control.CheckBox
    applyshackhartmannfromref matlab.ui.control.CheckBox
    temporalfilterCheckBox matlab.ui.control.CheckBox
    phaseregistrationCheckBox matlab.ui.control.CheckBox
    rephasingCheckBox matlab.ui.control.CheckBox
    image_registration matlab.ui.control.CheckBox
    showrefCheckBox matlab.ui.control.CheckBox
    iterativeregistrationCheckBox matlab.ui.control.CheckBox

    % ---- rendering parameters panel ----
    RenderingParametersPanel matlab.ui.container.Panel
    RenderingParametersGrid matlab.ui.container.GridLayout

    Padding_num matlab.ui.control.NumericEditField
    PaddNLabel matlab.ui.control.Label
    AutofocusButton matlab.ui.control.Button
    square matlab.ui.control.CheckBox
    flip_x matlab.ui.control.CheckBox
    flip_y matlab.ui.control.CheckBox
    indexRange2 matlab.ui.control.NumericEditField
    indexRange1 matlab.ui.control.NumericEditField
    indexRangeLabel matlab.ui.control.Label
    RenderPreviewLamp matlab.ui.control.Lamp
    SavePreviewButton matlab.ui.control.Button
    RenderPreviewButton matlab.ui.control.Button
    flat_field_gw matlab.ui.control.NumericEditField
    flat_field_gwLabel matlab.ui.control.Label
    frequencyRangeLabel matlab.ui.control.Label
    frequencyRange2 matlab.ui.control.NumericEditField
    frequencyRange1 matlab.ui.control.NumericEditField
    frequencyRangeInterLabel matlab.ui.control.Label
    frequencyRangeInter1 matlab.ui.control.NumericEditField
    frequencyRangeInter2 matlab.ui.control.NumericEditField
    time_transform matlab.ui.control.DropDown
    time_transformDropDownLabel matlab.ui.control.Label
    svdThreshold matlab.ui.control.NumericEditField
    svd_filter matlab.ui.control.CheckBox
    spatial_propagation matlab.ui.control.NumericEditField
    spatial_propagationLabel matlab.ui.control.Label
    spatial_transformation matlab.ui.control.DropDown
    spatial_transformationDropDownLabel matlab.ui.control.Label
    spatialFilterRange2 matlab.ui.control.NumericEditField
    spatialFilterRange1 matlab.ui.control.NumericEditField
    spatialFilter matlab.ui.control.CheckBox
    svdThreshold_reset_button matlab.ui.control.Button

    % ---- aberration compensation panel ----
    AberrationcompensationPanel matlab.ui.container.Panel
    onlydefocusCheckBox matlab.ui.control.CheckBox
    ConvergenceThreshold matlab.ui.control.NumericEditField
    calibrationfactorLabel_2 matlab.ui.control.Label
    CalibrationFactor matlab.ui.control.NumericEditField
    calibrationfactorLabel matlab.ui.control.Label
    NumberOfIteration matlab.ui.control.NumericEditField
    numberofiterationLabel matlab.ui.control.Label
    imageSubApSizeRatio matlab.ui.control.NumericEditField
    imageSubApSizeRatioLabel matlab.ui.control.Label
    SubApNumPositions matlab.ui.control.NumericEditField
    SubApNumPositionsLabel matlab.ui.control.Label
    referenceimageDropDown matlab.ui.control.DropDown
    referenceimageDropDownLabel matlab.ui.control.Label
    ZernikeProjectionCheckBox matlab.ui.control.CheckBox
    savecoefsCheckBox matlab.ui.control.CheckBox
    rangeY matlab.ui.control.NumericEditField
    rangeYLabel matlab.ui.control.Label
    rangeZ matlab.ui.control.NumericEditField
    rangeZLabel matlab.ui.control.Label
    volumeSize matlab.ui.control.NumericEditField
    volumeSizeLabel matlab.ui.control.Label
    maxSubAp_PCA matlab.ui.control.NumericEditField
    max_2Label matlab.ui.control.Label
    minSubAp_PCA matlab.ui.control.NumericEditField
    min_2Label matlab.ui.control.Label
    SubAp_PCACheckBox matlab.ui.control.CheckBox
    aberrationPreviewLabel matlab.ui.control.Label
    IterativeCheckBox matlab.ui.control.CheckBox
    subApMargin matlab.ui.control.NumericEditField
    subApMarginLabel matlab.ui.control.Label
    shackHartmannZernikeRanks matlab.ui.control.NumericEditField
    zernikeRanksLabels matlab.ui.control.Label
    ShackHartmannCheckBox matlab.ui.control.CheckBox
    aberrationStatusLabel matlab.ui.control.Label
    UIAxes_aberrationPreview matlab.ui.control.UIAxes

    % ---- advanced processing panel ----
    AdvancedProcessingPanel matlab.ui.container.Panel
    SVDTresholdLabel_2 matlab.ui.control.Label
    svdStride matlab.ui.control.NumericEditField
    SVDThresholdCheckBox matlab.ui.control.CheckBox
    SVDThresholdLabel matlab.ui.control.Label
    SVDThreshold matlab.ui.control.NumericEditField
    xyStride matlab.ui.control.NumericEditField
    xyStrideLabel matlab.ui.control.Label
    r1 matlab.ui.control.NumericEditField
    r1Label matlab.ui.control.Label
    unitCellsinLattice matlab.ui.control.NumericEditField
    unitCellsinLatticeLabel matlab.ui.control.Label
    nu2 matlab.ui.control.NumericEditField
    nu2Label matlab.ui.control.Label
    nu1 matlab.ui.control.NumericEditField
    nu1Label matlab.ui.control.Label
    phi2 matlab.ui.control.NumericEditField
    phi2Label matlab.ui.control.Label
    phi1 matlab.ui.control.NumericEditField
    phi1Label matlab.ui.control.Label
    LocalfilteringLabel matlab.ui.control.Label
    temporalCheckBox matlab.ui.control.CheckBox
    spatialCheckBox matlab.ui.control.CheckBox
    SVDCheckBox matlab.ui.control.CheckBox

    % ---- context menu ----
    RightClickImageContextMenu matlab.ui.container.ContextMenu
    NextMenu matlab.ui.container.Menu
    ViewAllMenu matlab.ui.container.Menu
end

% =========================================================================
% Application state (readable by external code, e.g. classtogui / guitoclass)
% =========================================================================
properties (Access = public)
    fileLoaded % was file_loaded
    HD % HoloDopplerClass instance
    drawer_list = {}
end

% =========================================================================
% Internal state
% =========================================================================
properties (Access = private)
    DialogApp % Dialog box app
    poolobj
end

% =========================================================================
% Callbacks
% =========================================================================
methods (Access = private)

    % --- Startup / lifecycle -----------------------------------------------

    function startupFcn(app)
        logFile = fullfile(tempdir, ['matlab_log_' char(datetime('now', 'Format', 'yyyyMMdd_HHmmss')) '.txt']);
        diary(logFile);

        if exist("version.txt", 'file')
            v = readlines('version.txt');
            fprintf("============================================\n " + ...
                "Welcome to HoloDoppler %s\n" + ...
                "--------------------------------------------\n" + ...
                "Developed by the DigitalHolographyFoundation\n" + ...
                "============================================\n", v(1));
        end

        app.HoloDopplerUIFigure.Name = ['HoloDoppler ', char(v(1))];

        addpath("Tools\"); % for the splashscreen
        displaySplashScreen();
        app.HD = HoloDopplerClass();
    end

    function HoloDopplerUIFigureCloseRequest(app, ~)
        diary off;
        delete(app.HoloDopplerUIFigure);
    end

    function HoloDopplerUIFigureWindowKeyPress(app, event)

        switch event.Key
            case 'return'
                app.RenderPreviewButtonPushed();
            case 'rightarrow'
                app.NextMenuSelected();
        end

    end

    % --- File I/O callbacks ------------------------------------------------

    function LoadfileButtonPushed(app, ~)
        % Dummy figure keeps uigetfile from minimising the main GUI
        f = figure('Position', [-100 -100 0 0]);

        if isempty(app.HD.file)
            [fname, fpath] = uigetfile('*.raw;*.cine;*.holo');
        else
            [fname, fpath] = uigetfile(strcat(app.HD.file.path, "*.raw;*.cine;*.holo"));
        end

        delete(f);

        if fname == 0
            return
        end

        try
            app.fileLoadedLamp.Color = [1 0.5 0];
            app.HD.LoadFile(fullfile(fpath, fname));
            app.syncGuiFromClass();
            app.RenderPreviewButtonPushed();
            app.fileLoaded = 1;
            app.fileLoadedLamp.Color = [0 1 0];
        catch ME
            MEdisp(ME);
            app.fileLoadedLamp.Color = [1 0 0];
            drawnow
        end

        if ~isempty(app.HD.file)
            app.CurrentFilePanel.Title = ['Current File : ' app.HD.file.path];
        end

        app.refreshClass();
    end

    function LoadconfigButtonPushed(app, ~)
        [selected_file, path] = uigetfile('*.json', 'Select File');

        if selected_file
            [~, ~, ext] = fileparts(selected_file);

            if ismember(ext, {'.json'})
                app.HD.loadParams(fullfile(path, selected_file));

                try
                    app.syncGuiFromClass();
                catch ME
                    MEdisp(ME);
                end

            else
                fprintf("Couldn't load config");
            end

        end

    end

    function SaveconfigButtonPushed(app, ~)
        app.HD.saveParams();
    end

    % --- Render callbacks --------------------------------------------------

    function RenderPreviewButtonPushed(app, ~)
        app.RenderPreviewLamp.Color = [1 0.5 0];
        drawnow;

        try
            Images = app.HD.PreviewRendering();
            app.RenderPreviewLamp.Color = [0 1 0];
        catch ME
            Images = [];
            MEdisp(ME);
            app.RenderPreviewLamp.Color = [1 0 0];
            drawnow
        end

        if ~isempty(Images)
            app.ImageLeft.ImageSource = toImageSource(Images{1}, app);
        else
            app.ImageLeft.ImageSource = '';
        end

        if ismember("FH_modulus_mean", app.HD.params.image_types)
            img = app.HD.view.getImages({"FH_modulus_mean"});

            if ~isempty(img{1})
                app.ImageRight.ImageSource = toImageSource(img{1});
            end

        else
            app.ImageRight.ImageSource = '';
        end

    end

    function VideoRenderingButtonPushed(app, ~)
        app.VideoRenderingLamp.Color = [1 0.5 0]; drawnow;

        try
            app.HD.VideoRendering();
            app.VideoRenderingLamp.Color = [0 1 0];
        catch ME
            MEdisp(ME);
            app.VideoRenderingLamp.Color = [1 0 0];
        end

    end

    function SaveVideoButtonPushed(app, ~)
        app.HD.SaveVideo();
    end

    function SavePreviewButtonPushed(app, ~)
        app.HD.savePreview();
    end

    % --- UI state sync / refresh -------------------------------------------

    % Sync every widget value into the HD class, then update enable states.
    % Connected to ~50 component ValueChanged callbacks.
    function refreshClass(app, ~)

        if ~isempty(app.HD.file)
            app.framePosition.Value = app.positioninfileSlider.Value;
        else
            app.framePosition.Value = 0;
        end

        app.syncClassFromGui();
        app.updateTimeTransformControls();
    end

    function RefreshAppButtonPushed(app, ~)
        app.syncGuiFromClass();

        if isempty(app.HD.params.image_types)
            return
        end

        imgs = app.HD.view.getImages(app.HD.params.image_types(1));

        if ~isempty(imgs)
            app.ImageLeft.ImageSource = toImageSource(imgs{randsample(numel(imgs), 1)});
        else
            app.ImageLeft.ImageSource = '';
        end

    end

    function AutofocusButtonPushed2(app, ~)
        zopti = autofocus(app.HD.view, app.HD.params);
        app.HD.params.spatial_propagation = zopti;
        app.syncGuiFromClass();
        app.RenderPreviewButtonPushed();
    end

    % --- Context menu / image navigation -----------------------------------

    function NextMenuSelected(app, ~)
        imgs = app.HD.view.getImages(app.HD.params.image_types);

        if ~isempty(imgs)
            num = randi(numel(imgs), 1);

            if isnumeric(imgs{num})
                image = imgs{num};

                if ~ismember(app.HD.params.image_types{num}, {'broadening'}) && size(image, 1) ~= size(image, 2)
                    image = imresize(image, [max(size(image, 1), size(image, 2)), max(size(image, 1), size(image, 2))]);
                end

                imgs{num} = image;

                if ~isempty(imgs)
                    app.ImageLeft.ImageSource = toImageSource(imgs{num}, app);
                else
                    app.ImageLeft.ImageSource = '';
                end

            else
                toImageSource(imgs{randi(numel(imgs), 1)}, app);
            end

        else
            app.ImageLeft.ImageSource = '';
        end

    end

    function ViewAllMenuSelected(app, ~)
        app.HD.showPreviewImages();
    end

    % --- Misc callbacks ----------------------------------------------------

    function ShowHistogramButtonPushed(app, ~)
        app.HD.view.showFramesHistogram();
    end

    function svdThreshold_reset_buttonPushed(app, ~)

        if app.svdThreshold.Value == 0
            val = ceil(app.frequencyRange1.Value * 2 * app.batchSize.Value / app.fs.Value);

            if ~isnan(val)
                app.svdThreshold.Value = val;
            end

        else
            app.svdThreshold.Value = 0;
        end

        app.refreshClass();

    end

    function frequencyRange2ValueChanged(app, ~)

        if strcmp(app.time_transform, 'FFT') && app.frequencyRange2.Value > app.fs.Value / 2
            app.frequencyRange2.Value = app.fs.Value / 2;
        end

        app.refreshClass();
    end

    function AdvancedButtonPushed(app, ~)
        AdvancedPanel(app);
    end

    function registration_disc_ratioValueChanged(app, ~)
        app.refreshClass();
        show_ref_disc(app, app.image_registration.Value);
    end

    % --- Folder management -------------------------------------------------

    function FoldermanagementButtonPushed(app, ~)
        FolderManagement(app);
    end

end % callbacks methods block

% =========================================================================
% Private helper methods (GUI sync, UI enable logic, drawer operations)
% =========================================================================
methods (Access = private)

    % --- GUI <-> class sync (replaces external classtogui / guitoclass) ----

    % Push all widget values into HD (was external guitoclass)
    function syncClassFromGui(app)
        guitoclass(app.HD, app);
    end

    % Pull all HD values into widgets (was external classtogui)
    function syncGuiFromClass(app)
        classtogui(app.HD, app);
    end

    % --- refreshClass sub-routines ----------------------------------------

    function updateTimeTransformControls(app)
        useFreqRange = ismember(app.time_transform.Value, {'FFT', 'autocorrelation', 'intercorrelation'});
        app.frequencyRangeLabel.Enable = useFreqRange;
        app.frequencyRange1.Enable = useFreqRange;
        app.frequencyRange2.Enable = useFreqRange;
        app.frequencyRangeInterLabel.Enable = useFreqRange;
        app.frequencyRangeInter1.Enable = useFreqRange;
        app.frequencyRangeInter2.Enable = useFreqRange;
        app.indexRange1.Enable = ~useFreqRange;
        app.indexRange2.Enable = ~useFreqRange;
        app.indexRangeLabel.Enable = ~useFreqRange;
    end

    % --- Drawer (folder management) helpers --------------------------------

end % private helpers methods block

% =========================================================================
% Component initialisation — split by panel
% =========================================================================
methods (Access = private)

    function createComponents(app)
        pathToMLAPP = fileparts(mfilename('fullpath'));

        app.createFigureAndRootGrid(pathToMLAPP);
        app.createFileSelectionPanel();
        app.createBatchVideoPanel();
        app.createCurrentFileStrip();
        app.createAdvancedProcessingPanel();
        app.createAberrationPanel();
        app.createRenderingParametersPanel();
        app.createImageViewsAndMenus();

        app.HoloDopplerUIFigure.Visible = 'on';
    end

    % -----------------------------------------------------------------------
    function createFigureAndRootGrid(app, pathToMLAPP)
        app.HoloDopplerUIFigure = uifigure('Visible', 'off');
        app.HoloDopplerUIFigure.Color = [0.149 0.149 0.149];
        app.HoloDopplerUIFigure.Position = [210 56 1260 900];
        app.HoloDopplerUIFigure.Name = 'HoloDoppler';
        app.HoloDopplerUIFigure.Icon = fullfile(pathToMLAPP, 'holoDopplerLogo.png');
        app.HoloDopplerUIFigure.CloseRequestFcn = createCallbackFcn(app, @HoloDopplerUIFigureCloseRequest, true);
        app.HoloDopplerUIFigure.WindowKeyPressFcn = createCallbackFcn(app, @HoloDopplerUIFigureWindowKeyPress, true);

        app.RootGrid = uigridlayout(app.HoloDopplerUIFigure);
        app.RootGrid.ColumnWidth = {'1.2x', '2x', '2x'};
        app.RootGrid.RowHeight = {'1x', 420};
        app.RootGrid.RowSpacing = 5;
        app.RootGrid.Padding = [0 3.20001220703125 0 3.20001220703125];
        app.RootGrid.BackgroundColor = [0.2 0.2 0.2];
    end

    % -----------------------------------------------------------------------
    function createFileSelectionPanel(app)

        backgroundColor = [0.2 0.2 0.2];
        darkBackgroundColor = [0.15 0.15 0.15];
        fontColor = [0.9 0.9 0.9];
        grayButtonColor = [0.5 0.5 0.5];

        app.FileselectionPanel = uipanel(app.RootGrid);
        app.FileselectionPanel.Tooltip = {''};
        app.FileselectionPanel.ForegroundColor = fontColor;
        app.FileselectionPanel.TitlePosition = 'centertop';
        app.FileselectionPanel.Title = 'File selection';
        app.FileselectionPanel.BackgroundColor = backgroundColor;
        app.FileselectionPanel.Layout.Row = [1 2];
        app.FileselectionPanel.Layout.Column = 1;

        app.mainParametersGrid = uigridlayout(app.FileselectionPanel, [10 3]);
        app.mainParametersGrid.RowHeight = {'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', '1x'};
        app.mainParametersGrid.ColumnWidth = {'1x', '1x', '1x'};
        app.mainParametersGrid.Padding = [10 10 10 10];
        app.mainParametersGrid.RowSpacing = 5;
        app.mainParametersGrid.ColumnSpacing = 5;
        app.mainParametersGrid.BackgroundColor = backgroundColor;

        app.LoadfileButton = uibutton(app.mainParametersGrid, 'push');
        app.LoadfileButton.ButtonPushedFcn = createCallbackFcn(app, @LoadfileButtonPushed, true);
        app.LoadfileButton.BackgroundColor = grayButtonColor;
        app.LoadfileButton.FontColor = fontColor;
        app.LoadfileButton.Tooltip = {'Load a raw video file (formats : .raw, .cine, .holo)'};
        app.LoadfileButton.Layout.Row = 1;
        app.LoadfileButton.Layout.Column = 1;
        app.LoadfileButton.Text = 'Load file';

        app.fileLoadedLamp = uilamp(app.mainParametersGrid);
        app.fileLoadedLamp.Layout.Row = 1;
        app.fileLoadedLamp.Layout.Column = 3;

        app.lambdaLabel = uilabel(app.mainParametersGrid);
        app.lambdaLabel.FontColor = fontColor;
        app.lambdaLabel.Tooltip = {'Laser''s wavelength for light propagation calculations in (m)'};
        app.lambdaLabel.Text = 'λ (m)';
        app.lambdaLabel.HorizontalAlignment = 'center';
        app.lambdaLabel.Layout.Row = 2;
        app.lambdaLabel.Layout.Column = 1;

        app.lambda = uieditfield(app.mainParametersGrid, 'numeric');
        app.lambda.Limits = [0 Inf];
        app.lambda.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.lambda.FontColor = fontColor;
        app.lambda.BackgroundColor = darkBackgroundColor;
        app.lambda.Tooltip = {'Laser wavelength in nanometers'};
        app.lambda.Layout.Row = 2;
        app.lambda.Layout.Column = 2;

        app.fsLabel = uilabel(app.mainParametersGrid);
        app.fsLabel.FontColor = fontColor;
        app.fsLabel.Tooltip = {'Sampling frequency in (kHz)'};
        app.fsLabel.Text = 'fs (kHz)';
        app.fsLabel.HorizontalAlignment = 'center';
        app.fsLabel.Layout.Row = 3;
        app.fsLabel.Layout.Column = 1;

        app.fs = uieditfield(app.mainParametersGrid, 'numeric');
        app.fs.Limits = [0 Inf];
        app.fs.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.fs.FontColor = fontColor;
        app.fs.BackgroundColor = darkBackgroundColor;
        app.fs.Tooltip = {'Sampling frequency in (kHz)'};
        app.fs.Layout.Row = 3;
        app.fs.Layout.Column = 2;

        app.pixelPitchLabel = uilabel(app.mainParametersGrid);
        app.pixelPitchLabel.HorizontalAlignment = 'center';
        app.pixelPitchLabel.FontColor = fontColor;
        app.pixelPitchLabel.Tooltip = {'Camera pixel pitch (distance between spatial sampling points) in (m)'};
        app.pixelPitchLabel.Text = 'pp x y';
        app.pixelPitchLabel.Layout.Row = 4;
        app.pixelPitchLabel.Layout.Column = 1;

        app.ppx = uieditfield(app.mainParametersGrid, 'numeric');
        app.ppx.Limits = [0 10];
        app.ppx.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ppx.FontColor = fontColor;
        app.ppx.BackgroundColor = darkBackgroundColor;
        app.ppx.Layout.Row = 4;
        app.ppx.Layout.Column = 2;

        app.ppy = uieditfield(app.mainParametersGrid, 'numeric');
        app.ppy.Limits = [0 10];
        app.ppy.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ppy.FontColor = fontColor;
        app.ppy.BackgroundColor = darkBackgroundColor;
        app.ppy.Layout.Row = 4;
        app.ppy.Layout.Column = 3;

        app.imageSizeLabel = uilabel(app.mainParametersGrid);
        app.imageSizeLabel.HorizontalAlignment = 'center';
        app.imageSizeLabel.FontColor = fontColor;
        app.imageSizeLabel.Tooltip = {'Camera pixel pitch (distance between spatial sampling points) in (m)'};
        app.imageSizeLabel.Text = 'Nx Ny';
        app.imageSizeLabel.Layout.Row = 5;
        app.imageSizeLabel.Layout.Column = 1;

        app.Nx = uieditfield(app.mainParametersGrid, 'numeric');
        app.Nx.Limits = [0 Inf];
        app.Nx.Editable = 'off';
        app.Nx.FontColor = fontColor;
        app.Nx.BackgroundColor = darkBackgroundColor;
        app.Nx.Tooltip = {'Width of the recorded interferograms'};
        app.Nx.Layout.Row = 5;
        app.Nx.Layout.Column = 2;

        app.Ny = uieditfield(app.mainParametersGrid, 'numeric');
        app.Ny.Limits = [0 Inf];
        app.Ny.Editable = 'off';
        app.Ny.FontColor = fontColor;
        app.Ny.BackgroundColor = darkBackgroundColor;
        app.Ny.Tooltip = {'Height of the recorded interferograms'};
        app.Ny.Layout.Row = 5;
        app.Ny.Layout.Column = 3;

        app.numworkersSpinnerLabel = uilabel(app.mainParametersGrid);
        app.numworkersSpinnerLabel.HorizontalAlignment = 'center';
        app.numworkersSpinnerLabel.FontColor = fontColor;
        app.numworkersSpinnerLabel.Text = 'num workers';
        app.numworkersSpinnerLabel.Layout.Row = 6;
        app.numworkersSpinnerLabel.Layout.Column = 1;

        app.parfor_arg = uispinner(app.mainParametersGrid);
        app.parfor_arg.ValueChangingFcn = createCallbackFcn(app, @refreshClass, true);
        app.parfor_arg.Limits = [-1 32];
        app.parfor_arg.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.parfor_arg.FontColor = fontColor;
        app.parfor_arg.BackgroundColor = darkBackgroundColor;
        app.parfor_arg.Tooltip = {'Number of worker used for the video rendering (depends of the working station)'};
        app.parfor_arg.Value = 10;
        app.parfor_arg.Layout.Row = 6;
        app.parfor_arg.Layout.Column = 2;

        app.positioninfileSliderLabel = uilabel(app.mainParametersGrid);
        app.positioninfileSliderLabel.HorizontalAlignment = 'center';
        app.positioninfileSliderLabel.FontColor = fontColor;
        app.positioninfileSliderLabel.Text = {'position in file'; ''};
        app.positioninfileSliderLabel.Layout.Row = 7;
        app.positioninfileSliderLabel.Layout.Column = 1;

        app.positioninfileSlider = uislider(app.mainParametersGrid);
        app.positioninfileSlider.Limits = [0 1];
        app.positioninfileSlider.MajorTicks = [];
        app.positioninfileSlider.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.positioninfileSlider.MinorTicks = [0 0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 1];
        app.positioninfileSlider.Tooltip = {'Change value to display a different video timestamp in the gui.'};
        app.positioninfileSlider.Layout.Row = 7;
        app.positioninfileSlider.Layout.Column = [2 3];

        app.framePosition = uieditfield(app.mainParametersGrid, 'numeric');
        app.framePosition.Limits = [0 Inf];
        app.framePosition.RoundFractionalValues = 'on';
        app.framePosition.ValueDisplayFormat = '%.0f';
        app.framePosition.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.framePosition.FontColor = fontColor;
        app.framePosition.BackgroundColor = darkBackgroundColor;
        app.framePosition.Tooltip = {''};
        app.framePosition.Layout.Row = 8;
        app.framePosition.Layout.Column = 3;

        app.RefreshAppButton = uibutton(app.mainParametersGrid, 'push');
        app.RefreshAppButton.ButtonPushedFcn = createCallbackFcn(app, @RefreshAppButtonPushed, true);
        app.RefreshAppButton.BackgroundColor = grayButtonColor;
        app.RefreshAppButton.FontColor = fontColor;
        app.RefreshAppButton.Tooltip = {'Refresh the app'};
        app.RefreshAppButton.Text = '👌';
        app.RefreshAppButton.Layout.Row = 9;
        app.RefreshAppButton.Layout.Column = 2;

        app.AdvancedButton = uibutton(app.mainParametersGrid, 'push');
        app.AdvancedButton.ButtonPushedFcn = createCallbackFcn(app, @AdvancedButtonPushed, true);
        app.AdvancedButton.BackgroundColor = grayButtonColor;
        app.AdvancedButton.FontColor = fontColor;
        app.AdvancedButton.Tooltip = {'Advanced settings'};
        app.AdvancedButton.Text = '📎 Advanced';
        app.AdvancedButton.Layout.Row = 9;
        app.AdvancedButton.Layout.Column = 3;
    end

    % -----------------------------------------------------------------------
    function createBatchVideoPanel(app)

        backgroundColor = [0.2 0.2 0.2];
        darkBackgroundColor = [0.15 0.15 0.15];
        fontColor = [0.9 0.9 0.9];
        grayButtonColor = [0.5 0.5 0.5];

        app.batchPanel = uipanel(app.mainParametersGrid);
        app.batchPanel.ForegroundColor = fontColor;
        app.batchPanel.Title = 'Batch parameters';
        app.batchPanel.BackgroundColor = backgroundColor;
        app.batchPanel.Layout.Row = 10;
        app.batchPanel.Layout.Column = [1 3];

        app.batchGrid = uigridlayout(app.batchPanel, [11 2]);
        app.batchGrid.RowHeight = {'1x', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit'};
        app.batchGrid.ColumnWidth = {'1x', '1x'};
        app.batchGrid.Padding = [10 10 10 10];
        app.batchGrid.RowSpacing = 5;
        app.batchGrid.ColumnSpacing = 5;
        app.batchGrid.BackgroundColor = backgroundColor;

        p = app.batchGrid;

        % listBox row 1
        app.Image_typesListBox = uilistbox(p);
        app.Image_typesListBox.Items = {};
        app.Image_typesListBox.Multiselect = 'on';
        app.Image_typesListBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.Image_typesListBox.Tooltip = {'Image types output giving extracting different informations from a batch of frames'};
        app.Image_typesListBox.FontColor = [1 1 1];
        app.Image_typesListBox.BackgroundColor = darkBackgroundColor;
        app.Image_typesListBox.Layout.Row = 1;
        app.Image_typesListBox.Layout.Column = [1 2];
        app.Image_typesListBox.Value = {};

        % buttons row 2
        app.LoadconfigButton = uibutton(p, 'push');
        app.LoadconfigButton.ButtonPushedFcn = createCallbackFcn(app, @LoadconfigButtonPushed, true);
        app.LoadconfigButton.BackgroundColor = grayButtonColor;
        app.LoadconfigButton.FontColor = fontColor;
        app.LoadconfigButton.Tooltip = {'Save a configuration for the video rendering of a file'};
        app.LoadconfigButton.Layout.Row = 2;
        app.LoadconfigButton.Layout.Column = 1;
        app.LoadconfigButton.Text = 'Load config';

        app.SaveconfigButton = uibutton(p, 'push');
        app.SaveconfigButton.ButtonPushedFcn = createCallbackFcn(app, @SaveconfigButtonPushed, true);
        app.SaveconfigButton.BackgroundColor = grayButtonColor;
        app.SaveconfigButton.FontColor = fontColor;
        app.SaveconfigButton.Tooltip = {'Save a configuration for the video rendering of a file'};
        app.SaveconfigButton.Layout.Row = 2;
        app.SaveconfigButton.Layout.Column = 2;
        app.SaveconfigButton.Text = 'Save config';

        % buttons row 3
        app.FoldermanagementButton = uibutton(p, 'push');
        app.FoldermanagementButton.ButtonPushedFcn = createCallbackFcn(app, @FoldermanagementButtonPushed, true);
        app.FoldermanagementButton.BackgroundColor = grayButtonColor;
        app.FoldermanagementButton.FontColor = fontColor;
        app.FoldermanagementButton.Tooltip = {'Open a window to render all files from different folders with their config files'};
        app.FoldermanagementButton.Layout.Row = 3;
        app.FoldermanagementButton.Layout.Column = 1;
        app.FoldermanagementButton.Text = 'Folder management';

        app.VideoRenderingButton = uibutton(p, 'push');
        app.VideoRenderingButton.ButtonPushedFcn = createCallbackFcn(app, @VideoRenderingButtonPushed, true);
        app.VideoRenderingButton.BackgroundColor = grayButtonColor;
        app.VideoRenderingButton.FontColor = fontColor;
        app.VideoRenderingButton.Tooltip = {'Render ''batchSize'' frame batchs spaced by ''batchStride'' and output a video of different image types'};
        app.VideoRenderingButton.Layout.Row = 3;
        app.VideoRenderingButton.Layout.Column = 2;
        app.VideoRenderingButton.Text = 'Video Rendering';

        % Trivia row 4

        app.ShowHistogramButton = uibutton(p, 'push');
        app.ShowHistogramButton.ButtonPushedFcn = createCallbackFcn(app, @ShowHistogramButtonPushed, true);
        app.ShowHistogramButton.BackgroundColor = grayButtonColor;
        app.ShowHistogramButton.FontColor = fontColor;
        app.ShowHistogramButton.Tooltip = {'Show the full frame batch histogram'};
        app.ShowHistogramButton.Layout.Row = 4;
        app.ShowHistogramButton.Layout.Column = 1;
        app.ShowHistogramButton.Text = 'Histogram';

        app.VideoRenderingLamp = uilamp(p);
        app.VideoRenderingLamp.Layout.Row = 4;
        app.VideoRenderingLamp.Layout.Column = 2;

        % sizes row 5 6 7
        app.batchSizeLabel = uilabel(p);
        app.batchSizeLabel.HorizontalAlignment = 'center';
        app.batchSizeLabel.FontColor = fontColor;
        app.batchSizeLabel.Layout.Row = 5;
        app.batchSizeLabel.Layout.Column = 1;
        app.batchSizeLabel.Text = 'batch size';

        app.batchSize = uieditfield(p, 'numeric');
        app.batchSize.Limits = [0 Inf];
        app.batchSize.ValueDisplayFormat = '%.0f';
        app.batchSize.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.batchSize.FontColor = fontColor;
        app.batchSize.BackgroundColor = darkBackgroundColor;
        app.batchSize.Tooltip = {'Number of interferograms used to compute the image'};
        app.batchSize.Layout.Row = 5;
        app.batchSize.Layout.Column = 2;

        app.batchStrideLabel = uilabel(p);
        app.batchStrideLabel.HorizontalAlignment = 'center';
        app.batchStrideLabel.FontColor = fontColor;
        app.batchStrideLabel.Layout.Row = 6;
        app.batchStrideLabel.Layout.Column = 1;
        app.batchStrideLabel.Text = 'batch stride';

        app.batchStride = uieditfield(p, 'numeric');
        app.batchStride.Limits = [0 Inf];
        app.batchStride.ValueDisplayFormat = '%.0f';
        app.batchStride.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.batchStride.FontColor = fontColor;
        app.batchStride.BackgroundColor = darkBackgroundColor;
        app.batchStride.Tooltip = {'Number of interferograms to skip between two images'};
        app.batchStride.Layout.Row = 6;
        app.batchStride.Layout.Column = 2;

        app.refBatchSizeLabel = uilabel(p);
        app.refBatchSizeLabel.HorizontalAlignment = 'center';
        app.refBatchSizeLabel.FontColor = fontColor;
        app.refBatchSizeLabel.Layout.Row = 7;
        app.refBatchSizeLabel.Layout.Column = 1;
        app.refBatchSizeLabel.Text = 'reg batch size';

        app.refBatchSize = uieditfield(p, 'numeric');
        app.refBatchSize.Limits = [0 Inf];
        app.refBatchSize.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.refBatchSize.FontColor = fontColor;
        app.refBatchSize.BackgroundColor = darkBackgroundColor;
        app.refBatchSize.Tooltip = {'Number of interferograms used to compute the image used as reference in registration'};
        app.refBatchSize.Layout.Row = 7;
        app.refBatchSize.Layout.Column = 2;

        % Registration row 8 9 10
        app.AutofocusFromRef = uicheckbox(p);
        app.AutofocusFromRef.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.AutofocusFromRef.Tooltip = {'Activate frame to frame translation registration of images'};
        app.AutofocusFromRef.Text = 'autofocus from ref';
        app.AutofocusFromRef.FontColor = fontColor;
        app.AutofocusFromRef.Layout.Row = 8;
        app.AutofocusFromRef.Layout.Column = 1;

        app.applyshackhartmannfromref = uicheckbox(p);
        app.applyshackhartmannfromref.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.applyshackhartmannfromref.Tooltip = {'Activate frame to frame translation registration of images'};
        app.applyshackhartmannfromref.Text = 'refocus from ref (numeric shack hartmann)';
        app.applyshackhartmannfromref.FontColor = fontColor;
        app.applyshackhartmannfromref.Layout.Row = 9;
        app.applyshackhartmannfromref.Layout.Column = [1 2];

        app.image_registration = uicheckbox(p);
        app.image_registration.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.image_registration.Tooltip = {'Activate frame to frame translation registration of images'};
        app.image_registration.Text = 'image registration';
        app.image_registration.FontColor = fontColor;
        app.image_registration.Layout.Row = 10;
        app.image_registration.Layout.Column = [1 2];

        app.registrationDiscLabel = uilabel(p);
        app.registrationDiscLabel.HorizontalAlignment = 'center';
        app.registrationDiscLabel.FontColor = fontColor;
        app.registrationDiscLabel.Layout.Row = 11;
        app.registrationDiscLabel.Layout.Column = 1;
        app.registrationDiscLabel.Text = 'disk';

        app.registration_disc_ratio = uieditfield(p, 'numeric');
        app.registration_disc_ratio.Limits = [0 1000];
        app.registration_disc_ratio.ValueChangedFcn = createCallbackFcn(app, @registration_disc_ratioValueChanged, true);
        app.registration_disc_ratio.FontColor = fontColor;
        app.registration_disc_ratio.BackgroundColor = darkBackgroundColor;
        app.registration_disc_ratio.Tooltip = {'Size of a disk centered on the images used to compute the registration shifts (0 is empty and 1 is a disc of the maximum dimension).'};
        app.registration_disc_ratio.Layout.Row = 11;
        app.registration_disc_ratio.Layout.Column = 2;

    end

    % -----------------------------------------------------------------------
    function createCurrentFileStrip(app)
        app.CurrentFilePanel = uipanel(app.RootGrid);
        app.CurrentFilePanel.Tooltip = {''};
        app.CurrentFilePanel.ForegroundColor = [0.8 0.8 0.8];
        app.CurrentFilePanel.Title = 'Current file';
        app.CurrentFilePanel.BackgroundColor = [0.2 0.2 0.2];
        app.CurrentFilePanel.Layout.Row = 2;
        app.CurrentFilePanel.Layout.Column = [2 3];

        app.CurrentFileGrid = uigridlayout(app.CurrentFilePanel);
        app.CurrentFileGrid.ColumnWidth = {'1x', '1x', '1x'};
        app.CurrentFileGrid.RowHeight = {'0.8x'};
        app.CurrentFileGrid.BackgroundColor = [0.2 0.2 0.2];

        app.RenderingGrid = uigridlayout(app.CurrentFileGrid);
        app.RenderingGrid.ColumnWidth = {'1x'};
        app.RenderingGrid.RowHeight = {'1x'};
        app.RenderingGrid.Padding = [0 0 0 0];
        app.RenderingGrid.Layout.Row = 1;
        app.RenderingGrid.Layout.Column = 1;
        app.RenderingGrid.BackgroundColor = [0.2 0.2 0.2];

        app.RenderingInnerGrid = uigridlayout(app.RenderingGrid);
        app.RenderingInnerGrid.ColumnWidth = {'1x'};
        app.RenderingInnerGrid.RowHeight = {'1x'};
        app.RenderingInnerGrid.Padding = [0 0 0 0];
        app.RenderingInnerGrid.Layout.Row = 1;
        app.RenderingInnerGrid.Layout.Column = 1;
        app.RenderingInnerGrid.BackgroundColor = [0.2 0.2 0.2];
    end

    % -----------------------------------------------------------------------
    function createAdvancedProcessingPanel(app)
        app.AdvancedProcessingPanel = uipanel(app.CurrentFileGrid);
        app.AdvancedProcessingPanel.ForegroundColor = [0.902 0.902 0.902];
        app.AdvancedProcessingPanel.Title = 'Advanced Processing';
        app.AdvancedProcessingPanel.Visible = 'off';
        app.AdvancedProcessingPanel.BackgroundColor = [0.2 0.2 0.2];
        app.AdvancedProcessingPanel.Layout.Row = 1;
        app.AdvancedProcessingPanel.Layout.Column = 2;

        p = app.AdvancedProcessingPanel;

        app.SVDCheckBox = uicheckbox(p);
        app.SVDCheckBox.Tooltip = {'Enable SVD hologram filtering in hologram construction'};
        app.SVDCheckBox.Text = 'SVD';
        app.SVDCheckBox.FontColor = [0.902 0.902 0.902];
        app.SVDCheckBox.Position = [21 317 47 22];
        app.SVDCheckBox.Value = true;

        app.spatialCheckBox = uicheckbox(p);
        app.spatialCheckBox.Text = 'spatial';
        app.spatialCheckBox.FontColor = [0.8 0.8 0.8];
        app.spatialCheckBox.Position = [19 234 92 22];

        app.temporalCheckBox = uicheckbox(p);
        app.temporalCheckBox.Text = 'temporal';
        app.temporalCheckBox.FontColor = [0.8 0.8 0.8];
        app.temporalCheckBox.Position = [19 261 87 23];

        app.LocalfilteringLabel = uilabel(p);
        app.LocalfilteringLabel.FontColor = [0.8 0.8 0.8];
        app.LocalfilteringLabel.Position = [19 285 83 22];
        app.LocalfilteringLabel.Text = 'Local filtering';

        app.phi1Label = uilabel(p);
        app.phi1Label.HorizontalAlignment = 'right';
        app.phi1Label.FontColor = [0.8 0.8 0.8];
        app.phi1Label.Position = [102 258 28 22];
        app.phi1Label.Text = 'phi1';

        app.phi1 = uieditfield(p, 'numeric');
        app.phi1.Position = [134 258 21 21];

        app.phi2Label = uilabel(p);
        app.phi2Label.HorizontalAlignment = 'right';
        app.phi2Label.FontColor = [0.8 0.8 0.8];
        app.phi2Label.Position = [173 261 28 22];
        app.phi2Label.Text = 'phi2';

        app.phi2 = uieditfield(p, 'numeric');
        app.phi2.Position = [205 261 21 21];

        app.nu1Label = uilabel(p);
        app.nu1Label.HorizontalAlignment = 'right';
        app.nu1Label.FontColor = [0.8 0.8 0.8];
        app.nu1Label.Position = [107 230 26 22];
        app.nu1Label.Text = 'nu1';

        app.nu1 = uieditfield(p, 'numeric');
        app.nu1.Position = [135 230 21 21];

        app.nu2Label = uilabel(p);
        app.nu2Label.HorizontalAlignment = 'right';
        app.nu2Label.FontColor = [0.8 0.8 0.8];
        app.nu2Label.Position = [175 230 26 22];
        app.nu2Label.Text = 'nu2';

        app.nu2 = uieditfield(p, 'numeric');
        app.nu2.FontColor = [0.149 0.149 0.149];
        app.nu2.Position = [205 230 21 21];

        app.unitCellsinLatticeLabel = uilabel(p);
        app.unitCellsinLatticeLabel.HorizontalAlignment = 'right';
        app.unitCellsinLatticeLabel.FontColor = [0.902 0.902 0.902];
        app.unitCellsinLatticeLabel.Position = [18 170 110 22];
        app.unitCellsinLatticeLabel.Text = '# unit cells in lattice';

        app.unitCellsinLattice = uieditfield(p, 'numeric');
        app.unitCellsinLattice.Limits = [0 Inf];
        app.unitCellsinLattice.Position = [135 170 29 22];
        app.unitCellsinLattice.Value = 8;

        app.r1Label = uilabel(p);
        app.r1Label.HorizontalAlignment = 'right';
        app.r1Label.FontColor = [0.902 0.902 0.902];
        app.r1Label.Position = [102 140 25 22];
        app.r1Label.Text = 'r1';

        app.r1 = uieditfield(p, 'numeric');
        app.r1.Limits = [0 Inf];
        app.r1.Position = [135 138 29 23];
        app.r1.Value = 3;

        app.xyStrideLabel = uilabel(p);
        app.xyStrideLabel.HorizontalAlignment = 'right';
        app.xyStrideLabel.FontColor = [0.8 0.8 0.8];
        app.xyStrideLabel.Position = [59 108 50 22];
        app.xyStrideLabel.Text = 'xy stride';

        app.xyStride = uieditfield(p, 'numeric');
        app.xyStride.Position = [124 105 41 27];
        app.xyStride.Value = 32;

        app.SVDThreshold = uieditfield(p, 'numeric');
        app.SVDThreshold.Limits = [0 Inf];
        app.SVDThreshold.Enable = 'off';
        app.SVDThreshold.Position = [247 291 26 22];
        app.SVDThreshold.Value = 64;

        app.SVDThresholdLabel = uilabel(p);
        app.SVDThresholdLabel.HorizontalAlignment = 'right';
        app.SVDThresholdLabel.FontColor = [0.902 0.902 0.902];
        app.SVDThresholdLabel.Position = [153 291 86 22];
        app.SVDThresholdLabel.Text = 'SVD Threshold';

        app.SVDThresholdCheckBox = uicheckbox(p);
        app.SVDThresholdCheckBox.Text = '';
        app.SVDThresholdCheckBox.FontColor = [0.902 0.902 0.902];
        app.SVDThresholdCheckBox.Position = [137 293 25 22];

        app.svdStride = uieditfield(p, 'numeric');
        app.svdStride.Limits = [0 Inf];
        app.svdStride.Tooltip = {'Sub sampling parameter for faster SVD calculations. Defaults to 1 -> full image, 2 -> one pixel on two, ...'};
        app.svdStride.Position = [256 30 26 22];
        app.svdStride.Value = 1;

        app.SVDTresholdLabel_2 = uilabel(p);
        app.SVDTresholdLabel_2.HorizontalAlignment = 'right';
        app.SVDTresholdLabel_2.FontColor = [0.902 0.902 0.902];
        app.SVDTresholdLabel_2.Position = [184 30 64 22];
        app.SVDTresholdLabel_2.Text = 'SVD Stride';
    end

    % -----------------------------------------------------------------------
    function createAberrationPanel(app)
        app.AberrationcompensationPanel = uipanel(app.CurrentFileGrid);
        app.AberrationcompensationPanel.ForegroundColor = [0.8 0.8 0.8];
        app.AberrationcompensationPanel.Title = 'Aberration compensation';
        app.AberrationcompensationPanel.BackgroundColor = [0.2 0.2 0.2];
        app.AberrationcompensationPanel.Layout.Row = 1;
        app.AberrationcompensationPanel.Layout.Column = 3;

        p = app.AberrationcompensationPanel;

        app.UIAxes_aberrationPreview = uiaxes(p);
        app.UIAxes_aberrationPreview.XColor = [0.129411764705882 0.129411764705882 0.129411764705882];
        app.UIAxes_aberrationPreview.XTick = [];
        app.UIAxes_aberrationPreview.YTick = [];
        app.UIAxes_aberrationPreview.LineWidth = 2;
        app.UIAxes_aberrationPreview.Color = [0.149 0.149 0.149];
        app.UIAxes_aberrationPreview.Position = [103 47 88 85];

        app.aberrationStatusLabel = uilabel(p);
        app.aberrationStatusLabel.VerticalAlignment = 'top';
        app.aberrationStatusLabel.FontColor = [0.8 0.8 0.8];
        app.aberrationStatusLabel.Position = [9 332 229 21];
        app.aberrationStatusLabel.Text = {''; ''};

        app.ShackHartmannCheckBox = uicheckbox(p);
        app.ShackHartmannCheckBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ShackHartmannCheckBox.Tooltip = {'Perform aberration compensation with Shack Hartmann simulation'};
        app.ShackHartmannCheckBox.Text = 'Shack Hartmann';
        app.ShackHartmannCheckBox.FontColor = [0.902 0.902 0.902];
        app.ShackHartmannCheckBox.Position = [12 285 111 22];

        app.zernikeRanksLabels = uilabel(p);
        app.zernikeRanksLabels.HorizontalAlignment = 'center';
        app.zernikeRanksLabels.FontColor = [0.8 0.8 0.8];
        app.zernikeRanksLabels.Position = [9 230 77 22];
        app.zernikeRanksLabels.Text = 'zernike ranks';

        app.shackHartmannZernikeRanks = uieditfield(p, 'numeric');
        app.shackHartmannZernikeRanks.Limits = [2 6];
        app.shackHartmannZernikeRanks.RoundFractionalValues = 'on';
        app.shackHartmannZernikeRanks.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.shackHartmannZernikeRanks.FontColor = [0.8 0.8 0.8];
        app.shackHartmannZernikeRanks.BackgroundColor = [0.149 0.149 0.149];
        app.shackHartmannZernikeRanks.Tooltip = {'Number of zernike ranks to use for aberration correction'};
        app.shackHartmannZernikeRanks.Position = [142 230 43 22];
        app.shackHartmannZernikeRanks.Value = 2;

        app.subApMarginLabel = uilabel(p);
        app.subApMarginLabel.HorizontalAlignment = 'center';
        app.subApMarginLabel.FontColor = [0.8 0.8 0.8];
        app.subApMarginLabel.Visible = 'off';
        app.subApMarginLabel.Position = [9 161 110 22];
        app.subApMarginLabel.Text = 'subaperture margin';

        app.subApMargin = uieditfield(p, 'numeric');
        app.subApMargin.Limits = [0 Inf];
        app.subApMargin.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.subApMargin.FontColor = [0.8 0.8 0.8];
        app.subApMargin.BackgroundColor = [0.149 0.149 0.149];
        app.subApMargin.Visible = 'off';
        app.subApMargin.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
        app.subApMargin.Position = [142 161 43 22];
        app.subApMargin.Value = 0.15;

        app.IterativeCheckBox = uicheckbox(p);
        app.IterativeCheckBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.IterativeCheckBox.Tooltip = {'Activate aberration compensation via image entropy optimization. This might significantly increase the computation time.'};
        app.IterativeCheckBox.Text = 'Iterative';
        app.IterativeCheckBox.FontColor = [0.902 0.902 0.902];
        app.IterativeCheckBox.Position = [149 335 65 22];

        app.aberrationPreviewLabel = uilabel(p);
        app.aberrationPreviewLabel.FontColor = [0.8 0.8 0.8];
        app.aberrationPreviewLabel.Position = [17 81 96 42];
        app.aberrationPreviewLabel.Text = {'astig_1 : 0.0'; 'defocus: 0.0'; 'astig_2 : 0.0'};

        app.SubAp_PCACheckBox = uicheckbox(p);
        app.SubAp_PCACheckBox.Visible = 'off';
        app.SubAp_PCACheckBox.Text = 'SubAp_PCA';
        app.SubAp_PCACheckBox.FontColor = [1 1 1];
        app.SubAp_PCACheckBox.Position = [10 337 89 22];

        app.min_2Label = uilabel(p);
        app.min_2Label.HorizontalAlignment = 'right';
        app.min_2Label.FontColor = [1 1 1];
        app.min_2Label.Visible = 'off';
        app.min_2Label.Position = [9 314 25 22];
        app.min_2Label.Text = 'min';

        app.minSubAp_PCA = uieditfield(p, 'numeric');
        app.minSubAp_PCA.Limits = [1 Inf];
        app.minSubAp_PCA.Visible = 'off';
        app.minSubAp_PCA.Position = [41 317 24 16];
        app.minSubAp_PCA.Value = 1;

        app.max_2Label = uilabel(p);
        app.max_2Label.HorizontalAlignment = 'right';
        app.max_2Label.FontColor = [1 1 1];
        app.max_2Label.Visible = 'off';
        app.max_2Label.Position = [73 314 28 22];
        app.max_2Label.Text = 'max';

        app.maxSubAp_PCA = uieditfield(p, 'numeric');
        app.maxSubAp_PCA.Limits = [1 Inf];
        app.maxSubAp_PCA.Visible = 'off';
        app.maxSubAp_PCA.Position = [108 317 24 16];
        app.maxSubAp_PCA.Value = 16;

        app.volumeSizeLabel = uilabel(p);
        app.volumeSizeLabel.HorizontalAlignment = 'right';
        app.volumeSizeLabel.FontColor = [0.8 0.8 0.8];
        app.volumeSizeLabel.Visible = 'off';
        app.volumeSizeLabel.Position = [157 53 69 22];
        app.volumeSizeLabel.Text = 'volume size';

        app.volumeSize = uieditfield(p, 'numeric');
        app.volumeSize.Limits = [1 Inf];
        app.volumeSize.Visible = 'off';
        app.volumeSize.Position = [231 54 31 21];
        app.volumeSize.Value = 256;

        app.rangeZLabel = uilabel(p);
        app.rangeZLabel.HorizontalAlignment = 'right';
        app.rangeZLabel.FontColor = [0.8 0.8 0.8];
        app.rangeZLabel.Visible = 'off';
        app.rangeZLabel.Position = [180 26 44 22];
        app.rangeZLabel.Text = 'rangeZ';

        app.rangeZ = uieditfield(p, 'numeric');
        app.rangeZ.Limits = [1 Inf];
        app.rangeZ.Visible = 'off';
        app.rangeZ.Position = [232 25 30 22];
        app.rangeZ.Value = 1;

        app.rangeYLabel = uilabel(p);
        app.rangeYLabel.HorizontalAlignment = 'right';
        app.rangeYLabel.FontColor = [0.8 0.8 0.8];
        app.rangeYLabel.Visible = 'off';
        app.rangeYLabel.Position = [14 26 44 22];
        app.rangeYLabel.Text = 'rangeY';

        app.rangeY = uieditfield(p, 'numeric');
        app.rangeY.Limits = [1 Inf];
        app.rangeY.Visible = 'off';
        app.rangeY.Position = [66 25 30 22];
        app.rangeY.Value = 1;

        app.savecoefsCheckBox = uicheckbox(p);
        app.savecoefsCheckBox.Visible = 'off';
        app.savecoefsCheckBox.Text = 'save coefs';
        app.savecoefsCheckBox.FontColor = [0.8 0.8 0.8];
        app.savecoefsCheckBox.Position = [14 51 90 22];

        app.ZernikeProjectionCheckBox = uicheckbox(p);
        app.ZernikeProjectionCheckBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ZernikeProjectionCheckBox.Tooltip = {'Perform aberration compensation with Shack Hartmann simulation'};
        app.ZernikeProjectionCheckBox.Text = 'Zernike Projection';
        app.ZernikeProjectionCheckBox.FontColor = [0.902 0.902 0.902];
        app.ZernikeProjectionCheckBox.Position = [13 255 119 22];
        app.ZernikeProjectionCheckBox.Value = true;

        app.referenceimageDropDownLabel = uilabel(p);
        app.referenceimageDropDownLabel.HorizontalAlignment = 'right';
        app.referenceimageDropDownLabel.FontColor = [0.902 0.902 0.902];
        app.referenceimageDropDownLabel.Position = [7 135 92 22];
        app.referenceimageDropDownLabel.Text = 'reference image';

        app.referenceimageDropDown = uidropdown(p);
        app.referenceimageDropDown.Items = {'central subaperture', 'resized image'};
        app.referenceimageDropDown.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.referenceimageDropDown.FontColor = [0.9412 0.9412 0.9412];
        app.referenceimageDropDown.BackgroundColor = [0.502 0.502 0.502];
        app.referenceimageDropDown.Position = [114 135 135 18];
        app.referenceimageDropDown.Value = 'central subaperture';

        app.SubApNumPositionsLabel = uilabel(p);
        app.SubApNumPositionsLabel.FontColor = [0.8 0.8 0.8];
        app.SubApNumPositionsLabel.Position = [12 207 115 22];
        app.SubApNumPositionsLabel.Text = 'subap num positions';

        app.SubApNumPositions = uieditfield(p, 'numeric');
        app.SubApNumPositions.Limits = [1 20];
        app.SubApNumPositions.RoundFractionalValues = 'on';
        app.SubApNumPositions.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.SubApNumPositions.FontColor = [0.8 0.8 0.8];
        app.SubApNumPositions.BackgroundColor = [0.149 0.149 0.149];
        app.SubApNumPositions.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
        app.SubApNumPositions.Position = [142 207 43 22];
        app.SubApNumPositions.Value = 5;

        app.imageSubApSizeRatioLabel = uilabel(p);
        app.imageSubApSizeRatioLabel.FontColor = [0.8 0.8 0.8];
        app.imageSubApSizeRatioLabel.Position = [12 184 125 22];
        app.imageSubApSizeRatioLabel.Text = 'image subap size ratio';

        app.imageSubApSizeRatio = uieditfield(p, 'numeric');
        app.imageSubApSizeRatio.Limits = [1 20];
        app.imageSubApSizeRatio.RoundFractionalValues = 'on';
        app.imageSubApSizeRatio.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.imageSubApSizeRatio.FontColor = [0.8 0.8 0.8];
        app.imageSubApSizeRatio.BackgroundColor = [0.149 0.149 0.149];
        app.imageSubApSizeRatio.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
        app.imageSubApSizeRatio.Position = [142 184 43 22];
        app.imageSubApSizeRatio.Value = 5;

        app.numberofiterationLabel = uilabel(p);
        app.numberofiterationLabel.HorizontalAlignment = 'center';
        app.numberofiterationLabel.FontColor = [0.8 0.8 0.8];
        app.numberofiterationLabel.Position = [149 309 105 22];
        app.numberofiterationLabel.Text = 'number of iteration';

        app.NumberOfIteration = uieditfield(p, 'numeric');
        app.NumberOfIteration.Limits = [1 Inf];
        app.NumberOfIteration.RoundFractionalValues = 'on';
        app.NumberOfIteration.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.NumberOfIteration.FontColor = [0.8 0.8 0.8];
        app.NumberOfIteration.BackgroundColor = [0.149 0.149 0.149];
        app.NumberOfIteration.Tooltip = {'Number of zernike ranks to use for aberration correction'};
        app.NumberOfIteration.Position = [268 309 27 22];
        app.NumberOfIteration.Value = 3;

        app.calibrationfactorLabel = uilabel(p);
        app.calibrationfactorLabel.HorizontalAlignment = 'center';
        app.calibrationfactorLabel.FontColor = [0.8 0.8 0.8];
        app.calibrationfactorLabel.Visible = 'off';
        app.calibrationfactorLabel.Position = [149 159 93 22];
        app.calibrationfactorLabel.Text = 'calibration factor';

        app.CalibrationFactor = uieditfield(p, 'numeric');
        app.CalibrationFactor.Limits = [0 Inf];
        app.CalibrationFactor.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.CalibrationFactor.FontColor = [0.8 0.8 0.8];
        app.CalibrationFactor.BackgroundColor = [0.149 0.149 0.149];
        app.CalibrationFactor.Visible = 'off';
        app.CalibrationFactor.Tooltip = {'Number of zernike ranks to use for aberration correction'};
        app.CalibrationFactor.Position = [268 158 27 22];
        app.CalibrationFactor.Value = 60;

        app.calibrationfactorLabel_2 = uilabel(p);
        app.calibrationfactorLabel_2.HorizontalAlignment = 'center';
        app.calibrationfactorLabel_2.FontColor = [0.8 0.8 0.8];
        app.calibrationfactorLabel_2.Position = [133 284 126 22];
        app.calibrationfactorLabel_2.Text = 'convergence threshold';

        app.ConvergenceThreshold = uieditfield(p, 'numeric');
        app.ConvergenceThreshold.Limits = [0 Inf];
        app.ConvergenceThreshold.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ConvergenceThreshold.FontColor = [0.8 0.8 0.8];
        app.ConvergenceThreshold.BackgroundColor = [0.149 0.149 0.149];
        app.ConvergenceThreshold.Tooltip = {'Number of zernike ranks to use for aberration correction'};
        app.ConvergenceThreshold.Position = [268 283 27 22];
        app.ConvergenceThreshold.Value = 0.5;

        app.onlydefocusCheckBox = uicheckbox(p);
        app.onlydefocusCheckBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.onlydefocusCheckBox.Tooltip = {'Activate aberration compensation via image entropy optimization. This might significantly increase the computation time.'};
        app.onlydefocusCheckBox.Text = 'only defocus';
        app.onlydefocusCheckBox.FontColor = [0.902 0.902 0.902];
        app.onlydefocusCheckBox.Position = [149 255 89 22];
    end

    % -----------------------------------------------------------------------
    function createRenderingParametersPanel(app)

        backgroundColor = [0.2 0.2 0.2];
        darkBackgroundColor = [0.15 0.15 0.15];
        fontColor = [0.9 0.9 0.9];
        grayButtonColor = [0.5 0.5 0.5];

        app.RenderingParametersPanel = uipanel(app.RenderingInnerGrid);
        app.RenderingParametersPanel.ForegroundColor = [0.8 0.8 0.8];
        app.RenderingParametersPanel.Title = 'Rendering parameters';
        app.RenderingParametersPanel.BackgroundColor = [0.2 0.2 0.2];
        app.RenderingParametersPanel.Layout.Row = 1;
        app.RenderingParametersPanel.Layout.Column = 1;

        app.RenderingParametersGrid = uigridlayout(app.RenderingParametersPanel, [12 3]);
        app.RenderingParametersGrid.RowHeight = {'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit', 'fit'};
        app.RenderingParametersGrid.ColumnWidth = {'fit', '1x', '1x'};
        app.RenderingParametersGrid.Padding = [10 10 10 10];
        app.RenderingParametersGrid.RowSpacing = 5;
        app.RenderingParametersGrid.ColumnSpacing = 5;
        app.RenderingParametersGrid.BackgroundColor = backgroundColor;

        p = app.RenderingParametersGrid;

        % Spatial filtering parameters row 1

        app.spatialFilter = uicheckbox(p);
        app.spatialFilter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatialFilter.Tooltip = {'Filter the spatial frequencies of the interferograms keeping only those between spatial filter range1 and 2 (between 0 and 1-> highest dimension)'};
        app.spatialFilter.Text = 'Spatial filter';
        app.spatialFilter.FontColor = fontColor;
        app.spatialFilter.Layout.Column = 1;
        app.spatialFilter.Layout.Row = 1;

        app.spatialFilterRange1 = uieditfield(p, 'numeric');
        app.spatialFilterRange1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatialFilterRange1.FontColor = fontColor;
        app.spatialFilterRange1.BackgroundColor = darkBackgroundColor;
        app.spatialFilterRange1.Layout.Column = 2;
        app.spatialFilterRange1.Layout.Row = 1;

        app.spatialFilterRange2 = uieditfield(p, 'numeric');
        app.spatialFilterRange2.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatialFilterRange2.FontColor = fontColor;
        app.spatialFilterRange2.BackgroundColor = darkBackgroundColor;
        app.spatialFilterRange2.Layout.Column = 3;
        app.spatialFilterRange2.Layout.Row = 1;

        % Padding row 2
        app.PaddNLabel = uilabel(p);
        app.PaddNLabel.HorizontalAlignment = 'right';
        app.PaddNLabel.FontColor = fontColor;
        app.PaddNLabel.Layout.Column = 2;
        app.PaddNLabel.Layout.Row = 2;
        app.PaddNLabel.Text = 'Padding N';

        app.Padding_num = uieditfield(p, 'numeric');
        app.Padding_num.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.Padding_num.FontColor = fontColor;
        app.Padding_num.BackgroundColor = darkBackgroundColor;
        app.Padding_num.Tooltip = {'Distance of spatial reconstruction using the preceding calculation scheme in (m) '};
        app.Padding_num.Layout.Column = 3;
        app.Padding_num.Layout.Row = 2;

        % Local spatial transformation row 3

        app.spatial_transformationDropDownLabel = uilabel(p);
        app.spatial_transformationDropDownLabel.HorizontalAlignment = 'left';
        app.spatial_transformationDropDownLabel.FontColor = fontColor;
        app.spatial_transformationDropDownLabel.Layout.Column = 1;
        app.spatial_transformationDropDownLabel.Layout.Row = 3;
        app.spatial_transformationDropDownLabel.Text = 'Spatial transformation';

        app.spatial_transformation = uidropdown(p);
        app.spatial_transformation.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_transformation.Tooltip = {'Type of light propagation calculation to perform (depends of the experimental setup)'};
        app.spatial_transformation.FontColor = fontColor;
        app.spatial_transformation.BackgroundColor = grayButtonColor;
        app.spatial_transformation.Layout.Column = [2 3];
        app.spatial_transformation.Layout.Row = 3;
        app.spatial_transformation.Items = {'Angular spectrum', 'Fresnel', 'Fraunhofer', 'None'};

        % Spatial propagation row 4

        app.spatial_propagationLabel = uilabel(p);
        app.spatial_propagationLabel.HorizontalAlignment = 'left';
        app.spatial_propagationLabel.FontColor = fontColor;
        app.spatial_propagationLabel.Layout.Column = 1;
        app.spatial_propagationLabel.Layout.Row = 4;
        app.spatial_propagationLabel.Text = 'Spatial propagation';

        app.spatial_propagation = uieditfield(p, 'numeric');
        app.spatial_propagation.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_propagation.FontColor = fontColor;
        app.spatial_propagation.BackgroundColor = darkBackgroundColor;
        app.spatial_propagation.Tooltip = {'Distance of spatial reconstruction using the preceding calculation scheme in (m) '};
        app.spatial_propagation.Layout.Column = 2;
        app.spatial_propagation.Layout.Row = 4;

        app.AutofocusButton = uibutton(p, 'push');
        app.AutofocusButton.ButtonPushedFcn = createCallbackFcn(app, @AutofocusButtonPushed2, true);
        app.AutofocusButton.BackgroundColor = grayButtonColor;
        app.AutofocusButton.FontColor = fontColor;
        app.AutofocusButton.Layout.Column = 3;
        app.AutofocusButton.Layout.Row = 4;
        app.AutofocusButton.Text = 'Autofocus';

        % SVD filtering row 5 6 7

        app.svd_filter = uicheckbox(p);
        app.svd_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svd_filter.Tooltip = {'Filter to remove intense time correlated feature images of the output fluctuation hologram using eigenvalue decomposition of the correlation matrix of frames.'};
        app.svd_filter.Text = 'SVD Filter';
        app.svd_filter.FontColor = fontColor;
        app.svd_filter.Layout.Column = 1;
        app.svd_filter.Layout.Row = 5;

        app.svdThreshold_reset_button = uibutton(p, 'push');
        app.svdThreshold_reset_button.ButtonPushedFcn = createCallbackFcn(app, @svdThreshold_reset_buttonPushed, true);
        app.svdThreshold_reset_button.BackgroundColor = grayButtonColor;
        app.svdThreshold_reset_button.FontColor = fontColor;
        app.svdThreshold_reset_button.Layout.Column = 2;
        app.svdThreshold_reset_button.Layout.Row = 5;
        app.svdThreshold_reset_button.Text = 'Reset';
        app.svdThreshold = uieditfield(p, 'numeric');
        app.svdThreshold.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdThreshold.FontColor = fontColor;
        app.svdThreshold.BackgroundColor = darkBackgroundColor;
        app.svdThreshold.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => frequencyRange(1)/fs * batchSize * 2)'};
        app.svdThreshold.Layout.Column = 3;
        app.svdThreshold.Layout.Row = 5;

        % Time transformation row 6
        app.time_transformDropDownLabel = uilabel(p);
        app.time_transformDropDownLabel.FontColor = fontColor;
        app.time_transformDropDownLabel.Layout.Column = 1;
        app.time_transformDropDownLabel.Layout.Row = 6;
        app.time_transformDropDownLabel.Text = 'Time transform';

        app.time_transform = uidropdown(p);
        app.time_transform.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.time_transform.Tooltip = {'Time tranformation to aggregate the fluctuation hologram. FFT is a frequency domain tranform and pass bad filter, PCA is a projection on intensity ordered eigen vectors, ICA is experimental.'};
        app.time_transform.FontColor = fontColor;
        app.time_transform.BackgroundColor = grayButtonColor;
        app.time_transform.Layout.Column = [2 3];
        app.time_transform.Layout.Row = 6;
        app.time_transform.Items = {'FFT', 'PCA', 'ICA'};

        % Frequency range row 7 8 9
        app.frequencyRangeLabel = uilabel(p);
        app.frequencyRangeLabel.FontColor = fontColor;
        app.frequencyRangeLabel.Text = 'Frequency Range';
        app.frequencyRangeLabel.Layout.Column = 1;
        app.frequencyRangeLabel.Layout.Row = 7;

        app.frequencyRange1 = uieditfield(p, 'numeric');
        app.frequencyRange1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.frequencyRange1.FontColor = fontColor;
        app.frequencyRange1.BackgroundColor = darkBackgroundColor;
        app.frequencyRange1.Layout.Column = 2;
        app.frequencyRange1.Layout.Row = 7;
        app.frequencyRange1.Tooltip = {'Frequency range to apply the time transformation (if different from time range)'};
        app.frequencyRange1.Placeholder = 'f1';

        app.frequencyRange2 = uieditfield(p, 'numeric');
        app.frequencyRange2.ValueChangedFcn = createCallbackFcn(app, @frequencyRange2ValueChanged, true);
        app.frequencyRange2.FontColor = fontColor;
        app.frequencyRange2.BackgroundColor = darkBackgroundColor;
        app.frequencyRange2.Layout.Column = 3;
        app.frequencyRange2.Layout.Row = 7;
        app.frequencyRange2.Tooltip = {'Frequency range to apply the time transformation (if different from time range)'};
        app.frequencyRange2.Placeholder = 'f2';

        app.frequencyRangeInterLabel = uilabel(p);
        app.frequencyRangeInterLabel.FontColor = fontColor;
        app.frequencyRangeInterLabel.Text = 'Intermediary Time Range';
        app.frequencyRangeInterLabel.Layout.Column = 1;
        app.frequencyRangeInterLabel.Layout.Row = 8;

        app.frequencyRangeInter1 = uieditfield(p, 'numeric');
        app.frequencyRangeInter1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.frequencyRangeInter1.FontColor = fontColor;
        app.frequencyRangeInter1.BackgroundColor = darkBackgroundColor;
        app.frequencyRangeInter1.Layout.Column = 2;
        app.frequencyRangeInter1.Layout.Row = 8;
        app.frequencyRangeInter1.Tooltip = {'Frequency range to apply the intermediary time transformation (if different from time range)'};
        app.frequencyRangeInter1.Placeholder = 'fi1';

        app.frequencyRangeInter2 = uieditfield(p, 'numeric');
        app.frequencyRangeInter2.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.frequencyRangeInter2.FontColor = fontColor;
        app.frequencyRangeInter2.BackgroundColor = darkBackgroundColor;
        app.frequencyRangeInter2.Layout.Column = 3;
        app.frequencyRangeInter2.Layout.Row = 8;
        app.frequencyRangeInter2.Tooltip = {'Frequency range to apply the intermediary time transformation (if different from time range)'};
        app.frequencyRangeInter2.Placeholder = 'fi2';

        app.indexRangeLabel = uilabel(p);
        app.indexRangeLabel.FontColor = fontColor;
        app.indexRangeLabel.Text = 'Index range';
        app.indexRangeLabel.Layout.Column = 1;
        app.indexRangeLabel.Layout.Row = 9;

        app.indexRange1 = uieditfield(p, 'numeric');
        app.indexRange1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.indexRange1.FontColor = fontColor;
        app.indexRange1.BackgroundColor = darkBackgroundColor;
        app.indexRange1.Layout.Column = 2;
        app.indexRange1.Layout.Row = 9;

        app.indexRange2 = uieditfield(p, 'numeric');
        app.indexRange2.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.indexRange2.FontColor = fontColor;
        app.indexRange2.BackgroundColor = darkBackgroundColor;
        app.indexRange2.Layout.Column = 3;
        app.indexRange2.Layout.Row = 9;

        % Other parameters row 10 11 12

        app.flat_field_gwLabel = uilabel(p);
        app.flat_field_gwLabel.HorizontalAlignment = 'left';
        app.flat_field_gwLabel.FontColor = fontColor;
        app.flat_field_gwLabel.Text = 'Flatfield';
        app.flat_field_gwLabel.Layout.Column = 1;
        app.flat_field_gwLabel.Layout.Row = 10;

        app.flat_field_gw = uieditfield(p, 'numeric');
        app.flat_field_gw.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flat_field_gw.FontColor = [1 1 1];
        app.flat_field_gw.BackgroundColor = [0.149 0.149 0.149];
        app.flat_field_gw.Tooltip = {'flat_filed parameter to apply to some of the output images (gaussian width in pixels to divide the image to correct uneven illumination of images).'};
        app.flat_field_gw.Layout.Column = 2;
        app.flat_field_gw.Layout.Row = 10;

        app.flip_y = uicheckbox(p);
        app.flip_y.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_y.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.flip_y.Text = 'Flip y';
        app.flip_y.FontColor = fontColor;
        app.flip_y.Layout.Column = 3;
        app.flip_y.Layout.Row = 11;

        app.flip_x = uicheckbox(p);
        app.flip_x.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_x.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.flip_x.Text = 'Flip x';
        app.flip_x.FontColor = fontColor;
        app.flip_x.Layout.Column = 2;
        app.flip_x.Layout.Row = 11;

        app.square = uicheckbox(p);
        app.square.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.square.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.square.Text = 'Square';
        app.square.FontColor = fontColor;
        app.square.Layout.Column = 1;
        app.square.Layout.Row = 11;

        app.RenderPreviewButton = uibutton(p, 'push');
        app.RenderPreviewButton.ButtonPushedFcn = createCallbackFcn(app, @RenderPreviewButtonPushed, true);
        app.RenderPreviewButton.BackgroundColor = grayButtonColor;
        app.RenderPreviewButton.FontColor = fontColor;
        app.RenderPreviewButton.Layout.Column = 2;
        app.RenderPreviewButton.Layout.Row = 12;
        app.RenderPreviewButton.Text = 'Render';

        app.SavePreviewButton = uibutton(p, 'push');
        app.SavePreviewButton.ButtonPushedFcn = createCallbackFcn(app, @SavePreviewButtonPushed, true);
        app.SavePreviewButton.BackgroundColor = grayButtonColor;
        app.SavePreviewButton.FontColor = fontColor;
        app.SavePreviewButton.Layout.Column = 3;
        app.SavePreviewButton.Layout.Row = 12;
        app.SavePreviewButton.Text = 'Save';

        app.RenderPreviewLamp = uilamp(p);
        app.RenderPreviewLamp.Color = [0.8 0.8 0.8];
        app.RenderPreviewLamp.Layout.Column = 1;
        app.RenderPreviewLamp.Layout.Row = 12;
    end

    % -----------------------------------------------------------------------
    function createImageViewsAndMenus(app)
        app.ImageRight = uiimage(app.RootGrid);
        app.ImageRight.Layout.Row = 1;
        app.ImageRight.Layout.Column = 3;

        app.ImageLeft = uiimage(app.RootGrid);
        app.ImageLeft.Layout.Row = 1;
        app.ImageLeft.Layout.Column = 2;

        app.PanelPlot = uipanel(app.RootGrid);
        app.PanelPlot.Title = 'Plot';
        app.PanelPlot.Visible = 'off';
        app.PanelPlot.BackgroundColor = [1 1 1];
        app.PanelPlot.Layout.Row = 1;
        app.PanelPlot.Layout.Column = 3;

        app.RightClickImageContextMenu = uicontextmenu(app.HoloDopplerUIFigure);

        app.NextMenu = uimenu(app.RightClickImageContextMenu);
        app.NextMenu.MenuSelectedFcn = createCallbackFcn(app, @NextMenuSelected, true);
        app.NextMenu.Text = 'Next';

        app.ViewAllMenu = uimenu(app.RightClickImageContextMenu);
        app.ViewAllMenu.MenuSelectedFcn = createCallbackFcn(app, @ViewAllMenuSelected, true);
        app.ViewAllMenu.Text = 'ViewAll';

        app.ImageLeft.ContextMenu = app.RightClickImageContextMenu;
    end

end % createComponents methods block

% =========================================================================
% App construction and deletion
% =========================================================================
methods (Access = public)

    function app = HoloDopplerApp
        createComponents(app)
        registerApp(app, app.HoloDopplerUIFigure)
        runStartupFcn(app, @startupFcn)

        if nargout == 0
            clear app
        end

    end

    function delete(app)
        delete(app.HoloDopplerUIFigure)
    end

end

end
