classdef holodoppler < matlab.apps.AppBase

% =========================================================================
% UI component handles — required public by App Designer / registerApp
% =========================================================================
properties (Access = public)
    HoloDopplerUIFigure matlab.ui.Figure

    % ---- top-level layout ----
    RootGrid matlab.ui.container.GridLayout
    Image matlab.ui.control.Image

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
    parforArg matlab.ui.control.Spinner
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
    imageTypesListBox matlab.ui.control.ListBox
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
    ImproveContrast matlab.ui.control.CheckBox

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

        version = 'unknown';

        if isfile(fullfile(fileparts(mfilename('fullpath')), 'version.txt'))
            v = readlines('version.txt');
            version = char(v(1));
            fprintf("============================================\n" + ...
                " Welcome to HoloDoppler %s\n" + ...
                "--------------------------------------------\n" + ...
                " Developed by the DigitalHolographyFoundation\n" + ...
                "============================================\n", version);
        else
            warning('holodoppler:noVersionFile', 'version.txt not found — version will be shown as unknown.');
        end

        app.HoloDopplerUIFigure.Name = ['HoloDoppler ' version];

        % Use fullfile so the path separator is correct on all platforms
        addpath(fullfile(fileparts(mfilename('fullpath')), 'Tools'));
        displaySplashScreen();
        app.HD = HoloDopplerClass();

        app.updateButtonStates();
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
        % Dummy off-screen figure prevents uigetfile from minimising the main GUI
        f = figure('Position', [-200 -200 1 1], 'Visible', 'off');
        cleanupObj = onCleanup(@() delete(f));

        if isempty(app.HD.file)
            [fname, fpath] = uigetfile('*.raw;*.cine;*.holo');
        else
            [fname, fpath] = uigetfile(fullfile(app.HD.file.path, '*.raw;*.cine;*.holo'));
        end

        if isequal(fname, 0)
            return
        end

        try
            app.fileLoadedLamp.Color = [1 0.5 0];
            drawnow;
            app.HD.LoadFile(fullfile(fpath, fname));
            app.syncGuiFromClass();
            app.RenderPreviewButtonPushed();
            app.fileLoaded = 1;
            app.fileLoadedLamp.Color = [0 1 0];
        catch ME
            MEdisp(ME);
            app.fileLoaded = 0;
            app.fileLoadedLamp.Color = [1 0 0];
            drawnow;
        end

        app.updateButtonStates();
    end

    function LoadConfigButtonPushed(app, ~)
        [selected_file, path] = uigetfile('*.json', 'Select Config File');

        if isequal(selected_file, 0)
            return
        end

        try
            app.HD.loadParams(fullfile(path, selected_file));
            app.syncGuiFromClass();
            fprintf('Config loaded from %s\n', fullfile(path, selected_file));
        catch ME
            MEdisp(ME);
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
        app.refreshClass();
        drawnow;

        Images = [];

        try
            Images = app.HD.PreviewRendering();
            app.RenderPreviewLamp.Color = [0 1 0];
        catch ME
            MEdisp(ME);
            app.RenderPreviewLamp.Color = [1 0 0];
            drawnow;
        end

        if ~isempty(Images)
            app.Image.ImageSource = toImageSource(Images{1}, app);
            app.MenuIndex = 1;
        else
            app.Image.ImageSource = '';
        end

        % A successful render means we can now save the preview
        app.updateButtonStates();
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

        if isempty(app.HD.params.imageTypes)
            return
        end

        imgs = app.HD.view.getImages(app.HD.params.imageTypes(1));

        if ~isempty(imgs)
            app.Image.ImageSource = toImageSource(imgs{randsample(numel(imgs), 1)}, app);
        else
            app.Image.ImageSource = '';
        end

    end

    function AutofocusButtonPushed(app, ~)
        zopti = autofocus(app.HD.view, app.HD.params);
        app.HD.params.spatialPropagation = zopti;
        app.syncGuiFromClass();
        app.RenderPreviewButtonPushed();
    end

    % --- Context menu / image navigation -----------------------------------

    function changeMenu(app, direction)

        idx = app.MenuIndex;
        imagesTypes = app.HD.params.imageTypes;

        if direction == "next"
            num = mod(idx, length(imagesTypes)) + 1;
            app.SelectMenu(num);
        elseif direction == "previous"
            num = mod(idx - 2, length(imagesTypes)) + 1;
            app.SelectMenu(num);
        end

    end

    function SelectMenu(app, num, ~)
        imgs = app.HD.view.getImages(app.HD.params.imageTypes);

        if isempty(imgs) || isempty(imgs{num})
            app.Image.ImageSource = '';
            return
        end

        image = imgs{num};
        % Resize non-square images (except 'broadening') to square for display
        if ~ismember(app.HD.params.imageTypes{num}, {'broadening'}) && ...
                size(image, 1) ~= size(image, 2)
            maxSize = max(size(image));
            image = imresize(image, [maxSize, maxSize]);
        end

        app.Image.ImageSource = toImageSource(image, app);
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

            if isfinite(val) % catches both NaN and Inf
                app.svdThreshold.Value = val;
            end

        else
            app.svdThreshold.Value = 0;
        end

        app.refreshClass();
    end

    function frequencyRange2ValueChanged(app, ~)

        if strcmp(app.timeTransform.Value, 'FFT') && app.frequencyRange2.Value > app.fs.Value / 2
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

    function registrationCheckBoxValueChanged(app, ~)
        % Toggling registration enables/disables the disk ratio field
        app.registrationDiskRatio.Enable = app.imageRegistration.Value;
        app.registrationDiskLabel.Enable = app.imageRegistration.Value;
        app.refreshClass();
    end

    function spatialFilterCheckBoxValueChanged(app, ~)
        % Toggling spatial filter enables/disables its range fields
        app.spatialFilterRange1.Enable = app.spatialFilter.Value;
        app.spatialFilterRange2.Enable = app.spatialFilter.Value;
        app.refreshClass();
    end

    function svdFilterCheckBoxValueChanged(app, ~)
        % Toggling SVD filter enables/disables its threshold and stride fields
        app.svdThreshold.Enable = app.svd_filter.Value;
        app.svdThresholdResetButton.Enable = app.svd_filter.Value;
        app.svdStride.Enable = app.svd_filter.Value;
        app.svdStrideLabel.Enable = app.svd_filter.Value;
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

    % --- Enable / disable controls based on application state -------------
    %
    % Three tiers of availability:
    %   (A) always available  — LoadfileButton, LoadConfigButton,
    %                           FolderManagementButton, AdvancedButton
    %   (B) file loaded       — everything that reads from obj.reader
    %   (C) preview rendered  — SavePreviewButton, image navigation

    function updateButtonStates(app)
        fileReady = ~isempty(app.HD) && ~isempty(app.HD.file);
        previewReady = fileReady && ~isempty(app.HD.view) && ...
            ~isempty(app.HD.view.Output);

        % ---- (B) require a loaded file ------------------------------------
        fileControls = { ...
                            app.SaveConfigButton, ...
                            app.VideoRenderingButton, ...
                            app.ShowHistogramButton, ...
                            app.RefreshAppButton, ...
                            app.RenderPreviewButton, ...
                            app.AutofocusButton, ...
                            app.AutofocusFromRef, ...
                            app.imageRegistration, ...
                            app.registrationDiskRatio, ...
                            app.positioninfileSlider, ...
                            app.framePosition, ...
                            app.batchSize, ...
                            app.batchStride, ...
                            app.refBatchSize, ...
                            app.fs, ...
                            app.lambda, ...
                            app.ppx, ...
                            app.ppy, ...
                            app.spatialFilter, ...
                            app.spatialFilterRange1, ...
                            app.spatialFilterRange2, ...
                            app.PaddingNum, ...
                            app.spatialTransformation, ...
                            app.spatialPropagation, ...
                            app.svd_filter, ...
                            app.svdThreshold, ...
                            app.svdThresholdResetButton, ...
                            app.svdStride, ...
                            app.timeTransform, ...
                            app.frequencyRange1, ...
                            app.frequencyRange2, ...
                            app.frequencyRangeInter1, ...
                            app.frequencyRangeInter2, ...
                            app.indexRange1, ...
                            app.indexRange2, ...
                            app.flat_field_gw, ...
                            app.square, ...
                            app.flip_x, ...
                            app.flip_y, ...
                            app.parforArg, ...
                        };

        for k = 1:numel(fileControls)
            fileControls{k}.Enable = fileReady;
        end

        % ---- (C) require a rendered preview --------------------------------
        app.SavePreviewButton.Enable = previewReady;
        app.NextMenu.Enable = previewReady;
        app.ViewAllMenu.Enable = previewReady;

        % ---- frequency / index range: also respect the transform type ------
        % (only meaningful once a file is loaded; skip otherwise)
        if fileReady
            app.updateTimeTransformControls();
        end

        % ---- registration disk ratio: only when registration is on ---------
        if fileReady
            app.registrationDiskRatio.Enable = app.imageRegistration.Value;
            app.registrationDiskLabel.Enable = app.imageRegistration.Value;
        end

        % ---- SVD sub-controls: only when SVD filter is checked -------------
        if fileReady
            app.svdThreshold.Enable = app.svd_filter.Value;
            app.svdThresholdResetButton.Enable = app.svd_filter.Value;
            app.svdStride.Enable = app.svd_filter.Value;
            app.svdStrideLabel.Enable = app.svd_filter.Value;
        end

        % ---- Spatial filter ranges: only when spatial filter is checked ----
        if fileReady
            app.spatialFilterRange1.Enable = app.spatialFilter.Value;
            app.spatialFilterRange2.Enable = app.spatialFilter.Value;
        end

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
        app.createrenderingParametersPanel();
        app.createImageViewsAndMenus();

        app.HoloDopplerUIFigure.Visible = 'on';
    end

    % -----------------------------------------------------------------------
    function createFigureAndRootGrid(app, pathToMLAPP)
        app.HoloDopplerUIFigure = uifigure('Visible', 'off');
        app.HoloDopplerUIFigure.Position = [210 56 900 900];
        app.HoloDopplerUIFigure.Name = 'HoloDoppler';
        app.HoloDopplerUIFigure.Icon = fullfile(pathToMLAPP, 'holoDopplerLogo.png');
        app.HoloDopplerUIFigure.CloseRequestFcn = createCallbackFcn(app, @HoloDopplerUIFigureCloseRequest, true);
        app.HoloDopplerUIFigure.WindowKeyPressFcn = createCallbackFcn(app, @HoloDopplerUIFigureWindowKeyPress, true);

        app.RootGrid = uigridlayout(app.HoloDopplerUIFigure, [2 2]);
        app.RootGrid.ColumnWidth = {'1x', '1x'};
        app.RootGrid.RowHeight = {'1x', '1x'};
        app.RootGrid.RowSpacing = 5;
        app.RootGrid.ColumnSpacing = 5;
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

        app.parforArg = uispinner(app.mainParametersGrid);
        app.parforArg.ValueChangingFcn = createCallbackFcn(app, @refreshClass, true);
        maxWorkers = parcluster('local').NumWorkers;
        app.parforArg.Limits = [-1 maxWorkers];
        app.parforArg.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.parforArg.FontColor = fontColor;
        app.parforArg.BackgroundColor = darkBackgroundColor;
        app.parforArg.Tooltip = {'Number of worker used for the video rendering (depends of the working station)'};
        app.parforArg.Value = 10;
        app.parforArg.Layout.Row = 6;
        app.parforArg.Layout.Column = 2;

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
        app.RefreshAppButton.Text = '👌 Refresh app';
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
        app.imageTypesListBox = uilistbox(p);
        app.imageTypesListBox.Items = {};
        app.imageTypesListBox.Multiselect = 'on';
        app.imageTypesListBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.imageTypesListBox.Tooltip = {'Image types output giving extracting different informations from a batch of frames'};
        app.imageTypesListBox.FontColor = [1 1 1];
        app.imageTypesListBox.BackgroundColor = darkBackgroundColor;
        app.imageTypesListBox.Layout.Row = 1;
        app.imageTypesListBox.Layout.Column = [1 2];
        app.imageTypesListBox.Value = {};

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

        app.imageRegistration = uicheckbox(p);
        app.imageRegistration.ValueChangedFcn = createCallbackFcn(app, @registrationCheckBoxValueChanged, true);
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
    function createrenderingParametersPanel(app)

        backgroundColor = [0.2 0.2 0.2];
        darkBackgroundColor = [0.15 0.15 0.15];
        fontColor = [0.9 0.9 0.9];
        grayButtonColor = [0.5 0.5 0.5];

        app.renderingParametersPanel = uipanel(app.RootGrid);
        app.renderingParametersPanel.ForegroundColor = [0.8 0.8 0.8];
        app.renderingParametersPanel.Title = 'Rendering parameters';
        app.renderingParametersPanel.BackgroundColor = [0.2 0.2 0.2];
        app.renderingParametersPanel.Layout.Row = 2;
        app.renderingParametersPanel.Layout.Column = 2;

        app.renderingParametersGrid = uigridlayout(app.renderingParametersPanel, [14 3]);
        app.renderingParametersGrid.RowHeight = repmat({'fit'}, 1, 14);
        app.renderingParametersGrid.ColumnWidth = {'fit', '1x', '1x'};
        app.renderingParametersGrid.Padding = [10 10 10 10];
        app.renderingParametersGrid.RowSpacing = 5;
        app.renderingParametersGrid.ColumnSpacing = 5;
        app.renderingParametersGrid.BackgroundColor = backgroundColor;

        p = app.renderingParametersGrid;

        % Spatial filtering parameters row 1

        app.spatialFilter = uicheckbox(p);
        app.spatialFilter.ValueChangedFcn = createCallbackFcn(app, @spatialFilterCheckBoxValueChanged, true);
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
        app.AutofocusButton.ButtonPushedFcn = createCallbackFcn(app, @AutofocusButtonPushed, true);
        app.AutofocusButton.BackgroundColor = grayButtonColor;
        app.AutofocusButton.FontColor = fontColor;
        app.AutofocusButton.Layout.Column = 3;
        app.AutofocusButton.Layout.Row = 4;
        app.AutofocusButton.Text = 'Autofocus';

        % SVD filtering row 5 6

        app.svd_filter = uicheckbox(p);
        app.svd_filter.ValueChangedFcn = createCallbackFcn(app, @svdFilterCheckBoxValueChanged, true);
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
        app.svdThreshold.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => frequencyRange1/fs * batchSize * 2)'};
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
        app.flat_field_gw.FontColor = fontColor;
        app.flat_field_gw.BackgroundColor = darkBackgroundColor;
        app.flat_field_gw.Tooltip = {'flat_filed parameter to apply to some of the output images (gaussian width in pixels to divide the image to correct uneven illumination of images).'};
        app.flat_field_gw.Layout.Column = 2;
        app.flat_field_gw.Layout.Row = 11;

        app.flip_y = uicheckbox(p);
        app.flip_y.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_y.Tooltip = {'Flip the output image vertically'};
        app.flip_y.Text = 'Flip y';
        app.flip_y.FontColor = fontColor;
        app.flip_y.Layout.Column = 3;
        app.flip_y.Layout.Row = 12;

        app.flip_x = uicheckbox(p);
        app.flip_x.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_x.Tooltip = {'Flip the output image horizontally'};
        app.flip_x.Text = 'Flip x';
        app.flip_x.FontColor = fontColor;
        app.flip_x.Layout.Column = 2;
        app.flip_x.Layout.Row = 12;

        app.square = uicheckbox(p);
        app.square.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.square.Tooltip = {'Crop the output image to a square aspect ratio'};
        app.square.Text = 'Square';
        app.square.FontColor = fontColor;
        app.square.Layout.Column = 1;
        app.square.Layout.Row = 12;

        app.ImproveContrast = uicheckbox(p);
        app.ImproveContrast.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ImproveContrast.Tooltip = {'Improve the contrast by rescaling the previewed frame'};
        app.ImproveContrast.Text = 'Improve frame contrast';
        app.ImproveContrast.FontColor = fontColor;
        app.ImproveContrast.Layout.Column = 1;
        app.ImproveContrast.Layout.Row = 13;

        app.RenderPreviewLamp = uilamp(p);
        app.RenderPreviewLamp.Color = [0.8 0.8 0.8];
        app.RenderPreviewLamp.Layout.Column = 1;
        app.RenderPreviewLamp.Layout.Row = 14;

        app.RenderPreviewButton = uibutton(p, 'push');
        app.RenderPreviewButton.ButtonPushedFcn = createCallbackFcn(app, @RenderPreviewButtonPushed, true);
        app.RenderPreviewButton.BackgroundColor = grayButtonColor;
        app.RenderPreviewButton.FontColor = fontColor;
        app.RenderPreviewButton.Layout.Column = 2;
        app.RenderPreviewButton.Layout.Row = 14;
        app.RenderPreviewButton.Text = 'Preview';

        app.SavePreviewButton = uibutton(p, 'push');
        app.SavePreviewButton.ButtonPushedFcn = createCallbackFcn(app, @SavePreviewButtonPushed, true);
        app.SavePreviewButton.BackgroundColor = grayButtonColor;
        app.SavePreviewButton.FontColor = fontColor;
        app.SavePreviewButton.Layout.Column = 3;
        app.SavePreviewButton.Layout.Row = 14;
        app.SavePreviewButton.Text = 'Save';

    end

    % -----------------------------------------------------------------------
    function createImageViewsAndMenus(app)
        app.Image = uiimage(app.RootGrid);
        app.Image.Layout.Row = 1;
        app.Image.Layout.Column = 2;

        app.RightClickImageContextMenu = uicontextmenu(app.HoloDopplerUIFigure);

        app.NextMenu = uimenu(app.RightClickImageContextMenu);
        app.NextMenu.MenuSelectedFcn = createCallbackFcn(app, @NextMenuSelected, true);
        app.NextMenu.Text = 'Next';

        app.ViewAllMenu = uimenu(app.RightClickImageContextMenu);
        app.ViewAllMenu.MenuSelectedFcn = createCallbackFcn(app, @ViewAllMenuSelected, true);
        app.ViewAllMenu.Text = 'View all images';

        app.Image.ContextMenu = app.RightClickImageContextMenu;
    end

end % createComponents methods block

% =========================================================================
% App construction and deletion
% =========================================================================
methods (Access = public)

    function app = holodoppler
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
