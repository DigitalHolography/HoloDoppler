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
    framePositionField matlab.ui.control.NumericEditField

    % ---- batch / video rendering sub-panel ----
    BatchselectionparametersandVideoRenderingPanel matlab.ui.container.Panel
    SaveconfigButton matlab.ui.control.Button
    PlayButton matlab.ui.control.Button
    ShowHistogramButton matlab.ui.control.Button
    VideoRenderingLamp matlab.ui.control.Lamp
    SaveVideoButton matlab.ui.control.Button
    batch_size matlab.ui.control.NumericEditField
    batchsizeLabel matlab.ui.control.Label
    Image_typesListBox matlab.ui.control.ListBox
    registrationDiscLabel matlab.ui.control.Label
    registration_disc_ratio matlab.ui.control.NumericEditField
    batch_size_registration matlab.ui.control.NumericEditField
    refbatchsizeEditFieldLabel matlab.ui.control.Label
    batch_stride matlab.ui.control.NumericEditField
    batchstrideEditFieldLabel matlab.ui.control.Label
    LoadconfigButton matlab.ui.control.Button
    VideoRenderingButton matlab.ui.control.Button
    FoldermanagementButton matlab.ui.control.Button
    temporalfilterEditField matlab.ui.control.NumericEditField
    AutofocusFromRef matlab.ui.control.CheckBox
    applyshackhartmannfromref matlab.ui.control.CheckBox
    temporalfilterCheckBox matlab.ui.control.CheckBox
    phaseregistrationCheckBox matlab.ui.control.CheckBox
    rephasingCheckBox matlab.ui.control.CheckBox
    image_registration matlab.ui.control.CheckBox
    showrefCheckBox matlab.ui.control.CheckBox
    iterativeregistrationCheckBox matlab.ui.control.CheckBox

    % ---- rendering parameters panel ----
    RenderingparametersPanel matlab.ui.container.Panel
    Padding_num matlab.ui.control.NumericEditField
    PaddNLabel matlab.ui.control.Label
    AutofocusButton matlab.ui.control.Button
    square matlab.ui.control.CheckBox
    flip_x matlab.ui.control.CheckBox
    flip_y matlab.ui.control.CheckBox
    NsubxtLabel matlab.ui.control.Label
    NsubxLabel matlab.ui.control.Label
    svdx_t_Nsub matlab.ui.control.NumericEditField
    svdx_Nsub matlab.ui.control.NumericEditField
    svdx_t_threshold matlab.ui.control.NumericEditField
    svdx_threshold matlab.ui.control.NumericEditField
    index_range2 matlab.ui.control.NumericEditField
    index_range1 matlab.ui.control.NumericEditField
    index_rangeLabel matlab.ui.control.Label
    svdx_t_filter matlab.ui.control.CheckBox
    RenderPreviewLamp matlab.ui.control.Lamp
    SavePreviewButton matlab.ui.control.Button
    RenderPreviewButton matlab.ui.control.Button
    flat_field_gw matlab.ui.control.NumericEditField
    flat_field_gwEditFieldLabel matlab.ui.control.Label
    time_range2 matlab.ui.control.NumericEditField
    time_range1 matlab.ui.control.NumericEditField
    frequency_rangeLabel matlab.ui.control.Label
    time_transform matlab.ui.control.DropDown
    time_transformDropDownLabel matlab.ui.control.Label
    svd_threshold matlab.ui.control.NumericEditField
    svdx_filter matlab.ui.control.CheckBox
    svd_filter matlab.ui.control.CheckBox
    spatial_propagation matlab.ui.control.NumericEditField
    spatial_propagationEditFieldLabel matlab.ui.control.Label
    spatial_transformation matlab.ui.control.DropDown
    spatial_transformationDropDownLabel matlab.ui.control.Label
    spatial_filter_range2 matlab.ui.control.NumericEditField
    spatial_filter_range1 matlab.ui.control.NumericEditField
    spatial_filter_range matlab.ui.control.Label
    hilbert_filter matlab.ui.control.CheckBox
    spatial_filter matlab.ui.control.CheckBox
    svd_threshold_reset_button matlab.ui.control.Button

    % ---- aberration compensation panel ----
    AberrationcompensationPanel matlab.ui.container.Panel
    onlydefocusCheckBox matlab.ui.control.CheckBox
    ConvergenceThreshold matlab.ui.control.NumericEditField
    calibrationfactorLabel_2 matlab.ui.control.Label
    CalibrationFactorEditField matlab.ui.control.NumericEditField
    calibrationfactorLabel matlab.ui.control.Label
    NumberOfIterationEditField matlab.ui.control.NumericEditField
    numberofiterationLabel matlab.ui.control.Label
    imagesubapsizeratioEditField matlab.ui.control.NumericEditField
    imagesubapsizeratioEditFieldLabel matlab.ui.control.Label
    subapnumpositionsEditField matlab.ui.control.NumericEditField
    subapnumpositionsEditFieldLabel matlab.ui.control.Label
    referenceimageDropDown matlab.ui.control.DropDown
    referenceimageDropDownLabel matlab.ui.control.Label
    ZernikeProjectionCheckBox matlab.ui.control.CheckBox
    savecoefsCheckBox matlab.ui.control.CheckBox
    rangeYEditField matlab.ui.control.NumericEditField
    rangeYEditFieldLabel matlab.ui.control.Label
    rangeZEditField matlab.ui.control.NumericEditField
    rangeZEditFieldLabel matlab.ui.control.Label
    volumesizeEditField matlab.ui.control.NumericEditField
    volumesizeEditFieldLabel matlab.ui.control.Label
    maxSubAp_PCAEditField matlab.ui.control.NumericEditField
    maxEditField_2Label matlab.ui.control.Label
    minSubAp_PCAEditField matlab.ui.control.NumericEditField
    minEditField_2Label matlab.ui.control.Label
    SubAp_PCACheckBox matlab.ui.control.CheckBox
    aberrationPreviewLabel matlab.ui.control.Label
    IterativeCheckBox matlab.ui.control.CheckBox
    subaperturemarginEditField matlab.ui.control.NumericEditField
    subaperturemarginEditFieldLabel matlab.ui.control.Label
    shackhartmannzernikeranksEditField matlab.ui.control.NumericEditField
    zernikeranksEditFieldLabel matlab.ui.control.Label
    ShackHartmannCheckBox matlab.ui.control.CheckBox
    aberrationStatusLabel matlab.ui.control.Label
    UIAxes_aberrationPreview matlab.ui.control.UIAxes

    % ---- advanced processing panel ----
    AdvancedProcessingPanel matlab.ui.container.Panel
    SVDTresholdEditFieldLabel_2 matlab.ui.control.Label
    SVDStrideEditField matlab.ui.control.NumericEditField
    SVDThresholdCheckBox matlab.ui.control.CheckBox
    SVDTresholdEditFieldLabel matlab.ui.control.Label
    SVDThresholdEditField matlab.ui.control.NumericEditField
    SVDxCheckBox matlab.ui.control.CheckBox
    SVDx_SubApEditField matlab.ui.control.NumericEditField
    SVDx_SubApEditFieldLabel matlab.ui.control.Label
    xystrideEditField matlab.ui.control.NumericEditField
    xystrideEditFieldLabel matlab.ui.control.Label
    r1EditField matlab.ui.control.NumericEditField
    r1EditFieldLabel matlab.ui.control.Label
    unitcellsinlatticeEditField matlab.ui.control.NumericEditField
    unitcellsinlatticeEditFieldLabel matlab.ui.control.Label
    nu2EditField matlab.ui.control.NumericEditField
    nu2EditFieldLabel matlab.ui.control.Label
    nu1EditField matlab.ui.control.NumericEditField
    nu1EditFieldLabel matlab.ui.control.Label
    phi2EditField matlab.ui.control.NumericEditField
    phi2EditFieldLabel matlab.ui.control.Label
    phi1EditField matlab.ui.control.NumericEditField
    phi1EditFieldLabel matlab.ui.control.Label
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
            fprintf("==========================================\n " + ...
                "Welcome to HoloDoppler %s\n" + ...
                "------------------------------------------\n" + ...
                "Developed by the DigitalHolographyFoundation\n" + ...
                "==========================================\n", v(1));
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

    function PlayButtonPushed(app, ~)

        try
            app.HD.showVideo();
        catch e
            fprintf("Couldn't play video (try to video render first) : %s", e.message);
        end

    end

    % --- UI state sync / refresh -------------------------------------------

    % Sync every widget value into the HD class, then update enable states.
    % Connected to ~50 component ValueChanged callbacks.
    function refreshClass(app, ~)
        app.syncClassFromGui();
        app.updateTimeTransformControls();
        app.updateSvdxFilterControls();
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

                if ~ismember(app.HD.params.image_types{num}, {'spectrogram', 'autocorrelogram', 'broadening', 'f_RMS'}) && size(image, 1) ~= size(image, 2)
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

    function svd_threshold_reset_buttonPushed(app, ~)

        if app.svd_threshold.Value == 0
            val = ceil(app.time_range1.Value * 2 * app.batch_size.Value / app.fs.Value);

            if ~isnan(val)
                app.svd_threshold.Value = val;
            end

        else
            app.svd_threshold.Value = 0;
        end

    end

    function time_range2ValueChanged(app, ~)

        if strcmp(app.time_transform, 'FFT') && app.time_range2.Value > app.fs.Value / 2
            app.time_range2.Value = app.fs.Value / 2;
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
        d = dialog('Position', [300, 300, 750, 130 + length(app.HD.drawer_list) * 14], ...
            'Color', [0.2, 0.2, 0.2], ...
            'Name', 'Folder management', ...
            'Resize', 'on', ...
            'WindowStyle', 'normal');

        txt = uicontrol('Parent', d, ...
            'Style', 'text', ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.2, 0.2, 0.2], ...
            'ForegroundColor', [0.8, 0.8, 0.8], ...
            'Position', [20, 90, 710, length(app.HD.drawer_list) * 14], ...
            'HorizontalAlignment', 'left', ...
            'String', app.HD.drawer_list);

        keep_z_distance = uicontrol('Parent', d, ...
            'Style', 'checkbox', ...
            'Position', [500, 50, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'FontWeight', 'bold', ...
            'String', 'Keep z distance', ...
            'Value', 0);

        app.makeDrawerButton(d, [20, 20], 'Select file', @(~, ~) app.drawerSelectFile(d, txt));
        app.makeDrawerButton(d, [20, 50], 'Select Current', @(~, ~) app.drawerSelectCurrent(d, txt));
        app.makeDrawerButton(d, [140, 50], 'Select Current Folder', @(~, ~) app.drawerSelectCurrentFolder(d, txt));
        app.makeDrawerButton(d, [140, 20], 'Select folder', @(~, ~) app.drawerSelectFolder(d, txt));
        app.makeDrawerButton(d, [260, 20], 'Clear list', @(~, ~) app.drawerClearList(d, txt));
        app.makeDrawerButton(d, [380, 20], 'Save configs', @(~, ~) app.drawerSaveConfigs(keep_z_distance));
        app.makeDrawerButton(d, [380, 50], 'Delete all configs', @(~, ~) app.drawerDeleteConfigs());
        app.makeDrawerButton(d, [500, 20], 'Render', @(~, ~) app.drawerRender());
        app.makeDrawerButton(d, [620, 20], 'Save to txt', @(~, ~) app.drawerSaveTxt());
        app.makeDrawerButton(d, [620, 50], 'Load from txt', @(~, ~) app.drawerLoadTxt(d, txt));
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
        app.time_range1.Enable = useFreqRange;
        app.time_range2.Enable = useFreqRange;
        app.frequency_rangeLabel.Enable = useFreqRange;
        app.index_range1.Enable = ~useFreqRange;
        app.index_range2.Enable = ~useFreqRange;
        app.index_rangeLabel.Enable = ~useFreqRange;
    end

    function updateSvdxFilterControls(app)
        en = app.svdx_filter.Value;
        app.svdx_threshold.Enable = en;
        app.NsubxLabel.Enable = en;
        app.svdx_Nsub.Enable = en;

        ent = app.svdx_t_filter.Value;
        app.svdx_t_threshold.Enable = ent;
        app.NsubxtLabel.Enable = ent;
        app.svdx_t_Nsub.Enable = ent;
    end

    % --- Drawer (folder management) helpers --------------------------------

    function makeDrawerButton(~, parent, pos, label, cb)
        uicontrol('Parent', parent, ...
            'Position', [pos, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', label, ...
            'Callback', cb);
    end

    function updateDrawerDisplay(app, d, txt)
        txt.String = app.HD.drawer_list;
        d.Position(4) = 100 + length(app.HD.drawer_list) * 14;
        txt.Position(4) = length(app.HD.drawer_list) * 14;
    end

    function drawerSelectFile(app, d, txt)

        if ~isempty(app.HD.drawer_list)
            [selected_file, path] = uigetfile(app.HD.drawer_list{end}, 'Select File');
        else
            [selected_file, path] = uigetfile('Select File');
        end

        if selected_file
            [~, ~, ext] = fileparts(selected_file);

            if ismember(ext, {'.cine', '.holo'})
                app.HD.drawer_list{end + 1} = fullfile(path, selected_file);
            else
                fprintf("File should be of extension .cine or .holo\n");
            end

        end

        app.updateDrawerDisplay(d, txt);
    end

    function drawerSelectCurrent(app, d, txt)

        if isempty(app.HD.file)
            return
        end

        selected_file = app.HD.file.path;
        [~, ~, ext] = fileparts(selected_file);

        if ismember(ext, {'.cine', '.holo'})
            app.HD.drawer_list{end + 1} = selected_file;
        else
            fprintf("File should be of extension .cine or .holo\n");
        end

        app.updateDrawerDisplay(d, txt);
    end

    function drawerAddFilesFromFolder(app, folder, d, txt)
        entries = dir(folder);

        for i = 1:numel(entries)

            if ~entries(i).isdir
                [~, ~, ext] = fileparts(entries(i).name);

                if ismember(ext, {'.cine', '.holo'})
                    app.HD.drawer_list{end + 1} = fullfile(folder, entries(i).name);
                end

            end

        end

        app.updateDrawerDisplay(d, txt);
    end

    function drawerSelectCurrentFolder(app, d, txt)

        if isempty(app.HD.file)
            return
        end

        app.drawerAddFilesFromFolder(app.HD.file.dir, d, txt);
    end

    function drawerSelectFolder(app, d, txt)

        if ~isempty(app.HD.drawer_list)
            [last_folder, ~, ~] = fileparts(app.HD.drawer_list{end});
        else
            last_folder = [];
        end

        selected_folder = uigetdir(last_folder);

        if selected_folder
            app.drawerAddFilesFromFolder(selected_folder, d, txt);
        end

    end

    function drawerClearList(app, d, txt)
        app.HD.drawer_list = {};
        app.updateDrawerDisplay(d, txt);
    end

    function drawerLoadTxt(app, d, txt)
        [selected_file, path] = uigetfile('*.txt', 'Select File');
        lines = readlines(fullfile(path, selected_file));

        for i = 1:numel(lines)

            if ~isempty(lines(i))

                try
                    [~, ~, ext] = fileparts(lines(i));

                    if ismember(ext, {'.cine', '.holo'})
                        app.HD.drawer_list{end + 1} = lines(i);
                    end

                catch e
                    disp(e)
                end

            end

        end

        app.updateDrawerDisplay(d, txt);
    end

    function drawerSaveTxt(app)
        [selected_file, path] = uigetfile('*.txt', 'Select File');
        writelines(app.HD.drawer_list, fullfile(path, selected_file));
    end

    function drawerSaveConfigs(app, keepZControl)

        for i = 1:length(app.HD.drawer_list)
            app.HD.saveParams(app.HD.drawer_list{i}, keepZControl.Value);
        end

    end

    function drawerRender(app)
        fileList = app.buildDrawerFileList();

        for i = 1:length(fileList)
            entry = fileList{i};

            if ~isempty(entry)
                configs = entry{2};

                for j = 1:length(configs)
                    app.HD.LoadFile(entry{1}, params = configs{j});
                    app.HD.VideoRendering();
                end

            end

        end

    end

    function drawerDeleteConfigs(app)
        fileList = app.buildDrawerFileList();

        for i = 1:length(fileList)
            entry = fileList{i};

            if ~isempty(entry) && ~isempty(entry{2})

                for j = 1:length(entry{2})
                    delete(entry{2}{j});
                end

            end

        end

    end

    function fileList = buildDrawerFileList(app)
        fileList = cell(size(app.HD.drawer_list));

        for i = 1:length(app.HD.drawer_list)
            config_list = get_config_files(app.HD.drawer_list{i});

            if ~isempty(config_list)
                fileList{i} = {app.HD.drawer_list{i}, config_list};
            end

        end

    end

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
        app.FileselectionPanel = uipanel(app.RootGrid);
        app.FileselectionPanel.Tooltip = {''};
        app.FileselectionPanel.ForegroundColor = [0.8 0.8 0.8];
        app.FileselectionPanel.TitlePosition = 'centertop';
        app.FileselectionPanel.Title = 'File selection';
        app.FileselectionPanel.BackgroundColor = [0.2 0.2 0.2];
        app.FileselectionPanel.Layout.Row = [1 2];
        app.FileselectionPanel.Layout.Column = 1;

        app.LoadfileButton = uibutton(app.FileselectionPanel, 'push');
        app.LoadfileButton.ButtonPushedFcn = createCallbackFcn(app, @LoadfileButtonPushed, true);
        app.LoadfileButton.BackgroundColor = [0.502 0.502 0.502];
        app.LoadfileButton.FontColor = [0.902 0.902 0.902];
        app.LoadfileButton.Position = [30 837 100 22];
        app.LoadfileButton.Text = 'Load file';

        app.fileLoadedLamp = uilamp(app.FileselectionPanel);
        app.fileLoadedLamp.Position = [138 843 10 10];

        app.lambdaLabel = uilabel(app.FileselectionPanel);
        app.lambdaLabel.HorizontalAlignment = 'center';
        app.lambdaLabel.FontColor = [0.8 0.8 0.8];
        app.lambdaLabel.Tooltip = {'Laser''s wavelength for light propagation calculations in (m)'};
        app.lambdaLabel.Position = [40 771 84 22];
        app.lambdaLabel.Text = 'wavelength';

        app.lambda = uieditfield(app.FileselectionPanel, 'numeric');
        app.lambda.Limits = [0 Inf];
        app.lambda.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.lambda.FontColor = [0.8 0.8 0.8];
        app.lambda.BackgroundColor = [0.149 0.149 0.149];
        app.lambda.Tooltip = {'Laser wavelength in nanometers'};
        app.lambda.Position = [123 772 100 22];

        app.fsLabel = uilabel(app.FileselectionPanel);
        app.fsLabel.HorizontalAlignment = 'right';
        app.fsLabel.FontColor = [0.8 0.8 0.8];
        app.fsLabel.Tooltip = {'Sampling frequency in (kHz)'};
        app.fsLabel.Position = [6 799 109 22];
        app.fsLabel.Text = 'sampling frequency';

        app.fs = uieditfield(app.FileselectionPanel, 'numeric');
        app.fs.Limits = [0 Inf];
        app.fs.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.fs.FontColor = [0.8 0.8 0.8];
        app.fs.BackgroundColor = [0.149 0.149 0.149];
        app.fs.Tooltip = {'Sampling frequency (kHz)'};
        app.fs.Position = [123 799 100 22];

        app.pixelPitchLabel = uilabel(app.FileselectionPanel);
        app.pixelPitchLabel.HorizontalAlignment = 'center';
        app.pixelPitchLabel.FontColor = [0.8 0.8 0.8];
        app.pixelPitchLabel.Tooltip = {'Camera pixel pitch (distance between spatial sampling points) in (m)'};
        app.pixelPitchLabel.Position = [45 743 84 22];
        app.pixelPitchLabel.Text = 'pp x y';

        app.ppx = uieditfield(app.FileselectionPanel, 'numeric');
        app.ppx.Limits = [0 10];
        app.ppx.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ppx.FontColor = [0.8 0.8 0.8];
        app.ppx.BackgroundColor = [0.149 0.149 0.149];
        app.ppx.Position = [122 744 73 22];

        app.ppy = uieditfield(app.FileselectionPanel, 'numeric');
        app.ppy.Limits = [0 10];
        app.ppy.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ppy.FontColor = [0.8 0.8 0.8];
        app.ppy.BackgroundColor = [0.149 0.149 0.149];
        app.ppy.Position = [211 744 62 22];

        app.imageSizeLabel = uilabel(app.FileselectionPanel);
        app.imageSizeLabel.HorizontalAlignment = 'center';
        app.imageSizeLabel.FontColor = [0.8 0.8 0.8];
        app.imageSizeLabel.Tooltip = {'Camera pixel pitch (distance between spatial sampling points) in (m)'};
        app.imageSizeLabel.Position = [36 712 84 22];
        app.imageSizeLabel.Text = 'Nx Ny';

        app.Nx = uieditfield(app.FileselectionPanel, 'numeric');
        app.Nx.Limits = [0 Inf];
        app.Nx.Editable = 'off';
        app.Nx.FontColor = [0.8 0.8 0.8];
        app.Nx.BackgroundColor = [0.149 0.149 0.149];
        app.Nx.Tooltip = {'Width of the recorded interferograms'};
        app.Nx.Position = [123 712 73 22];

        app.Ny = uieditfield(app.FileselectionPanel, 'numeric');
        app.Ny.Limits = [0 Inf];
        app.Ny.Editable = 'off';
        app.Ny.FontColor = [0.8 0.8 0.8];
        app.Ny.BackgroundColor = [0.149 0.149 0.149];
        app.Ny.Tooltip = {'Height of the recorded interferograms'};
        app.Ny.Position = [211 712 62 22];

        app.numworkersSpinnerLabel = uilabel(app.FileselectionPanel);
        app.numworkersSpinnerLabel.HorizontalAlignment = 'right';
        app.numworkersSpinnerLabel.FontColor = [0.902 0.902 0.902];
        app.numworkersSpinnerLabel.Position = [26 681 74 22];
        app.numworkersSpinnerLabel.Text = 'num workers';

        app.parfor_arg = uispinner(app.FileselectionPanel);
        app.parfor_arg.ValueChangingFcn = createCallbackFcn(app, @refreshClass, true);
        app.parfor_arg.Limits = [-1 32];
        app.parfor_arg.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.parfor_arg.FontColor = [0.8 0.8 0.8];
        app.parfor_arg.BackgroundColor = [0.149 0.149 0.149];
        app.parfor_arg.Tooltip = {'Number of worker used for the video rendering (depends of the working station)'};
        app.parfor_arg.Position = [109 681 103 22];
        app.parfor_arg.Value = 10;

        app.NotesTextAreaLabel = uilabel(app.FileselectionPanel);
        app.NotesTextAreaLabel.BackgroundColor = [0.2 0.2 0.2];
        app.NotesTextAreaLabel.HorizontalAlignment = 'right';
        app.NotesTextAreaLabel.FontColor = [0.8 0.8 0.8];
        app.NotesTextAreaLabel.Position = [10 204 37 22];
        app.NotesTextAreaLabel.Text = 'Notes';

        app.NotesTextArea = uitextarea(app.FileselectionPanel);
        app.NotesTextArea.FontColor = [0.8 0.8 0.8];
        app.NotesTextArea.BackgroundColor = [0.149 0.149 0.149];
        app.NotesTextArea.Position = [10 87 244 119];

        app.positioninfileSliderLabel = uilabel(app.FileselectionPanel);
        app.positioninfileSliderLabel.HorizontalAlignment = 'right';
        app.positioninfileSliderLabel.FontColor = [0.902 0.902 0.902];
        app.positioninfileSliderLabel.Position = [49 18 78 19];
        app.positioninfileSliderLabel.Text = {'position in file'; ''};

        app.positioninfileSlider = uislider(app.FileselectionPanel);
        app.positioninfileSlider.Limits = [0 1];
        app.positioninfileSlider.MajorTicks = [];
        app.positioninfileSlider.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.positioninfileSlider.MinorTicks = [0 0.05 0.1 0.15 0.2 0.25 0.3 0.35 0.4 0.45 0.5 0.55 0.6 0.65 0.7 0.75 0.8 0.85 0.9 0.95 1];
        app.positioninfileSlider.Tooltip = {'Change value to display a different video timestamp in the gui.'};
        app.positioninfileSlider.Position = [57 53 158 3];

        app.framePositionField = uieditfield(app.FileselectionPanel, 'numeric');
        app.framePositionField.Limits = [0 Inf];
        app.framePositionField.RoundFractionalValues = 'on';
        app.framePositionField.ValueDisplayFormat = '%.0f';
        app.framePositionField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.framePositionField.FontColor = [0.8 0.8 0.8];
        app.framePositionField.BackgroundColor = [0.149 0.149 0.149];
        app.framePositionField.Tooltip = {''};
        app.framePositionField.Position = [147 27 65 22];

        app.RefreshAppButton = uibutton(app.FileselectionPanel, 'push');
        app.RefreshAppButton.ButtonPushedFcn = createCallbackFcn(app, @RefreshAppButtonPushed, true);
        app.RefreshAppButton.BackgroundColor = [0.502 0.502 0.502];
        app.RefreshAppButton.FontColor = [0.902 0.902 0.902];
        app.RefreshAppButton.Tooltip = {'Refresh the app'};
        app.RefreshAppButton.Position = [5 11 31 23];
        app.RefreshAppButton.Text = '👌';

        app.AdvancedButton = uibutton(app.FileselectionPanel, 'push');
        app.AdvancedButton.ButtonPushedFcn = createCallbackFcn(app, @AdvancedButtonPushed, true);
        app.AdvancedButton.BackgroundColor = [0.502 0.502 0.502];
        app.AdvancedButton.FontColor = [1 1 1];
        app.AdvancedButton.Tooltip = {'Advanced settings'};
        app.AdvancedButton.Position = [5 39 31 23];
        app.AdvancedButton.Text = '📎';
    end

    % -----------------------------------------------------------------------
    function createBatchVideoPanel(app)
        app.BatchselectionparametersandVideoRenderingPanel = uipanel(app.FileselectionPanel);
        app.BatchselectionparametersandVideoRenderingPanel.ForegroundColor = [0.902 0.902 0.902];
        app.BatchselectionparametersandVideoRenderingPanel.Title = 'Batch selection parameters and Video Rendering';
        app.BatchselectionparametersandVideoRenderingPanel.BackgroundColor = [0.2 0.2 0.2];
        app.BatchselectionparametersandVideoRenderingPanel.Position = [10 237 244 433];

        p = app.BatchselectionparametersandVideoRenderingPanel;

        app.rephasingCheckBox = uicheckbox(p);
        app.rephasingCheckBox.Visible = 'off';
        app.rephasingCheckBox.Text = 'rephasing';
        app.rephasingCheckBox.FontColor = [0.902 0.902 0.902];
        app.rephasingCheckBox.Position = [38 106 75 22];
        app.rephasingCheckBox.Value = true;

        app.phaseregistrationCheckBox = uicheckbox(p);
        app.phaseregistrationCheckBox.Visible = 'off';
        app.phaseregistrationCheckBox.Tooltip = {'Activates video registration. Check this if the video is too shaky.'};
        app.phaseregistrationCheckBox.Text = 'phase registration';
        app.phaseregistrationCheckBox.FontColor = [0.902 0.902 0.902];
        app.phaseregistrationCheckBox.Position = [119 106 117 22];

        app.temporalfilterCheckBox = uicheckbox(p);
        app.temporalfilterCheckBox.Visible = 'off';
        app.temporalfilterCheckBox.Text = 'temporal filter';
        app.temporalfilterCheckBox.FontColor = [0.902 0.902 0.902];
        app.temporalfilterCheckBox.Position = [38 45 95 22];

        app.temporalfilterEditField = uieditfield(p, 'numeric');
        app.temporalfilterEditField.Limits = [1 Inf];
        app.temporalfilterEditField.FontColor = [0.8 0.8 0.8];
        app.temporalfilterEditField.BackgroundColor = [0.149 0.149 0.149];
        app.temporalfilterEditField.Visible = 'off';
        app.temporalfilterEditField.Tooltip = {'Laser wavelength in nanometers'};
        app.temporalfilterEditField.Position = [141 44 54 22];
        app.temporalfilterEditField.Value = 2;

        app.FoldermanagementButton = uibutton(p, 'push');
        app.FoldermanagementButton.ButtonPushedFcn = createCallbackFcn(app, @FoldermanagementButtonPushed, true);
        app.FoldermanagementButton.BackgroundColor = [0.502 0.502 0.502];
        app.FoldermanagementButton.FontColor = [0.902 0.902 0.902];
        app.FoldermanagementButton.Tooltip = {'Open a window to render all files from different folders with their config files'};
        app.FoldermanagementButton.Position = [7 171 123 23];
        app.FoldermanagementButton.Text = 'Folder management';

        app.VideoRenderingButton = uibutton(p, 'push');
        app.VideoRenderingButton.ButtonPushedFcn = createCallbackFcn(app, @VideoRenderingButtonPushed, true);
        app.VideoRenderingButton.BackgroundColor = [0.502 0.502 0.502];
        app.VideoRenderingButton.FontColor = [0.902 0.902 0.902];
        app.VideoRenderingButton.Tooltip = {'Render ''batch_size'' frame batchs spaced by ''batch_stride'' and output a video of different image types'};
        app.VideoRenderingButton.Position = [133 171 104 23];
        app.VideoRenderingButton.Text = 'Video Rendering';

        app.iterativeregistrationCheckBox = uicheckbox(p);
        app.iterativeregistrationCheckBox.Visible = 'off';
        app.iterativeregistrationCheckBox.Tooltip = {'''Activates video registration. Check this if the video is too shaky.'''};
        app.iterativeregistrationCheckBox.Text = 'iterative registration';
        app.iterativeregistrationCheckBox.FontColor = [0.902 0.902 0.902];
        app.iterativeregistrationCheckBox.Position = [38 66 131 22];

        app.showrefCheckBox = uicheckbox(p);
        app.showrefCheckBox.Visible = 'off';
        app.showrefCheckBox.Text = 'show ref';
        app.showrefCheckBox.FontColor = [0.902 0.902 0.902];
        app.showrefCheckBox.Position = [38 25 67 22];

        app.LoadconfigButton = uibutton(p, 'push');
        app.LoadconfigButton.ButtonPushedFcn = createCallbackFcn(app, @LoadconfigButtonPushed, true);
        app.LoadconfigButton.BackgroundColor = [0.502 0.502 0.502];
        app.LoadconfigButton.FontColor = [0.902 0.902 0.902];
        app.LoadconfigButton.Tooltip = {'Save a configuration for the video rendering of a file'};
        app.LoadconfigButton.Position = [7 198 100 23];
        app.LoadconfigButton.Text = 'Load config';

        app.image_registration = uicheckbox(p);
        app.image_registration.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.image_registration.Tooltip = {'Activate frame to frame translation registration of images'};
        app.image_registration.Text = 'image registration';
        app.image_registration.FontColor = [0.902 0.902 0.902];
        app.image_registration.Position = [35 4 117 22];

        app.batchstrideEditFieldLabel = uilabel(p);
        app.batchstrideEditFieldLabel.HorizontalAlignment = 'center';
        app.batchstrideEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.batchstrideEditFieldLabel.Position = [7 121 84 22];
        app.batchstrideEditFieldLabel.Text = 'batch stride';

        app.batch_stride = uieditfield(p, 'numeric');
        app.batch_stride.Limits = [0 Inf];
        app.batch_stride.ValueDisplayFormat = '%.0f';
        app.batch_stride.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.batch_stride.FontColor = [0.8 0.8 0.8];
        app.batch_stride.BackgroundColor = [0.149 0.149 0.149];
        app.batch_stride.Tooltip = {'Number of interferograms to skip between two images'};
        app.batch_stride.Position = [90 121 100 22];

        app.refbatchsizeEditFieldLabel = uilabel(p);
        app.refbatchsizeEditFieldLabel.HorizontalAlignment = 'center';
        app.refbatchsizeEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.refbatchsizeEditFieldLabel.Position = [7 99 80 22];
        app.refbatchsizeEditFieldLabel.Text = 'reg batch size';

        app.batch_size_registration = uieditfield(p, 'numeric');
        app.batch_size_registration.Limits = [0 Inf];
        app.batch_size_registration.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.batch_size_registration.FontColor = [0.8 0.8 0.8];
        app.batch_size_registration.BackgroundColor = [0.149 0.149 0.149];
        app.batch_size_registration.Tooltip = {'Number of interferograms used to compute the image used as reference in registration'};
        app.batch_size_registration.Position = [90 99 100 22];

        app.registration_disc_ratio = uieditfield(p, 'numeric');
        app.registration_disc_ratio.Limits = [0 1000];
        app.registration_disc_ratio.ValueChangedFcn = createCallbackFcn(app, @registration_disc_ratioValueChanged, true);
        app.registration_disc_ratio.FontColor = [0.8 0.8 0.8];
        app.registration_disc_ratio.BackgroundColor = [0.149 0.149 0.149];
        app.registration_disc_ratio.Tooltip = {'Size of a disk centered on the images used to compute the registration shifts (0 is empty and 1 is a disc of the maximum dimension).'};
        app.registration_disc_ratio.Position = [188 4 54 22];

        app.registrationDiscLabel = uilabel(p);
        app.registrationDiscLabel.HorizontalAlignment = 'center';
        app.registrationDiscLabel.FontColor = [0.8 0.8 0.8];
        app.registrationDiscLabel.Position = [157 4 26 22];
        app.registrationDiscLabel.Text = 'disk';

        app.Image_typesListBox = uilistbox(p);
        app.Image_typesListBox.Items = {};
        app.Image_typesListBox.Multiselect = 'on';
        app.Image_typesListBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.Image_typesListBox.Tooltip = {'Image types output giving extracting different informations from a batch of frames'};
        app.Image_typesListBox.FontColor = [1 1 1];
        app.Image_typesListBox.BackgroundColor = [0.149 0.149 0.149];
        app.Image_typesListBox.Position = [16 231 211 178];
        app.Image_typesListBox.Value = {};

        app.batchsizeLabel = uilabel(p);
        app.batchsizeLabel.HorizontalAlignment = 'center';
        app.batchsizeLabel.FontColor = [0.8 0.8 0.8];
        app.batchsizeLabel.Position = [7 143 84 22];
        app.batchsizeLabel.Text = 'batch size';

        app.batch_size = uieditfield(p, 'numeric');
        app.batch_size.Limits = [0 Inf];
        app.batch_size.ValueDisplayFormat = '%.0f';
        app.batch_size.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.batch_size.FontColor = [0.8 0.8 0.8];
        app.batch_size.BackgroundColor = [0.149 0.149 0.149];
        app.batch_size.Tooltip = {'Number of interferograms used to compute the image'};
        app.batch_size.Position = [90 143 100 22];

        app.SaveVideoButton = uibutton(p, 'push');
        app.SaveVideoButton.ButtonPushedFcn = createCallbackFcn(app, @SaveVideoButtonPushed, true);
        app.SaveVideoButton.BackgroundColor = [0.502 0.502 0.502];
        app.SaveVideoButton.FontColor = [0.902 0.902 0.902];
        app.SaveVideoButton.Visible = 'off';
        app.SaveVideoButton.Position = [138 70 100 23];
        app.SaveVideoButton.Text = 'Save Video';

        app.VideoRenderingLamp = uilamp(p);
        app.VideoRenderingLamp.Position = [226 153 12 12];

        app.ShowHistogramButton = uibutton(p, 'push');
        app.ShowHistogramButton.ButtonPushedFcn = createCallbackFcn(app, @ShowHistogramButtonPushed, true);
        app.ShowHistogramButton.BackgroundColor = [0.502 0.502 0.502];
        app.ShowHistogramButton.FontColor = [0.902 0.902 0.902];
        app.ShowHistogramButton.Tooltip = {'Show the full frame batch histogram'};
        app.ShowHistogramButton.Position = [9 70 70 23];
        app.ShowHistogramButton.Text = 'Histogram';

        app.PlayButton = uibutton(p, 'push');
        app.PlayButton.ButtonPushedFcn = createCallbackFcn(app, @PlayButtonPushed, true);
        app.PlayButton.BackgroundColor = [0.502 0.502 0.502];
        app.PlayButton.FontColor = [0.902 0.902 0.902];
        app.PlayButton.Tooltip = {'Play the video'};
        app.PlayButton.Position = [214 121 25 23];
        app.PlayButton.Text = 'l>';

        app.SaveconfigButton = uibutton(p, 'push');
        app.SaveconfigButton.ButtonPushedFcn = createCallbackFcn(app, @SaveconfigButtonPushed, true);
        app.SaveconfigButton.BackgroundColor = [0.502 0.502 0.502];
        app.SaveconfigButton.FontColor = [0.902 0.902 0.902];
        app.SaveconfigButton.Tooltip = {'Save a configuration for the video rendering of a file'};
        app.SaveconfigButton.Position = [112 197 100 23];
        app.SaveconfigButton.Text = 'Save config';

        app.applyshackhartmannfromref = uicheckbox(p);
        app.applyshackhartmannfromref.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.applyshackhartmannfromref.Tooltip = {'Activate frame to frame translation registration of images'};
        app.applyshackhartmannfromref.Text = 'refocus from ref (numeric shack hartmann)';
        app.applyshackhartmannfromref.FontColor = [0.902 0.902 0.902];
        app.applyshackhartmannfromref.Position = [35 25 251 22];

        app.AutofocusFromRef = uicheckbox(p);
        app.AutofocusFromRef.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.AutofocusFromRef.Tooltip = {'Activate frame to frame translation registration of images'};
        app.AutofocusFromRef.Text = 'autofocus from ref';
        app.AutofocusFromRef.FontColor = [0.902 0.902 0.902];
        app.AutofocusFromRef.Position = [35 45 119 22];
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

        app.phi1EditFieldLabel = uilabel(p);
        app.phi1EditFieldLabel.HorizontalAlignment = 'right';
        app.phi1EditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.phi1EditFieldLabel.Position = [102 258 28 22];
        app.phi1EditFieldLabel.Text = 'phi1';

        app.phi1EditField = uieditfield(p, 'numeric');
        app.phi1EditField.Position = [134 258 21 21];

        app.phi2EditFieldLabel = uilabel(p);
        app.phi2EditFieldLabel.HorizontalAlignment = 'right';
        app.phi2EditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.phi2EditFieldLabel.Position = [173 261 28 22];
        app.phi2EditFieldLabel.Text = 'phi2';

        app.phi2EditField = uieditfield(p, 'numeric');
        app.phi2EditField.Position = [205 261 21 21];

        app.nu1EditFieldLabel = uilabel(p);
        app.nu1EditFieldLabel.HorizontalAlignment = 'right';
        app.nu1EditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.nu1EditFieldLabel.Position = [107 230 26 22];
        app.nu1EditFieldLabel.Text = 'nu1';

        app.nu1EditField = uieditfield(p, 'numeric');
        app.nu1EditField.Position = [135 230 21 21];

        app.nu2EditFieldLabel = uilabel(p);
        app.nu2EditFieldLabel.HorizontalAlignment = 'right';
        app.nu2EditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.nu2EditFieldLabel.Position = [175 230 26 22];
        app.nu2EditFieldLabel.Text = 'nu2';

        app.nu2EditField = uieditfield(p, 'numeric');
        app.nu2EditField.FontColor = [0.149 0.149 0.149];
        app.nu2EditField.Position = [205 230 21 21];

        app.unitcellsinlatticeEditFieldLabel = uilabel(p);
        app.unitcellsinlatticeEditFieldLabel.HorizontalAlignment = 'right';
        app.unitcellsinlatticeEditFieldLabel.FontColor = [0.902 0.902 0.902];
        app.unitcellsinlatticeEditFieldLabel.Position = [18 170 110 22];
        app.unitcellsinlatticeEditFieldLabel.Text = '# unit cells in lattice';

        app.unitcellsinlatticeEditField = uieditfield(p, 'numeric');
        app.unitcellsinlatticeEditField.Limits = [0 Inf];
        app.unitcellsinlatticeEditField.Position = [135 170 29 22];
        app.unitcellsinlatticeEditField.Value = 8;

        app.r1EditFieldLabel = uilabel(p);
        app.r1EditFieldLabel.HorizontalAlignment = 'right';
        app.r1EditFieldLabel.FontColor = [0.902 0.902 0.902];
        app.r1EditFieldLabel.Position = [102 140 25 22];
        app.r1EditFieldLabel.Text = 'r1';

        app.r1EditField = uieditfield(p, 'numeric');
        app.r1EditField.Limits = [0 Inf];
        app.r1EditField.Position = [135 138 29 23];
        app.r1EditField.Value = 3;

        app.xystrideEditFieldLabel = uilabel(p);
        app.xystrideEditFieldLabel.HorizontalAlignment = 'right';
        app.xystrideEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.xystrideEditFieldLabel.Position = [59 108 50 22];
        app.xystrideEditFieldLabel.Text = 'xy stride';

        app.xystrideEditField = uieditfield(p, 'numeric');
        app.xystrideEditField.Position = [124 105 41 27];
        app.xystrideEditField.Value = 32;

        app.SVDx_SubApEditFieldLabel = uilabel(p);
        app.SVDx_SubApEditFieldLabel.HorizontalAlignment = 'right';
        app.SVDx_SubApEditFieldLabel.FontColor = [0.902 0.902 0.902];
        app.SVDx_SubApEditFieldLabel.Position = [160 317 79 22];
        app.SVDx_SubApEditFieldLabel.Text = 'SVDx_SubAp';

        app.SVDx_SubApEditField = uieditfield(p, 'numeric');
        app.SVDx_SubApEditField.Limits = [0 20];
        app.SVDx_SubApEditField.Position = [247 317 26 22];
        app.SVDx_SubApEditField.Value = 3;

        app.SVDxCheckBox = uicheckbox(p);
        app.SVDxCheckBox.Text = 'SVDx';
        app.SVDxCheckBox.FontColor = [0.902 0.902 0.902];
        app.SVDxCheckBox.Position = [85 317 53 22];

        app.SVDThresholdEditField = uieditfield(p, 'numeric');
        app.SVDThresholdEditField.Limits = [0 Inf];
        app.SVDThresholdEditField.Enable = 'off';
        app.SVDThresholdEditField.Position = [247 291 26 22];
        app.SVDThresholdEditField.Value = 64;

        app.SVDTresholdEditFieldLabel = uilabel(p);
        app.SVDTresholdEditFieldLabel.HorizontalAlignment = 'right';
        app.SVDTresholdEditFieldLabel.FontColor = [0.902 0.902 0.902];
        app.SVDTresholdEditFieldLabel.Position = [153 291 86 22];
        app.SVDTresholdEditFieldLabel.Text = 'SVD Threshold';

        app.SVDThresholdCheckBox = uicheckbox(p);
        app.SVDThresholdCheckBox.Text = '';
        app.SVDThresholdCheckBox.FontColor = [0.902 0.902 0.902];
        app.SVDThresholdCheckBox.Position = [137 293 25 22];

        app.SVDStrideEditField = uieditfield(p, 'numeric');
        app.SVDStrideEditField.Limits = [0 Inf];
        app.SVDStrideEditField.Tooltip = {'Sub sampling parameter for faster SVD calculations. Defaults to 1 -> full image, 2 -> one pixel on two, ...'};
        app.SVDStrideEditField.Position = [256 30 26 22];
        app.SVDStrideEditField.Value = 1;

        app.SVDTresholdEditFieldLabel_2 = uilabel(p);
        app.SVDTresholdEditFieldLabel_2.HorizontalAlignment = 'right';
        app.SVDTresholdEditFieldLabel_2.FontColor = [0.902 0.902 0.902];
        app.SVDTresholdEditFieldLabel_2.Position = [184 30 64 22];
        app.SVDTresholdEditFieldLabel_2.Text = 'SVD Stride';
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

        app.zernikeranksEditFieldLabel = uilabel(p);
        app.zernikeranksEditFieldLabel.HorizontalAlignment = 'center';
        app.zernikeranksEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.zernikeranksEditFieldLabel.Position = [9 230 77 22];
        app.zernikeranksEditFieldLabel.Text = 'zernike ranks';

        app.shackhartmannzernikeranksEditField = uieditfield(p, 'numeric');
        app.shackhartmannzernikeranksEditField.Limits = [2 6];
        app.shackhartmannzernikeranksEditField.RoundFractionalValues = 'on';
        app.shackhartmannzernikeranksEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.shackhartmannzernikeranksEditField.FontColor = [0.8 0.8 0.8];
        app.shackhartmannzernikeranksEditField.BackgroundColor = [0.149 0.149 0.149];
        app.shackhartmannzernikeranksEditField.Tooltip = {'Number of zernike ranks to use for aberration correction'};
        app.shackhartmannzernikeranksEditField.Position = [142 230 43 22];
        app.shackhartmannzernikeranksEditField.Value = 2;

        app.subaperturemarginEditFieldLabel = uilabel(p);
        app.subaperturemarginEditFieldLabel.HorizontalAlignment = 'center';
        app.subaperturemarginEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.subaperturemarginEditFieldLabel.Visible = 'off';
        app.subaperturemarginEditFieldLabel.Position = [9 161 110 22];
        app.subaperturemarginEditFieldLabel.Text = 'subaperture margin';

        app.subaperturemarginEditField = uieditfield(p, 'numeric');
        app.subaperturemarginEditField.Limits = [0 Inf];
        app.subaperturemarginEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.subaperturemarginEditField.FontColor = [0.8 0.8 0.8];
        app.subaperturemarginEditField.BackgroundColor = [0.149 0.149 0.149];
        app.subaperturemarginEditField.Visible = 'off';
        app.subaperturemarginEditField.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
        app.subaperturemarginEditField.Position = [142 161 43 22];
        app.subaperturemarginEditField.Value = 0.15;

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

        app.minEditField_2Label = uilabel(p);
        app.minEditField_2Label.HorizontalAlignment = 'right';
        app.minEditField_2Label.FontColor = [1 1 1];
        app.minEditField_2Label.Visible = 'off';
        app.minEditField_2Label.Position = [9 314 25 22];
        app.minEditField_2Label.Text = 'min';

        app.minSubAp_PCAEditField = uieditfield(p, 'numeric');
        app.minSubAp_PCAEditField.Limits = [1 Inf];
        app.minSubAp_PCAEditField.Visible = 'off';
        app.minSubAp_PCAEditField.Position = [41 317 24 16];
        app.minSubAp_PCAEditField.Value = 1;

        app.maxEditField_2Label = uilabel(p);
        app.maxEditField_2Label.HorizontalAlignment = 'right';
        app.maxEditField_2Label.FontColor = [1 1 1];
        app.maxEditField_2Label.Visible = 'off';
        app.maxEditField_2Label.Position = [73 314 28 22];
        app.maxEditField_2Label.Text = 'max';

        app.maxSubAp_PCAEditField = uieditfield(p, 'numeric');
        app.maxSubAp_PCAEditField.Limits = [1 Inf];
        app.maxSubAp_PCAEditField.Visible = 'off';
        app.maxSubAp_PCAEditField.Position = [108 317 24 16];
        app.maxSubAp_PCAEditField.Value = 16;

        app.volumesizeEditFieldLabel = uilabel(p);
        app.volumesizeEditFieldLabel.HorizontalAlignment = 'right';
        app.volumesizeEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.volumesizeEditFieldLabel.Visible = 'off';
        app.volumesizeEditFieldLabel.Position = [157 53 69 22];
        app.volumesizeEditFieldLabel.Text = 'volume size';

        app.volumesizeEditField = uieditfield(p, 'numeric');
        app.volumesizeEditField.Limits = [1 Inf];
        app.volumesizeEditField.Visible = 'off';
        app.volumesizeEditField.Position = [231 54 31 21];
        app.volumesizeEditField.Value = 256;

        app.rangeZEditFieldLabel = uilabel(p);
        app.rangeZEditFieldLabel.HorizontalAlignment = 'right';
        app.rangeZEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.rangeZEditFieldLabel.Visible = 'off';
        app.rangeZEditFieldLabel.Position = [180 26 44 22];
        app.rangeZEditFieldLabel.Text = 'rangeZ';

        app.rangeZEditField = uieditfield(p, 'numeric');
        app.rangeZEditField.Limits = [1 Inf];
        app.rangeZEditField.Visible = 'off';
        app.rangeZEditField.Position = [232 25 30 22];
        app.rangeZEditField.Value = 1;

        app.rangeYEditFieldLabel = uilabel(p);
        app.rangeYEditFieldLabel.HorizontalAlignment = 'right';
        app.rangeYEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.rangeYEditFieldLabel.Visible = 'off';
        app.rangeYEditFieldLabel.Position = [14 26 44 22];
        app.rangeYEditFieldLabel.Text = 'rangeY';

        app.rangeYEditField = uieditfield(p, 'numeric');
        app.rangeYEditField.Limits = [1 Inf];
        app.rangeYEditField.Visible = 'off';
        app.rangeYEditField.Position = [66 25 30 22];
        app.rangeYEditField.Value = 1;

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

        app.subapnumpositionsEditFieldLabel = uilabel(p);
        app.subapnumpositionsEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.subapnumpositionsEditFieldLabel.Position = [12 207 115 22];
        app.subapnumpositionsEditFieldLabel.Text = 'subap num positions';

        app.subapnumpositionsEditField = uieditfield(p, 'numeric');
        app.subapnumpositionsEditField.Limits = [1 20];
        app.subapnumpositionsEditField.RoundFractionalValues = 'on';
        app.subapnumpositionsEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.subapnumpositionsEditField.FontColor = [0.8 0.8 0.8];
        app.subapnumpositionsEditField.BackgroundColor = [0.149 0.149 0.149];
        app.subapnumpositionsEditField.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
        app.subapnumpositionsEditField.Position = [142 207 43 22];
        app.subapnumpositionsEditField.Value = 5;

        app.imagesubapsizeratioEditFieldLabel = uilabel(p);
        app.imagesubapsizeratioEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.imagesubapsizeratioEditFieldLabel.Position = [12 184 125 22];
        app.imagesubapsizeratioEditFieldLabel.Text = 'image subap size ratio';

        app.imagesubapsizeratioEditField = uieditfield(p, 'numeric');
        app.imagesubapsizeratioEditField.Limits = [1 20];
        app.imagesubapsizeratioEditField.RoundFractionalValues = 'on';
        app.imagesubapsizeratioEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.imagesubapsizeratioEditField.FontColor = [0.8 0.8 0.8];
        app.imagesubapsizeratioEditField.BackgroundColor = [0.149 0.149 0.149];
        app.imagesubapsizeratioEditField.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
        app.imagesubapsizeratioEditField.Position = [142 184 43 22];
        app.imagesubapsizeratioEditField.Value = 5;

        app.numberofiterationLabel = uilabel(p);
        app.numberofiterationLabel.HorizontalAlignment = 'center';
        app.numberofiterationLabel.FontColor = [0.8 0.8 0.8];
        app.numberofiterationLabel.Position = [149 309 105 22];
        app.numberofiterationLabel.Text = 'number of iteration';

        app.NumberOfIterationEditField = uieditfield(p, 'numeric');
        app.NumberOfIterationEditField.Limits = [1 Inf];
        app.NumberOfIterationEditField.RoundFractionalValues = 'on';
        app.NumberOfIterationEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.NumberOfIterationEditField.FontColor = [0.8 0.8 0.8];
        app.NumberOfIterationEditField.BackgroundColor = [0.149 0.149 0.149];
        app.NumberOfIterationEditField.Tooltip = {'Number of zernike ranks to use for aberration correction'};
        app.NumberOfIterationEditField.Position = [268 309 27 22];
        app.NumberOfIterationEditField.Value = 3;

        app.calibrationfactorLabel = uilabel(p);
        app.calibrationfactorLabel.HorizontalAlignment = 'center';
        app.calibrationfactorLabel.FontColor = [0.8 0.8 0.8];
        app.calibrationfactorLabel.Visible = 'off';
        app.calibrationfactorLabel.Position = [149 159 93 22];
        app.calibrationfactorLabel.Text = 'calibration factor';

        app.CalibrationFactorEditField = uieditfield(p, 'numeric');
        app.CalibrationFactorEditField.Limits = [0 Inf];
        app.CalibrationFactorEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.CalibrationFactorEditField.FontColor = [0.8 0.8 0.8];
        app.CalibrationFactorEditField.BackgroundColor = [0.149 0.149 0.149];
        app.CalibrationFactorEditField.Visible = 'off';
        app.CalibrationFactorEditField.Tooltip = {'Number of zernike ranks to use for aberration correction'};
        app.CalibrationFactorEditField.Position = [268 158 27 22];
        app.CalibrationFactorEditField.Value = 60;

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
        app.RenderingparametersPanel = uipanel(app.RenderingInnerGrid);
        app.RenderingparametersPanel.ForegroundColor = [0.8 0.8 0.8];
        app.RenderingparametersPanel.Title = 'Rendering parameters';
        app.RenderingparametersPanel.BackgroundColor = [0.2 0.2 0.2];
        app.RenderingparametersPanel.Layout.Row = 1;
        app.RenderingparametersPanel.Layout.Column = 1;

        p = app.RenderingparametersPanel;

        app.svd_threshold_reset_button = uibutton(p, 'push');
        app.svd_threshold_reset_button.ButtonPushedFcn = createCallbackFcn(app, @svd_threshold_reset_buttonPushed, true);
        app.svd_threshold_reset_button.BackgroundColor = [0.149 0.149 0.149];
        app.svd_threshold_reset_button.FontColor = [0.9412 0.9412 0.9412];
        app.svd_threshold_reset_button.Position = [152 235 90 23];
        app.svd_threshold_reset_button.Text = 'svd_threshold';

        app.spatial_filter = uicheckbox(p);
        app.spatial_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_filter.Tooltip = {'Filter the spatial frequencies of the interferograms keeping only those between spatial filter range1 and 2 (between 0 and 1-> highest dimension)'};
        app.spatial_filter.Text = 'spatial_filter';
        app.spatial_filter.FontColor = [0.9412 0.9412 0.9412];
        app.spatial_filter.Position = [9 331 86 22];

        app.hilbert_filter = uicheckbox(p);
        app.hilbert_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.hilbert_filter.Tooltip = {'Apply a hilbert transformation on the interferogram batch to get an analytical signal of each pixel.'};
        app.hilbert_filter.Text = 'hilbert_filter';
        app.hilbert_filter.FontColor = [0.9412 0.9412 0.9412];
        app.hilbert_filter.Position = [9 307 84 22];

        app.spatial_filter_range = uilabel(p);
        app.spatial_filter_range.FontColor = [0.9412 0.9412 0.9412];
        app.spatial_filter_range.Position = [94 331 106 22];
        app.spatial_filter_range.Text = 'spatial_filter_range';

        app.spatial_filter_range1 = uieditfield(p, 'numeric');
        app.spatial_filter_range1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_filter_range1.FontColor = [1 1 1];
        app.spatial_filter_range1.BackgroundColor = [0.149 0.149 0.149];
        app.spatial_filter_range1.Position = [199 331 29 22];

        app.spatial_filter_range2 = uieditfield(p, 'numeric');
        app.spatial_filter_range2.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_filter_range2.FontColor = [1 1 1];
        app.spatial_filter_range2.BackgroundColor = [0.149 0.149 0.149];
        app.spatial_filter_range2.Position = [240 331 28 22];

        app.spatial_transformationDropDownLabel = uilabel(p);
        app.spatial_transformationDropDownLabel.HorizontalAlignment = 'right';
        app.spatial_transformationDropDownLabel.FontColor = [0.9412 0.9412 0.9412];
        app.spatial_transformationDropDownLabel.Position = [9 285 123 22];
        app.spatial_transformationDropDownLabel.Text = 'spatial_transformation';

        app.spatial_transformation = uidropdown(p);
        app.spatial_transformation.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_transformation.Tooltip = {'Type of light propagation calculation to perform (depends of the experimental setup)'};
        app.spatial_transformation.FontColor = [1 1 1];
        app.spatial_transformation.BackgroundColor = [0.502 0.502 0.502];
        app.spatial_transformation.Position = [147 285 100 22];

        app.spatial_propagationEditFieldLabel = uilabel(p);
        app.spatial_propagationEditFieldLabel.HorizontalAlignment = 'right';
        app.spatial_propagationEditFieldLabel.FontColor = [0.9412 0.9412 0.9412];
        app.spatial_propagationEditFieldLabel.Position = [15 261 110 22];
        app.spatial_propagationEditFieldLabel.Text = 'spatial_propagation';

        app.spatial_propagation = uieditfield(p, 'numeric');
        app.spatial_propagation.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_propagation.FontColor = [1 1 1];
        app.spatial_propagation.BackgroundColor = [0.149 0.149 0.149];
        app.spatial_propagation.Tooltip = {'Distance of spatial reconstruction using the preceding calculation scheme in (m) '};
        app.spatial_propagation.Position = [140 261 60 22];

        app.svd_filter = uicheckbox(p);
        app.svd_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svd_filter.Tooltip = {'Filter to remove intense time correlated feature images of the output fluctuation hologram using eigenvalue decomposition of the correlation matrix of frames.'};
        app.svd_filter.Text = 'svd_filter';
        app.svd_filter.FontColor = [0.9412 0.9412 0.9412];
        app.svd_filter.Position = [17 236 70 22];

        app.svdx_filter = uicheckbox(p);
        app.svdx_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_filter.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.svdx_filter.Text = 'svdx_filter';
        app.svdx_filter.FontColor = [0.9412 0.9412 0.9412];
        app.svdx_filter.Position = [17 209 76 22];

        app.svd_threshold = uieditfield(p, 'numeric');
        app.svd_threshold.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svd_threshold.FontColor = [1 1 1];
        app.svd_threshold.BackgroundColor = [0.149 0.149 0.149];
        app.svd_threshold.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svd_threshold.Position = [246 236 31 22];

        app.time_transformDropDownLabel = uilabel(p);
        app.time_transformDropDownLabel.HorizontalAlignment = 'right';
        app.time_transformDropDownLabel.FontColor = [0.9412 0.9412 0.9412];
        app.time_transformDropDownLabel.Position = [15 155 85 22];
        app.time_transformDropDownLabel.Text = 'time_transform';

        app.time_transform = uidropdown(p);
        app.time_transform.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.time_transform.Tooltip = {'Time tranformation to aggregate the fluctuation hologram. FFT is a frequency domain tranform and pass bad filter, PCA is a projection on intensity ordered eigen vectors, ICA is experimental.'};
        app.time_transform.FontColor = [1 1 1];
        app.time_transform.BackgroundColor = [0.502 0.502 0.502];
        app.time_transform.Position = [115 155 100 22];

        app.frequency_rangeLabel = uilabel(p);
        app.frequency_rangeLabel.FontColor = [0.9412 0.9412 0.9412];
        app.frequency_rangeLabel.Position = [17 130 95 22];
        app.frequency_rangeLabel.Text = 'frequency_range';

        app.time_range1 = uieditfield(p, 'numeric');
        app.time_range1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.time_range1.FontColor = [1 1 1];
        app.time_range1.BackgroundColor = [0.149 0.149 0.149];
        app.time_range1.Position = [122 130 38 22];

        app.time_range2 = uieditfield(p, 'numeric');
        app.time_range2.ValueChangedFcn = createCallbackFcn(app, @time_range2ValueChanged, true);
        app.time_range2.FontColor = [1 1 1];
        app.time_range2.BackgroundColor = [0.149 0.149 0.149];
        app.time_range2.Position = [177 130 38 22];

        app.flat_field_gwEditFieldLabel = uilabel(p);
        app.flat_field_gwEditFieldLabel.HorizontalAlignment = 'right';
        app.flat_field_gwEditFieldLabel.FontColor = [0.9412 0.9412 0.9412];
        app.flat_field_gwEditFieldLabel.Position = [17 79 72 22];
        app.flat_field_gwEditFieldLabel.Text = 'flat_field_gw';

        app.flat_field_gw = uieditfield(p, 'numeric');
        app.flat_field_gw.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flat_field_gw.FontColor = [1 1 1];
        app.flat_field_gw.BackgroundColor = [0.149 0.149 0.149];
        app.flat_field_gw.Tooltip = {'flat_filed parameter to apply to some of the output images (gaussian width in pixels to divide the image to correct uneven illumination of images).'};
        app.flat_field_gw.Position = [104 79 100 22];

        app.RenderPreviewButton = uibutton(p, 'push');
        app.RenderPreviewButton.ButtonPushedFcn = createCallbackFcn(app, @RenderPreviewButtonPushed, true);
        app.RenderPreviewButton.BackgroundColor = [0.502 0.502 0.502];
        app.RenderPreviewButton.FontColor = [1 1 1];
        app.RenderPreviewButton.Position = [204 42 100 23];
        app.RenderPreviewButton.Text = 'Render Preview';

        app.SavePreviewButton = uibutton(p, 'push');
        app.SavePreviewButton.ButtonPushedFcn = createCallbackFcn(app, @SavePreviewButtonPushed, true);
        app.SavePreviewButton.BackgroundColor = [0.502 0.502 0.502];
        app.SavePreviewButton.FontColor = [1 1 1];
        app.SavePreviewButton.Position = [204 7 100 23];
        app.SavePreviewButton.Text = 'Save Preview';

        app.RenderPreviewLamp = uilamp(p);
        app.RenderPreviewLamp.Position = [188 48 12 12];

        app.svdx_t_filter = uicheckbox(p);
        app.svdx_t_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_t_filter.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.svdx_t_filter.Text = 'svd_x_t_filter';
        app.svdx_t_filter.FontColor = [0.9412 0.9412 0.9412];
        app.svdx_t_filter.Position = [17 183 93 22];

        app.index_rangeLabel = uilabel(p);
        app.index_rangeLabel.FontColor = [0.9412 0.9412 0.9412];
        app.index_rangeLabel.Position = [17 105 71 22];
        app.index_rangeLabel.Text = 'index_range';

        app.index_range1 = uieditfield(p, 'numeric');
        app.index_range1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.index_range1.FontColor = [1 1 1];
        app.index_range1.BackgroundColor = [0.149 0.149 0.149];
        app.index_range1.Position = [122 105 38 22];

        app.index_range2 = uieditfield(p, 'numeric');
        app.index_range2.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.index_range2.FontColor = [1 1 1];
        app.index_range2.BackgroundColor = [0.149 0.149 0.149];
        app.index_range2.Position = [177 105 38 22];

        app.svdx_threshold = uieditfield(p, 'numeric');
        app.svdx_threshold.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_threshold.FontColor = [1 1 1];
        app.svdx_threshold.BackgroundColor = [0.149 0.149 0.149];
        app.svdx_threshold.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svdx_threshold.Position = [246 207 31 22];

        app.svdx_t_threshold = uieditfield(p, 'numeric');
        app.svdx_t_threshold.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_t_threshold.FontColor = [1 1 1];
        app.svdx_t_threshold.BackgroundColor = [0.149 0.149 0.149];
        app.svdx_t_threshold.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svdx_t_threshold.Position = [246 182 31 22];

        app.svdx_Nsub = uieditfield(p, 'numeric');
        app.svdx_Nsub.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_Nsub.FontColor = [1 1 1];
        app.svdx_Nsub.BackgroundColor = [0.149 0.149 0.149];
        app.svdx_Nsub.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svdx_Nsub.Position = [189 207 31 22];

        app.svdx_t_Nsub = uieditfield(p, 'numeric');
        app.svdx_t_Nsub.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_t_Nsub.FontColor = [1 1 1];
        app.svdx_t_Nsub.BackgroundColor = [0.149 0.149 0.149];
        app.svdx_t_Nsub.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svdx_t_Nsub.Position = [189 182 31 22];

        app.NsubxLabel = uilabel(p);
        app.NsubxLabel.HorizontalAlignment = 'right';
        app.NsubxLabel.FontColor = [0.902 0.902 0.902];
        app.NsubxLabel.Position = [144 206 42 22];
        app.NsubxLabel.Text = 'Nsub x';

        app.NsubxtLabel = uilabel(p);
        app.NsubxtLabel.HorizontalAlignment = 'right';
        app.NsubxtLabel.FontColor = [0.902 0.902 0.902];
        app.NsubxtLabel.Position = [140 183 46 22];
        app.NsubxtLabel.Text = 'Nsub xt';

        app.flip_y = uicheckbox(p);
        app.flip_y.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_y.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.flip_y.Text = 'flip_y';
        app.flip_y.FontColor = [0.9412 0.9412 0.9412];
        app.flip_y.Position = [15 50 50 22];

        app.flip_x = uicheckbox(p);
        app.flip_x.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_x.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.flip_x.Text = 'flip_x';
        app.flip_x.FontColor = [0.9412 0.9412 0.9412];
        app.flip_x.Position = [15 33 50 22];

        app.square = uicheckbox(p);
        app.square.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.square.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.square.Text = 'square';
        app.square.FontColor = [0.9412 0.9412 0.9412];
        app.square.Position = [15 16 59 22];

        app.AutofocusButton = uibutton(p, 'push');
        app.AutofocusButton.ButtonPushedFcn = createCallbackFcn(app, @AutofocusButtonPushed2, true);
        app.AutofocusButton.BackgroundColor = [0.502 0.502 0.502];
        app.AutofocusButton.FontColor = [1 1 1];
        app.AutofocusButton.Position = [207 259 31 25];
        app.AutofocusButton.Text = '🤖';

        app.PaddNLabel = uilabel(p);
        app.PaddNLabel.HorizontalAlignment = 'right';
        app.PaddNLabel.FontColor = [0.9412 0.9412 0.9412];
        app.PaddNLabel.Position = [200 307 45 22];
        app.PaddNLabel.Text = 'Padd N';

        app.Padding_num = uieditfield(p, 'numeric');
        app.Padding_num.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.Padding_num.FontColor = [1 1 1];
        app.Padding_num.BackgroundColor = [0.149 0.149 0.149];
        app.Padding_num.Tooltip = {'Distance of spatial reconstruction using the preceding calculation scheme in (m) '};
        app.Padding_num.Position = [263 307 37 22];
    end

    % -----------------------------------------------------------------------
    function createImageViewsAndMenus(app)
        app.ImageRight = uiimage(app.RootGrid);
        app.ImageRight.ScaleMethod = 'stretch';
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
