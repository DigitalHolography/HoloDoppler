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
    batchIndexField matlab.ui.control.NumericEditField
    batchIndexLabel matlab.ui.control.Label
    framePosition matlab.ui.control.NumericEditField

    % ---- batch / video rendering sub-panel ----
    batchPanel matlab.ui.container.Panel
    batchGrid matlab.ui.container.GridLayout
    Image_typesListBox matlab.ui.control.ListBox
    LoadConfigButton matlab.ui.control.Button
    SaveConfigButton matlab.ui.control.Button
    FolderManagementButton matlab.ui.control.Button
    VideoRenderingButton matlab.ui.control.Button
    ShowHistogramButton matlab.ui.control.Button
    VideoRenderingLamp matlab.ui.control.Lamp
    batchSizeLabel matlab.ui.control.Label
    batchSize matlab.ui.control.NumericEditField
    batchStrideLabel matlab.ui.control.Label
    batchStride matlab.ui.control.NumericEditField
    refBatchSizeLabel matlab.ui.control.Label
    refBatchSize matlab.ui.control.NumericEditField
    AutofocusFromRef matlab.ui.control.CheckBox
    applyShackHartmannfromRef matlab.ui.control.CheckBox
    imageRegistration matlab.ui.control.CheckBox
    registrationDiskLabel matlab.ui.control.Label
    registrationDiskRatio matlab.ui.control.NumericEditField

    % ---- rendering parameters panel ----
    renderingParametersPanel matlab.ui.container.Panel
    renderingParametersGrid matlab.ui.container.GridLayout
    spatialFilter matlab.ui.control.CheckBox
    spatialFilterRange1 matlab.ui.control.NumericEditField
    spatialFilterRange2 matlab.ui.control.NumericEditField
    PaddingLabel matlab.ui.control.Label
    PaddingNum matlab.ui.control.NumericEditField
    spatialTransformationLabel matlab.ui.control.Label
    spatialTransformation matlab.ui.control.DropDown
    spatialPropagationLabel matlab.ui.control.Label
    spatialPropagation matlab.ui.control.NumericEditField
    AutofocusButton matlab.ui.control.Button
    svd_filter matlab.ui.control.CheckBox
    svdThresholdResetButton matlab.ui.control.Button
    svdThreshold matlab.ui.control.NumericEditField
    svdStrideLabel matlab.ui.control.Label
    svdStride matlab.ui.control.NumericEditField
    timeTransformLabel matlab.ui.control.Label
    timeTransform matlab.ui.control.DropDown
    frequencyRangeLabel matlab.ui.control.Label
    frequencyRange1 matlab.ui.control.NumericEditField
    frequencyRange2 matlab.ui.control.NumericEditField
    frequencyRangeInterLabel matlab.ui.control.Label
    frequencyRangeInter1 matlab.ui.control.NumericEditField
    frequencyRangeInter2 matlab.ui.control.NumericEditField
    indexRangeLabel matlab.ui.control.Label
    indexRange1 matlab.ui.control.NumericEditField
    indexRange2 matlab.ui.control.NumericEditField
    flat_field_gwLabel matlab.ui.control.Label
    flat_field_gw matlab.ui.control.NumericEditField
    square matlab.ui.control.CheckBox
    flip_x matlab.ui.control.CheckBox
    flip_y matlab.ui.control.CheckBox
    RenderPreviewLamp matlab.ui.control.Lamp
    RenderPreviewButton matlab.ui.control.Button
    SavePreviewButton matlab.ui.control.Button

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
    MenuIndex
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
            case 'space'
                app.ViewAllMenuSelected();
            case 'leftarrow'
                app.changeMenu('previous');
            case 'rightarrow'
                app.changeMenu('next');
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

        app.refreshClass();
    end

    function LoadConfigButtonPushed(app, ~)
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

    function SaveConfigButtonPushed(app, ~)

        try
            outputPath = app.HD.saveParams();
            fprintf("Config saved successfully to %s\n", outputPath);
        catch ME
            MEdisp(ME);
        end

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
            app.MenuIndex = 1;
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

    function SavePreviewButtonPushed(app, ~)
        app.HD.savePreview();
    end

    % --- UI state sync / refresh -------------------------------------------

    % Sync every widget value into the HD class, then update enable states.
    % Connected to ~50 component ValueChanged callbacks.
    function refreshClass(app, ~)
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
        app.HD.params.spatialPropagation = zopti;
        app.syncGuiFromClass();
        app.RenderPreviewButtonPushed();
    end

    % --- Context menu / image navigation -----------------------------------

    function changeMenu(app, direction)

        idx = app.MenuIndex;
        imagesTypes = app.HD.params.image_types;

        if direction == "next"
            num = mod(idx, length(imagesTypes)) + 1;
            app.SelectMenu(num);
        elseif direction == "previous"
            num = mod(idx - 2, length(imagesTypes)) + 1;
            app.SelectMenu(num);
        end

    end

    function SelectMenu(app, num, ~)
        imgs = app.HD.view.getImages(app.HD.params.image_types);

        if ~isempty(imgs)

            image = imgs{num};
            maxSize = max(size(image));

            if ~ismember(app.HD.params.image_types{num}, {'broadening'}) && ...
                    size(image, 1) ~= size(image, 2)
                image = imresize(image, [maxSize, maxSize]);
            end

            imgs{num} = image;

            if ~isempty(imgs)
                app.ImageLeft.ImageSource = toImageSource(imgs{num}, app);
            else
                app.ImageLeft.ImageSource = '';
            end

        else
            app.ImageLeft.ImageSource = '';
        end

        app.MenuIndex = num;

    end

    function ViewAllMenuSelected(app, ~)
        app.HD.showPreviewImages();
    end

    % --- Misc callbacks ----------------------------------------------------

    function ShowHistogramButtonPushed(app, ~)
        app.HD.view.showFramesHistogram();
    end

    function svdThresholdResetButtonPushed(app, ~)

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

        if strcmp(app.timeTransform, 'FFT') && app.frequencyRange2.Value > app.fs.Value / 2
            app.frequencyRange2.Value = app.fs.Value / 2;
        end

        app.refreshClass();
    end

    function AdvancedButtonPushed(app, ~)
        AdvancedPanel(app);
    end

    function registrationDiskRatioValueChanged(app, ~)
        app.refreshClass();
        show_ref_disk(app, app.imageRegistration.Value);
    end

    function positioninfileSliderValueChanged(app, ~)

        if ~isempty(app.HD.file)
            app.framePosition.Value = app.positioninfileSlider.Value;
        else
            app.framePosition.Value = 1;
        end

        frame = app.framePosition.Value;
        stride = app.batchStride.Value;
        batchIndex = ceil(frame / stride);
        app.batchIndexField.Value = batchIndex;

        app.refreshClass();
    end

    function framePositionValueChanged(app, ~)

        if ~isempty(app.HD.file)
            app.positioninfileSlider.Value = app.framePosition.Value;
        else
            app.positioninfileSlider.Value = 0;
        end

        frame = app.framePosition.Value;
        stride = app.batchStride.Value;
        batchIndex = ceil(frame / stride);
        app.batchIndexField.Value = batchIndex;

        app.refreshClass();
    end

    % --- Folder management -------------------------------------------------

    function FolderManagementButtonPushed(app, ~)
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
        useFreqRange = ismember(app.timeTransform.Value, {'FFT', 'autocorrelation', 'intercorrelation'});
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
        app.createAberrationPanel();
        app.createrenderingParametersPanel();
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
        app.pixelPitchLabel.FontColor = fontColor;
        app.pixelPitchLabel.Tooltip = {'Camera pixel pitch (distance between spatial sampling points) in (m)'};
        app.pixelPitchLabel.Text = 'Pixel pitch (m)';
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
        app.imageSizeLabel.FontColor = fontColor;
        app.imageSizeLabel.Tooltip = {'Size of the recorded interferograms in pixels (width x height)'};
        app.imageSizeLabel.Text = 'Image size (px)';
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
        app.numworkersSpinnerLabel.FontColor = fontColor;
        app.numworkersSpinnerLabel.Tooltip = {'Number of worker used for the video rendering (depends of the working station)'};
        app.numworkersSpinnerLabel.Text = '# Workers';
        app.numworkersSpinnerLabel.Layout.Row = 6;
        app.numworkersSpinnerLabel.Layout.Column = 1;

        app.parfor_arg = uispinner(app.mainParametersGrid);
        app.parfor_arg.ValueChangingFcn = createCallbackFcn(app, @refreshClass, true);
        maxWorkers = parcluster('local').NumWorkers;
        app.parfor_arg.Limits = [-1 maxWorkers];
        app.parfor_arg.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.parfor_arg.FontColor = fontColor;
        app.parfor_arg.BackgroundColor = darkBackgroundColor;
        app.parfor_arg.Tooltip = {'Number of worker used for the video rendering (depends of the working station)'};
        app.parfor_arg.Value = 10;
        app.parfor_arg.Layout.Row = 6;
        app.parfor_arg.Layout.Column = 2;

        app.positioninfileSliderLabel = uilabel(app.mainParametersGrid);
        app.positioninfileSliderLabel.FontColor = fontColor;
        app.positioninfileSliderLabel.Text = {'Position in file'};
        app.positioninfileSliderLabel.Layout.Row = 7;
        app.positioninfileSliderLabel.Layout.Column = 1;

        app.positioninfileSlider = uislider(app.mainParametersGrid);
        app.positioninfileSlider.Limits = [0 1];
        app.positioninfileSlider.MajorTicks = [];
        app.positioninfileSlider.ValueChangedFcn = createCallbackFcn(app, @positioninfileSliderValueChanged, true);
        app.positioninfileSlider.MinorTicks = [0 0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 1];
        app.positioninfileSlider.Tooltip = {'Change value to display a different video timestamp in the gui.'};
        app.positioninfileSlider.Layout.Row = 7;
        app.positioninfileSlider.Layout.Column = [2 3];

        app.batchIndexLabel = uilabel(app.mainParametersGrid);
        app.batchIndexLabel.FontColor = fontColor;
        app.batchIndexLabel.Text = {'Batch index'};
        app.batchIndexLabel.Layout.Row = 8;
        app.batchIndexLabel.Layout.Column = 1;

        app.batchIndexField = uieditfield(app.mainParametersGrid, 'numeric');
        app.batchIndexField.Editable = 'off';
        app.batchIndexField.FontColor = fontColor;
        app.batchIndexField.BackgroundColor = darkBackgroundColor;
        app.batchIndexField.ValueDisplayFormat = '%.0f';
        app.batchIndexField.Layout.Row = 8;
        app.batchIndexField.Layout.Column = 2;

        app.framePosition = uieditfield(app.mainParametersGrid, 'numeric');
        app.framePosition.Limits = [0 Inf];
        app.framePosition.RoundFractionalValues = 'on';
        app.framePosition.ValueDisplayFormat = '%.0f';
        app.framePosition.ValueChangedFcn = createCallbackFcn(app, @framePositionValueChanged, true);
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
        app.LoadConfigButton = uibutton(p, 'push');
        app.LoadConfigButton.ButtonPushedFcn = createCallbackFcn(app, @LoadConfigButtonPushed, true);
        app.LoadConfigButton.BackgroundColor = grayButtonColor;
        app.LoadConfigButton.FontColor = fontColor;
        app.LoadConfigButton.Tooltip = {'Save a configuration for the video rendering of a file'};
        app.LoadConfigButton.Layout.Row = 2;
        app.LoadConfigButton.Layout.Column = 1;
        app.LoadConfigButton.Text = 'Load config';

        app.SaveConfigButton = uibutton(p, 'push');
        app.SaveConfigButton.ButtonPushedFcn = createCallbackFcn(app, @SaveConfigButtonPushed, true);
        app.SaveConfigButton.BackgroundColor = grayButtonColor;
        app.SaveConfigButton.FontColor = fontColor;
        app.SaveConfigButton.Tooltip = {'Save a configuration for the video rendering of a file'};
        app.SaveConfigButton.Layout.Row = 2;
        app.SaveConfigButton.Layout.Column = 2;
        app.SaveConfigButton.Text = 'Save config';

        % buttons row 3
        app.FolderManagementButton = uibutton(p, 'push');
        app.FolderManagementButton.ButtonPushedFcn = createCallbackFcn(app, @FolderManagementButtonPushed, true);
        app.FolderManagementButton.BackgroundColor = grayButtonColor;
        app.FolderManagementButton.FontColor = fontColor;
        app.FolderManagementButton.Tooltip = {'Open a window to render all files from different folders with their config files'};
        app.FolderManagementButton.Layout.Row = 3;
        app.FolderManagementButton.Layout.Column = 1;
        app.FolderManagementButton.Text = 'Folder management';

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
        app.batchSizeLabel.FontColor = fontColor;
        app.batchSizeLabel.Layout.Row = 5;
        app.batchSizeLabel.Layout.Column = 1;
        app.batchSizeLabel.Text = 'Batch size';

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
        app.batchStrideLabel.FontColor = fontColor;
        app.batchStrideLabel.Layout.Row = 6;
        app.batchStrideLabel.Layout.Column = 1;
        app.batchStrideLabel.Text = 'Batch stride';

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
        app.refBatchSizeLabel.FontColor = fontColor;
        app.refBatchSizeLabel.Layout.Row = 7;
        app.refBatchSizeLabel.Layout.Column = 1;
        app.refBatchSizeLabel.Text = 'Reference batch size';

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

        app.applyShackHartmannfromRef = uicheckbox(p);
        app.applyShackHartmannfromRef.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.applyShackHartmannfromRef.Tooltip = {'Activate frame to frame translation registration of images'};
        app.applyShackHartmannfromRef.Text = 'refocus from ref (numeric shack hartmann)';
        app.applyShackHartmannfromRef.FontColor = fontColor;
        app.applyShackHartmannfromRef.Layout.Row = 9;
        app.applyShackHartmannfromRef.Layout.Column = [1 2];

        app.imageRegistration = uicheckbox(p);
        app.imageRegistration.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.imageRegistration.Tooltip = {'Activate frame to frame translation registration of images'};
        app.imageRegistration.Text = 'image registration';
        app.imageRegistration.FontColor = fontColor;
        app.imageRegistration.Layout.Row = 10;
        app.imageRegistration.Layout.Column = [1 2];

        app.registrationDiskLabel = uilabel(p);
        app.registrationDiskLabel.FontColor = fontColor;
        app.registrationDiskLabel.Layout.Row = 11;
        app.registrationDiskLabel.Layout.Column = 1;
        app.registrationDiskLabel.Text = 'Registration disk ratio';

        app.registrationDiskRatio = uieditfield(p, 'numeric');
        app.registrationDiskRatio.Limits = [0 1000];
        app.registrationDiskRatio.ValueChangedFcn = createCallbackFcn(app, @registrationDiskRatioValueChanged, true);
        app.registrationDiskRatio.FontColor = fontColor;
        app.registrationDiskRatio.BackgroundColor = darkBackgroundColor;
        app.registrationDiskRatio.Tooltip = {'Size of a disk centered on the images used to compute the registration shifts (0 is empty and 1 is a disk of the maximum dimension).'};
        app.registrationDiskRatio.Layout.Row = 11;
        app.registrationDiskRatio.Layout.Column = 2;

    end

    % -----------------------------------------------------------------------
    function createCurrentFileStrip(app)
        app.CurrentFileGrid = uigridlayout(app.RootGrid);
        app.CurrentFileGrid.ColumnWidth = {'1x', '1x'};
        app.CurrentFileGrid.RowHeight = {'1x'};
        app.CurrentFileGrid.BackgroundColor = [0.2 0.2 0.2];
        app.CurrentFileGrid.Layout.Row = 2;
        app.CurrentFileGrid.Layout.Column = [2 3];

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
    function createAberrationPanel(app)
        app.AberrationcompensationPanel = uipanel(app.CurrentFileGrid);
        app.AberrationcompensationPanel.ForegroundColor = [0.8 0.8 0.8];
        app.AberrationcompensationPanel.Title = 'Aberration compensation';
        app.AberrationcompensationPanel.BackgroundColor = [0.2 0.2 0.2];
        app.AberrationcompensationPanel.Layout.Row = 1;
        app.AberrationcompensationPanel.Layout.Column = 2;

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
    function createrenderingParametersPanel(app)

        backgroundColor = [0.2 0.2 0.2];
        darkBackgroundColor = [0.15 0.15 0.15];
        fontColor = [0.9 0.9 0.9];
        grayButtonColor = [0.5 0.5 0.5];

        app.renderingParametersPanel = uipanel(app.RenderingInnerGrid);
        app.renderingParametersPanel.ForegroundColor = [0.8 0.8 0.8];
        app.renderingParametersPanel.Title = 'Rendering parameters';
        app.renderingParametersPanel.BackgroundColor = [0.2 0.2 0.2];
        app.renderingParametersPanel.Layout.Row = 1;
        app.renderingParametersPanel.Layout.Column = 1;

        app.renderingParametersGrid = uigridlayout(app.renderingParametersPanel, [13 3]);
        app.renderingParametersGrid.RowHeight = repmat({'fit'}, 1, 13);
        app.renderingParametersGrid.ColumnWidth = {'fit', '1x', '1x'};
        app.renderingParametersGrid.Padding = [10 10 10 10];
        app.renderingParametersGrid.RowSpacing = 5;
        app.renderingParametersGrid.ColumnSpacing = 5;
        app.renderingParametersGrid.BackgroundColor = backgroundColor;

        p = app.renderingParametersGrid;

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
        app.PaddingLabel = uilabel(p);
        app.PaddingLabel.HorizontalAlignment = 'right';
        app.PaddingLabel.FontColor = fontColor;
        app.PaddingLabel.Layout.Column = 1;
        app.PaddingLabel.Layout.Row = 2;
        app.PaddingLabel.Text = 'Padding N';

        app.PaddingNum = uieditfield(p, 'numeric');
        app.PaddingNum.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.PaddingNum.FontColor = fontColor;
        app.PaddingNum.BackgroundColor = darkBackgroundColor;
        app.PaddingNum.Tooltip = {'Distance of spatial reconstruction using the preceding calculation scheme in (m) '};
        app.PaddingNum.Layout.Column = 2;
        app.PaddingNum.Layout.Row = 2;

        % Local spatial transformation row 3

        app.spatialTransformationLabel = uilabel(p);
        app.spatialTransformationLabel.HorizontalAlignment = 'right';
        app.spatialTransformationLabel.FontColor = fontColor;
        app.spatialTransformationLabel.Layout.Column = 1;
        app.spatialTransformationLabel.Layout.Row = 3;
        app.spatialTransformationLabel.Text = 'Spatial transformation';

        app.spatialTransformation = uidropdown(p);
        app.spatialTransformation.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatialTransformation.Tooltip = {'Type of light propagation calculation to perform (depends of the experimental setup)'};
        app.spatialTransformation.FontColor = fontColor;
        app.spatialTransformation.BackgroundColor = grayButtonColor;
        app.spatialTransformation.Layout.Column = [2 3];
        app.spatialTransformation.Layout.Row = 3;
        app.spatialTransformation.Items = {'Angular spectrum', 'Fresnel', 'None'};

        % Spatial propagation row 4

        app.spatialPropagationLabel = uilabel(p);
        app.spatialPropagationLabel.HorizontalAlignment = 'right';
        app.spatialPropagationLabel.FontColor = fontColor;
        app.spatialPropagationLabel.Layout.Column = 1;
        app.spatialPropagationLabel.Layout.Row = 4;
        app.spatialPropagationLabel.Text = 'Spatial propagation';

        app.spatialPropagation = uieditfield(p, 'numeric');
        app.spatialPropagation.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatialPropagation.FontColor = fontColor;
        app.spatialPropagation.BackgroundColor = darkBackgroundColor;
        app.spatialPropagation.Tooltip = {'Distance of spatial reconstruction using the preceding calculation scheme in (m) '};
        app.spatialPropagation.Layout.Column = 2;
        app.spatialPropagation.Layout.Row = 4;

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

        app.svdThresholdResetButton = uibutton(p, 'push');
        app.svdThresholdResetButton.ButtonPushedFcn = createCallbackFcn(app, @svdThresholdResetButtonPushed, true);
        app.svdThresholdResetButton.BackgroundColor = grayButtonColor;
        app.svdThresholdResetButton.FontColor = fontColor;
        app.svdThresholdResetButton.Layout.Column = 2;
        app.svdThresholdResetButton.Layout.Row = 5;
        app.svdThresholdResetButton.Text = 'Reset';

        app.svdThreshold = uieditfield(p, 'numeric');
        app.svdThreshold.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdThreshold.FontColor = fontColor;
        app.svdThreshold.BackgroundColor = darkBackgroundColor;
        app.svdThreshold.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => frequencyRange(1)/fs * batchSize * 2)'};
        app.svdThreshold.Layout.Column = 3;
        app.svdThreshold.Layout.Row = 5;

        app.svdStrideLabel = uilabel(p);
        app.svdStrideLabel.HorizontalAlignment = 'right';
        app.svdStrideLabel.FontColor = fontColor;
        app.svdStrideLabel.Layout.Column = 1;
        app.svdStrideLabel.Layout.Row = 6;
        app.svdStrideLabel.Text = 'SVD stride';

        app.svdStride = uieditfield(p, 'numeric');
        app.svdStride.Limits = [0 Inf];
        app.svdStride.Tooltip = {'Sub sampling parameter for faster SVD calculations. Defaults to 1 -> full image, 2 -> one pixel on two, ...'};
        app.svdStride.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdStride.FontColor = fontColor;
        app.svdStride.BackgroundColor = darkBackgroundColor;
        app.svdStride.Layout.Row = 6;
        app.svdStride.Layout.Column = 2;
        app.svdStride.Value = 1;

        % Time transformation row 7
        app.timeTransformLabel = uilabel(p);
        app.timeTransformLabel.FontColor = fontColor;
        app.timeTransformLabel.Layout.Column = 1;
        app.timeTransformLabel.Layout.Row = 7;
        app.timeTransformLabel.Text = 'Time transform';
        app.timeTransformLabel.HorizontalAlignment = 'right';

        app.timeTransform = uidropdown(p);
        app.timeTransform.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.timeTransform.Tooltip = {'Time tranformation to aggregate the fluctuation hologram. FFT is a frequency domain tranform and pass bad filter, PCA is a projection on intensity ordered eigen vectors, ICA is experimental.'};
        app.timeTransform.FontColor = fontColor;
        app.timeTransform.BackgroundColor = grayButtonColor;
        app.timeTransform.Layout.Column = [2 3];
        app.timeTransform.Layout.Row = 7;
        app.timeTransform.Items = {'FFT', 'PCA', 'ICA'};

        % Frequency range row 8 9 10
        app.frequencyRangeLabel = uilabel(p);
        app.frequencyRangeLabel.FontColor = fontColor;
        app.frequencyRangeLabel.Text = 'Frequency Range';
        app.frequencyRangeLabel.Layout.Column = 1;
        app.frequencyRangeLabel.Layout.Row = 8;
        app.frequencyRangeLabel.HorizontalAlignment = 'right';

        app.frequencyRange1 = uieditfield(p, 'numeric');
        app.frequencyRange1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.frequencyRange1.FontColor = fontColor;
        app.frequencyRange1.BackgroundColor = darkBackgroundColor;
        app.frequencyRange1.Layout.Column = 2;
        app.frequencyRange1.Layout.Row = 8;
        app.frequencyRange1.Tooltip = {'Frequency range to apply the time transformation (if different from time range)'};
        app.frequencyRange1.Placeholder = 'f1';

        app.frequencyRange2 = uieditfield(p, 'numeric');
        app.frequencyRange2.ValueChangedFcn = createCallbackFcn(app, @frequencyRange2ValueChanged, true);
        app.frequencyRange2.FontColor = fontColor;
        app.frequencyRange2.BackgroundColor = darkBackgroundColor;
        app.frequencyRange2.Layout.Column = 3;
        app.frequencyRange2.Layout.Row = 8;
        app.frequencyRange2.Tooltip = {'Frequency range to apply the time transformation (if different from time range)'};
        app.frequencyRange2.Placeholder = 'f2';

        app.frequencyRangeInterLabel = uilabel(p);
        app.frequencyRangeInterLabel.FontColor = fontColor;
        app.frequencyRangeInterLabel.Text = 'Inter freq range';
        app.frequencyRangeInterLabel.Layout.Row = 9;
        app.frequencyRangeInterLabel.Layout.Column = 1;
        app.frequencyRangeInterLabel.HorizontalAlignment = 'right';

        app.frequencyRangeInter1 = uieditfield(p, 'numeric');
        app.frequencyRangeInter1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.frequencyRangeInter1.FontColor = fontColor;
        app.frequencyRangeInter1.BackgroundColor = darkBackgroundColor;
        app.frequencyRangeInter1.Layout.Column = 2;
        app.frequencyRangeInter1.Layout.Row = 9;
        app.frequencyRangeInter1.Tooltip = {'Frequency range to apply the intermediary time transformation (if different from time range)'};
        app.frequencyRangeInter1.Placeholder = 'fi1';

        app.frequencyRangeInter2 = uieditfield(p, 'numeric');
        app.frequencyRangeInter2.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.frequencyRangeInter2.FontColor = fontColor;
        app.frequencyRangeInter2.BackgroundColor = darkBackgroundColor;
        app.frequencyRangeInter2.Layout.Column = 3;
        app.frequencyRangeInter2.Layout.Row = 9;
        app.frequencyRangeInter2.Tooltip = {'Frequency range to apply the intermediary time transformation (if different from time range)'};
        app.frequencyRangeInter2.Placeholder = 'fi2';

        app.indexRangeLabel = uilabel(p);
        app.indexRangeLabel.FontColor = fontColor;
        app.indexRangeLabel.Text = 'Index range';
        app.indexRangeLabel.Layout.Column = 1;
        app.indexRangeLabel.Layout.Row = 10;
        app.indexRangeLabel.HorizontalAlignment = 'right';

        app.indexRange1 = uieditfield(p, 'numeric');
        app.indexRange1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.indexRange1.FontColor = fontColor;
        app.indexRange1.BackgroundColor = darkBackgroundColor;
        app.indexRange1.Layout.Column = 2;
        app.indexRange1.Layout.Row = 10;

        app.indexRange2 = uieditfield(p, 'numeric');
        app.indexRange2.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.indexRange2.FontColor = fontColor;
        app.indexRange2.BackgroundColor = darkBackgroundColor;
        app.indexRange2.Layout.Column = 3;
        app.indexRange2.Layout.Row = 10;

        % Other parameters row 11 12 13
        app.flat_field_gwLabel = uilabel(p);
        app.flat_field_gwLabel.HorizontalAlignment = 'right';
        app.flat_field_gwLabel.FontColor = fontColor;
        app.flat_field_gwLabel.Text = 'Flatfield';
        app.flat_field_gwLabel.Layout.Column = 1;
        app.flat_field_gwLabel.Layout.Row = 11;

        app.flat_field_gw = uieditfield(p, 'numeric');
        app.flat_field_gw.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flat_field_gw.FontColor = [1 1 1];
        app.flat_field_gw.BackgroundColor = [0.149 0.149 0.149];
        app.flat_field_gw.Tooltip = {'flat_filed parameter to apply to some of the output images (gaussian width in pixels to divide the image to correct uneven illumination of images).'};
        app.flat_field_gw.Layout.Column = 2;
        app.flat_field_gw.Layout.Row = 11;

        app.flip_y = uicheckbox(p);
        app.flip_y.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_y.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.flip_y.Text = 'Flip y';
        app.flip_y.FontColor = fontColor;
        app.flip_y.Layout.Column = 3;
        app.flip_y.Layout.Row = 12;

        app.flip_x = uicheckbox(p);
        app.flip_x.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_x.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.flip_x.Text = 'Flip x';
        app.flip_x.FontColor = fontColor;
        app.flip_x.Layout.Column = 2;
        app.flip_x.Layout.Row = 12;

        app.square = uicheckbox(p);
        app.square.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.square.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.square.Text = 'Square';
        app.square.FontColor = fontColor;
        app.square.Layout.Column = 1;
        app.square.Layout.Row = 12;

        app.RenderPreviewLamp = uilamp(p);
        app.RenderPreviewLamp.Color = [0.8 0.8 0.8];
        app.RenderPreviewLamp.Layout.Column = 1;
        app.RenderPreviewLamp.Layout.Row = 13;

        app.RenderPreviewButton = uibutton(p, 'push');
        app.RenderPreviewButton.ButtonPushedFcn = createCallbackFcn(app, @RenderPreviewButtonPushed, true);
        app.RenderPreviewButton.BackgroundColor = grayButtonColor;
        app.RenderPreviewButton.FontColor = fontColor;
        app.RenderPreviewButton.Layout.Column = 2;
        app.RenderPreviewButton.Layout.Row = 13;
        app.RenderPreviewButton.Text = 'Preview';

        app.SavePreviewButton = uibutton(p, 'push');
        app.SavePreviewButton.ButtonPushedFcn = createCallbackFcn(app, @SavePreviewButtonPushed, true);
        app.SavePreviewButton.BackgroundColor = grayButtonColor;
        app.SavePreviewButton.FontColor = fontColor;
        app.SavePreviewButton.Layout.Column = 3;
        app.SavePreviewButton.Layout.Row = 13;
        app.SavePreviewButton.Text = 'Save';

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
        app.ViewAllMenu.Text = 'View all images';

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
