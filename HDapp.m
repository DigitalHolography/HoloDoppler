classdef HDapp < matlab.apps.AppBase

% Properties that correspond to app components
properties (Access = public)
    HoloDopplerUIFigure matlab.ui.Figure
    GridLayout4 matlab.ui.container.GridLayout
    PanelPlot matlab.ui.container.Panel
    ImageLeft matlab.ui.control.Image
    ImageRight matlab.ui.control.Image
    CurrentFilePanel matlab.ui.container.Panel
    GridLayout matlab.ui.container.GridLayout
    GridLayout2 matlab.ui.container.GridLayout
    GridLayout3 matlab.ui.container.GridLayout
    RenderingparametersPanel matlab.ui.container.Panel
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
    AberrationcompensationPanel matlab.ui.container.Panel
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
    PreviewLabel matlab.ui.control.Label
    masknumiterEditField matlab.ui.control.NumericEditField
    masknumiterEditFieldLabel matlab.ui.control.Label
    maxconstraintEditField matlab.ui.control.NumericEditField
    maxconstraintEditFieldLabel matlab.ui.control.Label
    zernikestolEditField matlab.ui.control.NumericEditField
    toleranceLabel matlab.ui.control.Label
    optimizationzernikeranksEditField matlab.ui.control.NumericEditField
    zernikeranksEditField_2Label matlab.ui.control.Label
    IterativeoptimizationCheckBox matlab.ui.control.CheckBox
    subaperturemarginEditField matlab.ui.control.NumericEditField
    subaperturemarginEditFieldLabel matlab.ui.control.Label
    shackhartmannzernikeranksEditField matlab.ui.control.NumericEditField
    zernikeranksEditFieldLabel matlab.ui.control.Label
    ShackHartmannCheckBox matlab.ui.control.CheckBox
    Label_2 matlab.ui.control.Label
    UIAxes_aberrationPreview matlab.ui.control.UIAxes
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
    FileselectionPanel matlab.ui.container.Panel
    LoadAllCheckBox matlab.ui.control.CheckBox
    AdvancedButton matlab.ui.control.Button
    ppxy_label_2 matlab.ui.control.Label
    Ny matlab.ui.control.NumericEditField
    Nx matlab.ui.control.NumericEditField
    RefreshAppButton matlab.ui.control.Button
    num_frames matlab.ui.control.Label
    file_loaded_lamp matlab.ui.control.Lamp
    positioninfileSlider matlab.ui.control.Slider
    positioninfileSliderLabel matlab.ui.control.Label
    frame_position matlab.ui.control.NumericEditField
    ppx matlab.ui.control.NumericEditField
    ppxy_label matlab.ui.control.Label
    ppy matlab.ui.control.NumericEditField
    setUpDropDown matlab.ui.control.DropDown
    Label matlab.ui.control.Label
    parfor_arg matlab.ui.control.Spinner
    numworkersSpinnerLabel matlab.ui.control.Label
    NotesTextArea matlab.ui.control.TextArea
    NotesTextAreaLabel matlab.ui.control.Label
    fs matlab.ui.control.NumericEditField
    samplingfrequencyLabel matlab.ui.control.Label
    ParallelismDropDown matlab.ui.control.DropDown
    lambda matlab.ui.control.NumericEditField
    wavelengthEditFieldLabel matlab.ui.control.Label
    LoadfileButton matlab.ui.control.Button
    BatchselectionparametersandVideoRenderingPanel matlab.ui.container.Panel
    applyshackhartmannfromref matlab.ui.control.CheckBox
    SaveconfigButton matlab.ui.control.Button
    PlayButton matlab.ui.control.Button
    ShowHistogramButton matlab.ui.control.Button
    VideoRenderingLamp matlab.ui.control.Lamp
    SaveVideoButton matlab.ui.control.Button
    batch_size matlab.ui.control.NumericEditField
    batchsizeLabel matlab.ui.control.Label
    Image_typesListBox matlab.ui.control.ListBox
    DxEditFieldLabel_2 matlab.ui.control.Label
    registration_disc_ratio matlab.ui.control.NumericEditField
    batch_size_registration matlab.ui.control.NumericEditField
    refbatchsizeEditFieldLabel matlab.ui.control.Label
    batch_stride matlab.ui.control.NumericEditField
    batchstrideEditFieldLabel matlab.ui.control.Label
    image_registration matlab.ui.control.CheckBox
    LoadconfigButton matlab.ui.control.Button
    showrefCheckBox matlab.ui.control.CheckBox
    iterativeregistrationCheckBox matlab.ui.control.CheckBox
    VideoRenderingButton matlab.ui.control.Button
    FoldermanagementButton matlab.ui.control.Button
    temporalfilterEditField matlab.ui.control.NumericEditField
    temporalfilterCheckBox matlab.ui.control.CheckBox
    phaseregistrationCheckBox matlab.ui.control.CheckBox
    rephasingCheckBox matlab.ui.control.CheckBox
    RightClickImageContextMenu matlab.ui.container.ContextMenu
    NextMenu matlab.ui.container.Menu
    ViewAllMenu matlab.ui.container.Menu
end

properties (Access = public)
    file_loaded
    HD %HoloDopplerClass
    drawer_list = {}
end

properties (Access = private)
    DialogApp % Dialog box app
    poolobj
end

methods (Access = private)

end

% Callbacks that handle component events
methods (Access = private)

    % Code that executes after component creation
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

        % add subfolders to path

        addpath("Tools\"); % for the splashscreen
        displaySplashScreen();
        app.HD = HoloDopplerClass();
    end

    % Button pushed function: LoadfileButton
    function LoadfileButtonPushed(app, ~)
        % open file and manage file extension
        f = figure('Position', [-100 -100 0 0]); %create a dummy figure so that uigetfile doesn't minimize our GUI

        if (isempty(app.HD.file))
            [fname, fpath] = uigetfile('*.raw;*.cine;*.holo');
        else
            [fname, fpath] = uigetfile(strcat(app.HD.file.path, "*.raw;*.cine;*.holo"));
        end

        delete(f); %delete the dummy figure

        if fname == 0
            return
        end

        try
            LoadAll = app.LoadAllCheckBox.Value;
            app.HD.LoadFile(fullfile(fpath, fname), LoadAll = LoadAll);
            classtogui(app.HD, app);
            app.RenderPreviewButtonPushed();
            app.file_loaded = 1; app.file_loaded_lamp.Color = [0 1 0]; %
        catch ME
            % Display error message and line number
            fprintf('Error: %s\n', ME.message);
            fprintf('Occurred in: %s at line %d\n', ME.stack(1).name, ME.stack(1).line);
            app.file_loaded_lamp.Color = [0.8 0.1 0.1];
            drawnow
        end

        if ~isempty(app.HD.file)
            app.CurrentFilePanel.Title = ['Current File : ' app.HD.file.path];
        end

        app.refreshClass();

    end

    % Button pushed function: VideoRenderingButton
    function VideoRenderingButtonPushed(app, ~)
        app.VideoRenderingLamp.Color = [0.75 0.15 0.1]; drawnow; % red in process

        try
            app.HD.VideoRendering();
            app.VideoRenderingLamp.Color = [0 1 0]; % green success
        catch ME
            % Display error message and line number
            fprintf('Error: %s\n', ME.message);
            fprintf('Occurred in: %s at line %d\n', ME.stack(1).name, ME.stack(1).line);

            for stackIdx = 1:size(ME.stack, 1)
                fprintf('%s : %s, line : %d \n', ME.stack(stackIdx).file, ME.stack(stackIdx).name, ME.stack(stackIdx).line);
            end

            app.VideoRenderingLamp.Color = [0.8 0.1 0.1]; % error happened
        end

    end

    % Close request function: HoloDopplerUIFigure
    function HoloDopplerUIFigureCloseRequest(app, ~)
        diary off;
        delete(app.HoloDopplerUIFigure);
    end

    % Button pushed function: LoadconfigButton
    function LoadconfigButtonPushed(app, ~)
        [selected_file, path] = uigetfile('*.json', 'Select File');

        if (selected_file)
            [~, ~, ext] = fileparts(selected_file);

            if ismember(ext, {'.json'})
                app.HD.loadParams(fullfile(path, selected_file));

                try
                    classtogui(app.HD, app);
                catch
                end

            else
                fprintf("Couldn't load config");
            end

        end

    end

    % Window key press function: HoloDopplerUIFigure
    function HoloDopplerUIFigureWindowKeyPress(app, event)

        switch event.Key
            case 'return'
                app.RenderPreviewButtonPushed();
            case 'rightarrow'
                app.NextMenuSelected();
        end

    end

    % Button pushed function: FoldermanagementButton
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

        uicontrol('Parent', d, ...
            'Position', [20, 20, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Select file', ...
            'Callback', @select);

        uicontrol('Parent', d, ...
            'Position', [20, 50, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Select Current', ...
            'Callback', @select_current);

        uicontrol('Parent', d, ...
            'Position', [140, 50, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Select Current Folder', ...
            'Callback', @select_current_folder);

        uicontrol('Parent', d, ...
            'Position', [140, 20, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Select folder', ...
            'Callback', @select_all);

        uicontrol('Parent', d, ...
            'Position', [260, 20, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Clear list', ...
            'Callback', @clear_drawer);

        uicontrol('Parent', d, ...
            'Position', [500, 20, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Render', ...
            'Callback', @render);

        uicontrol('Parent', d, ...
            'Position', [380, 20, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Save configs', ...
            'Callback', @save_config);

        uicontrol('Parent', d, ...
            'Position', [380, 50, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Delete all configs', ...
            'Callback', @del_configs);

        uicontrol('Parent', d, ...
            'Position', [620, 50, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Load from txt', ...
            'Callback', @load_txt);

        uicontrol('Parent', d, ...
            'Position', [620, 20, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'ForegroundColor', [0.9 0.9 0.9], ...
            'FontWeight', 'bold', ...
            'String', 'Save to txt', ...
            'Callback', @save_txt);

        keep_z_distance = uicontrol('Parent', d, ...
            'Style', 'checkbox', ...
            'Position', [500, 50, 100, 25], ...
            'FontName', 'Helvetica', ...
            'BackgroundColor', [0.5, 0.5, 0.5], ...
            'FontWeight', 'bold', ...
            'String', 'Keep z distance', ...
            'Value', 0); % Default unchecked

        %uiwait(d);

        function select(~, ~)

            if ~isempty(app.HD.drawer_list)
                last_file = app.HD.drawer_list{end};
                [selected_file, path] = uigetfile(last_file, 'Select File');
            else
                [selected_file, path] = uigetfile('Select File');
            end

            if (selected_file)
                [~, ~, ext] = fileparts(selected_file);

                if ismember(ext, {'.cine', '.holo'})
                    app.HD.drawer_list{end + 1} = fullfile(path, selected_file);
                else
                    fprintf("File should be of extension .cine or .holo")
                end

            end

            txt.String = app.HD.drawer_list;
            d.Position(4) = 100 + length(app.HD.drawer_list) * 14;
            txt.Position(4) = length(app.HD.drawer_list) * 14;
        end

        function select_current(~, ~)

            if isempty(app.HD.file)
                return
            end

            selected_file = app.HD.file.path;

            [~, ~, ext] = fileparts(selected_file);

            if ismember(ext, {'.cine', '.holo'})
                app.HD.drawer_list{end + 1} = selected_file;
            else
                fprintf("File should be of extension .cine or .holo")
            end

            txt.String = app.HD.drawer_list;
            d.Position(4) = 100 + length(app.HD.drawer_list) * 14;
            txt.Position(4) = length(app.HD.drawer_list) * 14;

        end

        function select_current_folder(~, ~)

            if isempty(app.HD.file)
                return
            end

            selected_folder = app.HD.file.dir;

            if selected_folder
                % List of files and folders within the selected directory
                tmp_dir = dir(selected_folder);
                % Loop through the files and folders in the selected directory
                for i = 1:numel(tmp_dir)
                    % Skip directories (.) and (..) and process files only
                    if ~tmp_dir(i).isdir
                        [~, ~, ext] = fileparts(tmp_dir(i).name); % Get the file extension
                        % Check if the file has a .cine or .holo extension
                        if ismember(ext, {'.cine', '.holo'})
                            % Add file to the drawer list
                            app.HD.drawer_list{end + 1} = fullfile(selected_folder, tmp_dir(i).name);
                        end

                    end

                end

                % Update the display
                txt.String = app.HD.drawer_list;
                d.Position(4) = 100 + length(app.HD.drawer_list) * 14;
                txt.Position(4) = length(app.HD.drawer_list) * 14;
            end

        end

        function select_all(~, ~)

            if ~isempty(app.drawer_list)
                [last_folder, ~, ~] = fileparts(app.drawer_list{end});
            else
                last_folder = [];
            end

            selected_folder = uigetdir(last_folder);

            if selected_folder
                % List of files and folders within the selected directory
                tmp_dir = dir(selected_folder);
                % Loop through the files and folders in the selected directory
                for i = 1:numel(tmp_dir)
                    % Skip directories (.) and (..) and process files only
                    if ~tmp_dir(i).isdir
                        [~, ~, ext] = fileparts(tmp_dir(i).name); % Get the file extension
                        % Check if the file has a .cine or .holo extension
                        if ismember(ext, {'.cine', '.holo'})
                            % Add file to the drawer list
                            app.HD.drawer_list{end + 1} = fullfile(selected_folder, tmp_dir(i).name);
                        end

                    end

                end

                % Update the display
                txt.String = app.HD.drawer_list;
                d.Position(4) = 100 + length(app.HD.drawer_list) * 14;
                txt.Position(4) = length(app.HD.drawer_list) * 14;
            end

        end

        function clear_drawer(~, ~)
            app.HD.drawer_list = {};
            txt.String = app.HD.drawer_list;
            d.Position(4) = 100 + length(app.HD.drawer_list) * 14;
            txt.Position(4) = length(app.HD.drawer_list) * 14;
        end

        function load_txt(~, ~)

            [selected_file, path] = uigetfile('*.txt', 'Select File');
            lines = readlines(fullfile(path, selected_file));

            for i = 1:numel(lines)

                if ~isempty(lines(i))

                    try
                        [~, ~, ext] = fileparts(lines(i)); % Get the file extension
                        % Check if the file has a .cine or .holo extension
                        if ismember(ext, {'.cine', '.holo'})
                            % Add file to the drawer list
                            app.HD.drawer_list{end + 1} = lines(i);
                        end

                    catch e

                        disp(e)
                    end

                end

                % Update the display
                txt.String = app.HD.drawer_list;
                d.Position(4) = 100 + length(app.HD.drawer_list) * 14;
                txt.Position(4) = length(app.HD.drawer_list) * 14;
            end

        end

        function save_txt(~, ~)

            [selected_file, path] = uigetfile('*.txt', 'Select File');
            writelines(app.HD.drawer_list, fullfile(path, selected_file));

        end

        function save_config(~, ~)

            for i = 1:length(app.HD.drawer_list)
                app.HD.saveParams(app.HD.drawer_list{i}, keep_z_distance.Value);
            end

        end

        function render(~, ~)
            L = length(app.HD.drawer_list);
            file_list = cell(L, 1);

            for i = 1:length(app.HD.drawer_list) % Circles through the files added by the user
                % Get config files
                config_list = get_config_files(app.HD.drawer_list{i});

                if (~isempty(config_list))
                    file_list{i} = {app.HD.drawer_list{i}, config_list};
                end

            end

            for i = 1:length(file_list)

                if (~isempty(file_list{i}{2}))

                    for j = 1:length(file_list{i}{2})
                        app.HD.LoadFile(file_list{i}{1}, params = file_list{i}{2}{j});
                        app.HD.VideoRendering();
                    end

                end

            end

            %close(d);
        end

        function del_configs(~, ~)
            L = length(app.HD.drawer_list);
            file_list = cell(L, 1);

            for i = 1:length(app.HD.drawer_list) % Circles through the files added by the user
                % Get config files
                [~, path_list] = get_config_files(app.HD.drawer_list{i});

                if (~isempty(path_list))
                    file_list{i} = {app.HD.drawer_list{i}, path_list};
                end

            end

            for i = 1:length(file_list)

                if (~isempty(file_list{i}{2}))

                    for j = 1:length(file_list{i}{2})
                        delete(file_list{i}{2}{j});
                    end

                end

            end

        end

    end

    % Callback function: Image_typesListBox, ShackHartmannCheckBox,
    % ...and 40 other components
    function refreshClass(app, ~)
        guitoclass(app.HD, app);

        switch app.time_transform.Value
            case 'FFT'
                app.time_range1.Enable = true; app.time_range2.Enable = true; app.frequency_rangeLabel.Enable = true;
                app.index_range1.Enable = false; app.index_range2.Enable = false; app.index_rangeLabel.Enable = false;
            case 'PCA'
                app.time_range1.Enable = false; app.time_range2.Enable = false; app.frequency_rangeLabel.Enable = false;
                app.index_range1.Enable = true; app.index_range2.Enable = true; app.index_rangeLabel.Enable = true;
            case 'ICA'
                app.time_range1.Enable = false; app.time_range2.Enable = false; app.frequency_rangeLabel.Enable = false;
                app.index_range1.Enable = true; app.index_range2.Enable = true; app.index_rangeLabel.Enable = true;
            case 'autocorrelation'
                app.time_range1.Enable = true; app.time_range2.Enable = true; app.frequency_rangeLabel.Enable = true;
                app.index_range1.Enable = false; app.index_range2.Enable = false; app.index_rangeLabel.Enable = false;
            case 'intercorrelation'
                app.time_range1.Enable = true; app.time_range2.Enable = true; app.frequency_rangeLabel.Enable = true;
                app.index_range1.Enable = false; app.index_range2.Enable = false; app.index_rangeLabel.Enable = false;
        end

        if app.svdx_filter.Value
            app.svdx_threshold.Enable = true; app.NsubxLabel.Enable = true; app.svdx_Nsub.Enable = true;
        else
            app.svdx_threshold.Enable = false; app.NsubxLabel.Enable = false; app.svdx_Nsub.Enable = false;
        end

        if app.svdx_t_filter.Value
            app.svdx_t_threshold.Enable = true; app.NsubxtLabel.Enable = true; app.svdx_t_Nsub.Enable = true;
        else
            app.svdx_t_threshold.Enable = false; app.NsubxtLabel.Enable = false; app.svdx_t_Nsub.Enable = false;
        end

    end

    % Button pushed function: RenderPreviewButton
    function RenderPreviewButtonPushed(app, ~)
        app.RenderPreviewLamp.Color = [0.75 0.15 0.1]; drawnow; % red in process

        try
            Images = app.HD.PreviewRendering();
            app.RenderPreviewLamp.Color = [0 1 0]; % green success
        catch ME
            Images = [];
            % Display error message and line number
            fprintf('Error: %s\n', ME.message);
            fprintf('Occurred in: %s at line %d\n', ME.stack(1).name, ME.stack(1).line);

            for stackIdx = 1:size(ME.stack, 1)
                fprintf('%s : %s, line : %d \n', ME.stack(stackIdx).file, ME.stack(stackIdx).name, ME.stack(stackIdx).line);
            end

            app.RenderPreviewLamp.Color = [0.8 0.1 0.1]; % error happened
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

    % Menu selected function: NextMenu
    function NextMenuSelected(app, ~)
        imgs = app.HD.view.getImages(app.HD.params.image_types);

        if ~isempty(imgs)
            num = randi(numel(imgs), 1);

            if isnumeric(imgs{num})
                image = imgs{num};

                if ~ismember(app.HD.params.image_types{num}, {'spectrogram', 'autocorrelogram', 'broadening', 'f_RMS'}) && size(image, 1) ~= size(image, 2) % do not resize the graphs
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

    % Menu selected function: ViewAllMenu
    function ViewAllMenuSelected(app, ~)
        app.HD.showPreviewImages();
    end

    % Button pushed function: SaveVideoButton
    function SaveVideoButtonPushed(app, ~)
        app.HD.SaveVideo();
    end

    % Button pushed function: SavePreviewButton
    function SavePreviewButtonPushed(app, ~)
        app.HD.savePreview();
    end

    % Button pushed function: svd_threshold_reset_button
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

    % Button pushed function: ShowHistogramButton
    function ShowHistogramButtonPushed(app, ~)
        app.HD.view.showFramesHistogram();
    end

    % Value changed function: time_range2
    function time_range2ValueChanged(app, ~)

        if strcmp(app.time_transform, 'FFT') && app.time_range2.Value > app.fs.Value / 2
            app.time_range2.Value = app.fs.Value / 2;
        end

        app.refreshClass();
    end

    % Button pushed function: PlayButton
    function PlayButtonPushed(app, ~)

        try
            app.HD.showVideo();
        catch e
            fprintf("Couldn't play video (try to video render first) : %s", e.message);
        end

    end

    % Button pushed function: RefreshAppButton
    function RefreshAppButtonPushed(app, ~)
        classtogui(app.HD, app);

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

    % Button pushed function: AdvancedButton
    function AdvancedButtonPushed(app, ~)
        AdvancedPanel(app);
    end

    % Value changed function: registration_disc_ratio
    function registration_disc_ratioValueChanged(app, ~)
        app.refreshClass();
        show_ref_disc(app, app.image_registration.Value);
    end

    % Button pushed function: SaveconfigButton
    function SaveconfigButtonPushed(app, ~)
        app.HD.saveParams();
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
        app.HoloDopplerUIFigure.Icon = fullfile(pathToMLAPP, 'holoDopplerLogo.png');
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
        app.FileselectionPanel.Tooltip = {''};
        app.FileselectionPanel.ForegroundColor = [0.8 0.8 0.8];
        app.FileselectionPanel.TitlePosition = 'centertop';
        app.FileselectionPanel.Title = 'File selection';
        app.FileselectionPanel.BackgroundColor = [0.2 0.2 0.2];
        app.FileselectionPanel.Layout.Row = [1 2];
        app.FileselectionPanel.Layout.Column = 1;

        % Create BatchselectionparametersandVideoRenderingPanel
        app.BatchselectionparametersandVideoRenderingPanel = uipanel(app.FileselectionPanel);
        app.BatchselectionparametersandVideoRenderingPanel.ForegroundColor = [0.902 0.902 0.902];
        app.BatchselectionparametersandVideoRenderingPanel.Title = 'Batch selection parameters and Video Rendering';
        app.BatchselectionparametersandVideoRenderingPanel.BackgroundColor = [0.2 0.2 0.2];
        app.BatchselectionparametersandVideoRenderingPanel.Position = [10 237 244 433];

        % Create rephasingCheckBox
        app.rephasingCheckBox = uicheckbox(app.BatchselectionparametersandVideoRenderingPanel);
        app.rephasingCheckBox.ValueChangedFcn = createCallbackFcn(app, @rephasingCheckBoxValueChanged, true);
        app.rephasingCheckBox.Visible = 'off';
        app.rephasingCheckBox.Text = 'rephasing';
        app.rephasingCheckBox.FontColor = [0.902 0.902 0.902];
        app.rephasingCheckBox.Position = [38 106 75 22];
        app.rephasingCheckBox.Value = true;

        % Create phaseregistrationCheckBox
        app.phaseregistrationCheckBox = uicheckbox(app.BatchselectionparametersandVideoRenderingPanel);
        app.phaseregistrationCheckBox.Visible = 'off';
        app.phaseregistrationCheckBox.Tooltip = {'Activates video registration. Check this if the video is too shaky.'};
        app.phaseregistrationCheckBox.Text = 'phase registration';
        app.phaseregistrationCheckBox.FontColor = [0.902 0.902 0.902];
        app.phaseregistrationCheckBox.Position = [119 106 117 22];

        % Create temporalfilterCheckBox
        app.temporalfilterCheckBox = uicheckbox(app.BatchselectionparametersandVideoRenderingPanel);
        app.temporalfilterCheckBox.Visible = 'off';
        app.temporalfilterCheckBox.Text = 'temporal filter';
        app.temporalfilterCheckBox.FontColor = [0.902 0.902 0.902];
        app.temporalfilterCheckBox.Position = [38 45 95 22];

        % Create temporalfilterEditField
        app.temporalfilterEditField = uieditfield(app.BatchselectionparametersandVideoRenderingPanel, 'numeric');
        app.temporalfilterEditField.Limits = [1 Inf];
        app.temporalfilterEditField.FontColor = [0.8 0.8 0.8];
        app.temporalfilterEditField.BackgroundColor = [0.149 0.149 0.149];
        app.temporalfilterEditField.Visible = 'off';
        app.temporalfilterEditField.Tooltip = {'Laser wavelength in nanometers'};
        app.temporalfilterEditField.Position = [141 44 54 22];
        app.temporalfilterEditField.Value = 2;

        % Create FoldermanagementButton
        app.FoldermanagementButton = uibutton(app.BatchselectionparametersandVideoRenderingPanel, 'push');
        app.FoldermanagementButton.ButtonPushedFcn = createCallbackFcn(app, @FoldermanagementButtonPushed, true);
        app.FoldermanagementButton.BackgroundColor = [0.502 0.502 0.502];
        app.FoldermanagementButton.FontColor = [0.902 0.902 0.902];
        app.FoldermanagementButton.Tooltip = {'Open a window to render all files from different folders with their config files'};
        app.FoldermanagementButton.Position = [7 171 123 23];
        app.FoldermanagementButton.Text = 'Folder management';

        % Create VideoRenderingButton
        app.VideoRenderingButton = uibutton(app.BatchselectionparametersandVideoRenderingPanel, 'push');
        app.VideoRenderingButton.ButtonPushedFcn = createCallbackFcn(app, @VideoRenderingButtonPushed, true);
        app.VideoRenderingButton.BackgroundColor = [0.502 0.502 0.502];
        app.VideoRenderingButton.FontColor = [0.902 0.902 0.902];
        app.VideoRenderingButton.Tooltip = {'Render ''batch_size'' frame batchs spaced by ''batch_stride'' and output a video of different image types'};
        app.VideoRenderingButton.Position = [133 171 104 23];
        app.VideoRenderingButton.Text = 'Video Rendering';

        % Create iterativeregistrationCheckBox
        app.iterativeregistrationCheckBox = uicheckbox(app.BatchselectionparametersandVideoRenderingPanel);
        app.iterativeregistrationCheckBox.Visible = 'off';
        app.iterativeregistrationCheckBox.Tooltip = {'''Activates video registration. Check this if the video is too shaky.'''};
        app.iterativeregistrationCheckBox.Text = 'iterative registration';
        app.iterativeregistrationCheckBox.FontColor = [0.902 0.902 0.902];
        app.iterativeregistrationCheckBox.Position = [38 66 131 22];

        % Create showrefCheckBox
        app.showrefCheckBox = uicheckbox(app.BatchselectionparametersandVideoRenderingPanel);
        app.showrefCheckBox.Visible = 'off';
        app.showrefCheckBox.Text = 'show ref';
        app.showrefCheckBox.FontColor = [0.902 0.902 0.902];
        app.showrefCheckBox.Position = [38 25 67 22];

        % Create LoadconfigButton
        app.LoadconfigButton = uibutton(app.BatchselectionparametersandVideoRenderingPanel, 'push');
        app.LoadconfigButton.ButtonPushedFcn = createCallbackFcn(app, @LoadconfigButtonPushed, true);
        app.LoadconfigButton.BackgroundColor = [0.502 0.502 0.502];
        app.LoadconfigButton.FontColor = [0.902 0.902 0.902];
        app.LoadconfigButton.Tooltip = {'Save a configuration for the video rendering of a file'};
        app.LoadconfigButton.Position = [7 198 100 23];
        app.LoadconfigButton.Text = 'Load config';

        % Create image_registration
        app.image_registration = uicheckbox(app.BatchselectionparametersandVideoRenderingPanel);
        app.image_registration.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.image_registration.Tooltip = {'Activate frame to frame translation registration of images'};
        app.image_registration.Text = 'image registration';
        app.image_registration.FontColor = [0.902 0.902 0.902];
        app.image_registration.Position = [35 4 117 22];

        % Create batchstrideEditFieldLabel
        app.batchstrideEditFieldLabel = uilabel(app.BatchselectionparametersandVideoRenderingPanel);
        app.batchstrideEditFieldLabel.HorizontalAlignment = 'center';
        app.batchstrideEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.batchstrideEditFieldLabel.Position = [7 121 84 22];
        app.batchstrideEditFieldLabel.Text = 'batch stride';

        % Create batch_stride
        app.batch_stride = uieditfield(app.BatchselectionparametersandVideoRenderingPanel, 'numeric');
        app.batch_stride.Limits = [0 Inf];
        app.batch_stride.ValueDisplayFormat = '%.0f';
        app.batch_stride.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.batch_stride.FontColor = [0.8 0.8 0.8];
        app.batch_stride.BackgroundColor = [0.149 0.149 0.149];
        app.batch_stride.Tooltip = {'Number of interferograms to skip between two images'};
        app.batch_stride.Position = [90 121 100 22];

        % Create refbatchsizeEditFieldLabel
        app.refbatchsizeEditFieldLabel = uilabel(app.BatchselectionparametersandVideoRenderingPanel);
        app.refbatchsizeEditFieldLabel.HorizontalAlignment = 'center';
        app.refbatchsizeEditFieldLabel.FontColor = [0.8 0.8 0.8];
        app.refbatchsizeEditFieldLabel.Position = [7 99 80 22];
        app.refbatchsizeEditFieldLabel.Text = 'reg batch size';

        % Create batch_size_registration
        app.batch_size_registration = uieditfield(app.BatchselectionparametersandVideoRenderingPanel, 'numeric');
        app.batch_size_registration.Limits = [0 Inf];
        app.batch_size_registration.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.batch_size_registration.FontColor = [0.8 0.8 0.8];
        app.batch_size_registration.BackgroundColor = [0.149 0.149 0.149];
        app.batch_size_registration.Tooltip = {'Number of interferograms usedcompute the image used as reference in registration'};
        app.batch_size_registration.Position = [90 99 100 22];

        % Create registration_disc_ratio
        app.registration_disc_ratio = uieditfield(app.BatchselectionparametersandVideoRenderingPanel, 'numeric');
        app.registration_disc_ratio.Limits = [0 1000];
        app.registration_disc_ratio.ValueChangedFcn = createCallbackFcn(app, @registration_disc_ratioValueChanged, true);
        app.registration_disc_ratio.FontColor = [0.8 0.8 0.8];
        app.registration_disc_ratio.BackgroundColor = [0.149 0.149 0.149];
        app.registration_disc_ratio.Tooltip = {'Size of a disk centered on the images used to compute the registration shifts (0 is empty and 1 is a disc of the maximum dimension).'};
        app.registration_disc_ratio.Position = [188 4 54 22];

        % Create DxEditFieldLabel_2
        app.DxEditFieldLabel_2 = uilabel(app.BatchselectionparametersandVideoRenderingPanel);
        app.DxEditFieldLabel_2.HorizontalAlignment = 'center';
        app.DxEditFieldLabel_2.FontColor = [0.8 0.8 0.8];
        app.DxEditFieldLabel_2.Position = [157 4 26 22];
        app.DxEditFieldLabel_2.Text = 'disk';

        % Create Image_typesListBox
        app.Image_typesListBox = uilistbox(app.BatchselectionparametersandVideoRenderingPanel);
        app.Image_typesListBox.Items = {};
        app.Image_typesListBox.Multiselect = 'on';
        app.Image_typesListBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.Image_typesListBox.Tooltip = {'Image types output giving extracting different informations from a batch of frames'};
        app.Image_typesListBox.FontColor = [1 1 1];
        app.Image_typesListBox.BackgroundColor = [0.149 0.149 0.149];
        app.Image_typesListBox.Position = [16 231 211 178];
        app.Image_typesListBox.Value = {};

        % Create batchsizeLabel
        app.batchsizeLabel = uilabel(app.BatchselectionparametersandVideoRenderingPanel);
        app.batchsizeLabel.HorizontalAlignment = 'center';
        app.batchsizeLabel.FontColor = [0.8 0.8 0.8];
        app.batchsizeLabel.Position = [7 143 84 22];
        app.batchsizeLabel.Text = 'batch size';

        % Create batch_size
        app.batch_size = uieditfield(app.BatchselectionparametersandVideoRenderingPanel, 'numeric');
        app.batch_size.Limits = [0 Inf];
        app.batch_size.ValueDisplayFormat = '%.0f';
        app.batch_size.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.batch_size.FontColor = [0.8 0.8 0.8];
        app.batch_size.BackgroundColor = [0.149 0.149 0.149];
        app.batch_size.Tooltip = {'Number of interferograms used to compute the image'};
        app.batch_size.Position = [90 143 100 22];

        % Create SaveVideoButton
        app.SaveVideoButton = uibutton(app.BatchselectionparametersandVideoRenderingPanel, 'push');
        app.SaveVideoButton.ButtonPushedFcn = createCallbackFcn(app, @SaveVideoButtonPushed, true);
        app.SaveVideoButton.BackgroundColor = [0.502 0.502 0.502];
        app.SaveVideoButton.FontColor = [0.902 0.902 0.902];
        app.SaveVideoButton.Visible = 'off';
        app.SaveVideoButton.Tooltip = {'Render ''batch_size'' frame batchs spaced by ''batch_stride'' and output a video of different image types'};
        app.SaveVideoButton.Position = [138 70 100 23];
        app.SaveVideoButton.Text = 'Save Video';

        % Create VideoRenderingLamp
        app.VideoRenderingLamp = uilamp(app.BatchselectionparametersandVideoRenderingPanel);
        app.VideoRenderingLamp.Position = [226 153 12 12];

        % Create ShowHistogramButton
        app.ShowHistogramButton = uibutton(app.BatchselectionparametersandVideoRenderingPanel, 'push');
        app.ShowHistogramButton.ButtonPushedFcn = createCallbackFcn(app, @ShowHistogramButtonPushed, true);
        app.ShowHistogramButton.BackgroundColor = [0.502 0.502 0.502];
        app.ShowHistogramButton.FontColor = [0.902 0.902 0.902];
        app.ShowHistogramButton.Tooltip = {'Show the full frame batch histogram'};
        app.ShowHistogramButton.Position = [9 70 70 23];
        app.ShowHistogramButton.Text = 'Histogram';

        % Create PlayButton
        app.PlayButton = uibutton(app.BatchselectionparametersandVideoRenderingPanel, 'push');
        app.PlayButton.ButtonPushedFcn = createCallbackFcn(app, @PlayButtonPushed, true);
        app.PlayButton.BackgroundColor = [0.502 0.502 0.502];
        app.PlayButton.FontColor = [0.902 0.902 0.902];
        app.PlayButton.Tooltip = {'Play the video'};
        app.PlayButton.Position = [214 121 25 23];
        app.PlayButton.Text = 'l>';

        % Create SaveconfigButton
        app.SaveconfigButton = uibutton(app.BatchselectionparametersandVideoRenderingPanel, 'push');
        app.SaveconfigButton.ButtonPushedFcn = createCallbackFcn(app, @SaveconfigButtonPushed, true);
        app.SaveconfigButton.BackgroundColor = [0.502 0.502 0.502];
        app.SaveconfigButton.FontColor = [0.902 0.902 0.902];
        app.SaveconfigButton.Tooltip = {'Save a configuration for the video rendering of a file'};
        app.SaveconfigButton.Position = [112 197 100 23];
        app.SaveconfigButton.Text = 'Save config';

        % Create applyshackhartmannfromref
        app.applyshackhartmannfromref = uicheckbox(app.BatchselectionparametersandVideoRenderingPanel);
        app.applyshackhartmannfromref.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.applyshackhartmannfromref.Tooltip = {'Activate frame to frame translation registration of images'};
        app.applyshackhartmannfromref.Text = 'refocus from ref (numeric shack hartmann)';
        app.applyshackhartmannfromref.FontColor = [0.902 0.902 0.902];
        app.applyshackhartmannfromref.Position = [35 25 251 22];

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
        app.wavelengthEditFieldLabel.Tooltip = {'Laser''s wavelength for light propagation calculations in (m)'};
        app.wavelengthEditFieldLabel.Position = [40 771 84 22];
        app.wavelengthEditFieldLabel.Text = 'wavelength';

        % Create lambda
        app.lambda = uieditfield(app.FileselectionPanel, 'numeric');
        app.lambda.Limits = [0 Inf];
        app.lambda.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.lambda.FontColor = [0.8 0.8 0.8];
        app.lambda.BackgroundColor = [0.149 0.149 0.149];
        app.lambda.Tooltip = {'Laser wavelength in nanometers'};
        app.lambda.Position = [123 772 100 22];

        % Create ParallelismDropDown
        app.ParallelismDropDown = uidropdown(app.FileselectionPanel);
        app.ParallelismDropDown.Items = {'CPU multithread', 'LightGPU', 'GPU parallelization', 'CPU singlethread', 'CPU/GPU rendering/optim'};
        app.ParallelismDropDown.Enable = 'off';
        app.ParallelismDropDown.Visible = 'off';
        app.ParallelismDropDown.FontColor = [0.9412 0.9412 0.9412];
        app.ParallelismDropDown.BackgroundColor = [0.502 0.502 0.502];
        app.ParallelismDropDown.Position = [29 712 124 22];
        app.ParallelismDropDown.Value = 'CPU multithread';

        % Create samplingfrequencyLabel
        app.samplingfrequencyLabel = uilabel(app.FileselectionPanel);
        app.samplingfrequencyLabel.HorizontalAlignment = 'right';
        app.samplingfrequencyLabel.FontColor = [0.8 0.8 0.8];
        app.samplingfrequencyLabel.Tooltip = {'Sampling frequency in (kHz)'};
        app.samplingfrequencyLabel.Position = [6 799 109 22];
        app.samplingfrequencyLabel.Text = 'sampling frequency';

        % Create fs
        app.fs = uieditfield(app.FileselectionPanel, 'numeric');
        app.fs.Limits = [0 Inf];
        app.fs.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.fs.FontColor = [0.8 0.8 0.8];
        app.fs.BackgroundColor = [0.149 0.149 0.149];
        app.fs.Tooltip = {'Sampling frequency (kHz)'};
        app.fs.Position = [123 799 100 22];

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

        % Create parfor_arg
        app.parfor_arg = uispinner(app.FileselectionPanel);
        app.parfor_arg.ValueChangingFcn = createCallbackFcn(app, @refreshClass, true);
        app.parfor_arg.Limits = [-1 32];
        app.parfor_arg.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.parfor_arg.FontColor = [0.8 0.8 0.8];
        app.parfor_arg.BackgroundColor = [0.149 0.149 0.149];
        app.parfor_arg.Tooltip = {'Number of worker used for the video rendering (depends of the working station)'};
        app.parfor_arg.Position = [109 681 103 22];
        app.parfor_arg.Value = 10;

        % Create Label
        app.Label = uilabel(app.FileselectionPanel);
        app.Label.HorizontalAlignment = 'right';
        app.Label.FontColor = [0.902 0.902 0.902];
        app.Label.Position = [122 206 25 22];
        app.Label.Text = '';

        % Create setUpDropDown
        app.setUpDropDown = uidropdown(app.FileselectionPanel);
        app.setUpDropDown.Items = {'Doppler'};
        app.setUpDropDown.FontColor = [0.902 0.902 0.902];
        app.setUpDropDown.BackgroundColor = [0.502 0.502 0.502];
        app.setUpDropDown.Position = [164 837 90 22];
        app.setUpDropDown.Value = 'Doppler';

        % Create ppy
        app.ppy = uieditfield(app.FileselectionPanel, 'numeric');
        app.ppy.Limits = [0 10];
        app.ppy.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ppy.FontColor = [0.8 0.8 0.8];
        app.ppy.BackgroundColor = [0.149 0.149 0.149];
        app.ppy.Tooltip = {'Number of frequencies intervals you want to have the M0 of.'};
        app.ppy.Position = [211 744 62 22];

        % Create ppxy_label
        app.ppxy_label = uilabel(app.FileselectionPanel);
        app.ppxy_label.HorizontalAlignment = 'center';
        app.ppxy_label.FontColor = [0.8 0.8 0.8];
        app.ppxy_label.Tooltip = {'Camera pixel pitch (distance between spatial sampling points) in (m)'};
        app.ppxy_label.Position = [45 743 84 22];
        app.ppxy_label.Text = 'pp x y';

        % Create ppx
        app.ppx = uieditfield(app.FileselectionPanel, 'numeric');
        app.ppx.Limits = [0 10];
        app.ppx.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ppx.FontColor = [0.8 0.8 0.8];
        app.ppx.BackgroundColor = [0.149 0.149 0.149];
        app.ppx.Tooltip = {'Number of frequencies intervals you want to have the M0 of.'};
        app.ppx.Position = [122 744 73 22];

        % Create frame_position
        app.frame_position = uieditfield(app.FileselectionPanel, 'numeric');
        app.frame_position.Limits = [0 Inf];
        app.frame_position.RoundFractionalValues = 'on';
        app.frame_position.ValueDisplayFormat = '%.0f';
        app.frame_position.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.frame_position.FontColor = [0.8 0.8 0.8];
        app.frame_position.BackgroundColor = [0.149 0.149 0.149];
        app.frame_position.Tooltip = {''};
        app.frame_position.Position = [147 27 65 22];

        % Create positioninfileSliderLabel
        app.positioninfileSliderLabel = uilabel(app.FileselectionPanel);
        app.positioninfileSliderLabel.HorizontalAlignment = 'right';
        app.positioninfileSliderLabel.FontColor = [0.902 0.902 0.902];
        app.positioninfileSliderLabel.Position = [49 18 78 19];
        app.positioninfileSliderLabel.Text = {'position in file'; ''};

        % Create positioninfileSlider
        app.positioninfileSlider = uislider(app.FileselectionPanel);
        app.positioninfileSlider.Limits = [0 1];
        app.positioninfileSlider.MajorTicks = [];
        app.positioninfileSlider.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.positioninfileSlider.Tooltip = {'Change value to display a different video timestamp in the gui.'};
        app.positioninfileSlider.Position = [57 53 158 3];

        % Create file_loaded_lamp
        app.file_loaded_lamp = uilamp(app.FileselectionPanel);
        app.file_loaded_lamp.Position = [138 843 10 10];
        app.file_loaded_lamp.Color = [0.9294 0.6902 0.1294];

        % Create num_frames
        app.num_frames = uilabel(app.FileselectionPanel);
        app.num_frames.FontSize = 8;
        app.num_frames.FontColor = [1 1 1];
        app.num_frames.Position = [229 27 88 22];
        app.num_frames.Text = '/';

        % Create RefreshAppButton
        app.RefreshAppButton = uibutton(app.FileselectionPanel, 'push');
        app.RefreshAppButton.ButtonPushedFcn = createCallbackFcn(app, @RefreshAppButtonPushed, true);
        app.RefreshAppButton.BackgroundColor = [0.502 0.502 0.502];
        app.RefreshAppButton.FontColor = [0.902 0.902 0.902];
        app.RefreshAppButton.Tooltip = {'Refresh the app'};
        app.RefreshAppButton.Position = [5 11 31 23];
        app.RefreshAppButton.Text = '👌';

        % Create Nx
        app.Nx = uieditfield(app.FileselectionPanel, 'numeric');
        app.Nx.Limits = [0 Inf];
        app.Nx.Editable = 'off';
        app.Nx.FontColor = [0.8 0.8 0.8];
        app.Nx.BackgroundColor = [0.149 0.149 0.149];
        app.Nx.Tooltip = {'Width of the recorded interferograms'};
        app.Nx.Position = [123 712 73 22];

        % Create Ny
        app.Ny = uieditfield(app.FileselectionPanel, 'numeric');
        app.Ny.Limits = [0 Inf];
        app.Ny.Editable = 'off';
        app.Ny.FontColor = [0.8 0.8 0.8];
        app.Ny.BackgroundColor = [0.149 0.149 0.149];
        app.Ny.Tooltip = {'Height of the recorded interferograms'};
        app.Ny.Position = [211 712 62 22];

        % Create ppxy_label_2
        app.ppxy_label_2 = uilabel(app.FileselectionPanel);
        app.ppxy_label_2.HorizontalAlignment = 'center';
        app.ppxy_label_2.FontColor = [0.8 0.8 0.8];
        app.ppxy_label_2.Tooltip = {'Camera pixel pitch (distance between spatial sampling points) in (m)'};
        app.ppxy_label_2.Position = [36 712 84 22];
        app.ppxy_label_2.Text = 'Nx Ny';

        % Create AdvancedButton
        app.AdvancedButton = uibutton(app.FileselectionPanel, 'push');
        app.AdvancedButton.ButtonPushedFcn = createCallbackFcn(app, @AdvancedButtonPushed, true);
        app.AdvancedButton.BackgroundColor = [0.502 0.502 0.502];
        app.AdvancedButton.FontColor = [1 1 1];
        app.AdvancedButton.Tooltip = {'Advanced settings'};
        app.AdvancedButton.Position = [5 39 31 23];
        app.AdvancedButton.Text = '📎';

        % Create LoadAllCheckBox
        app.LoadAllCheckBox = uicheckbox(app.FileselectionPanel);
        app.LoadAllCheckBox.Tooltip = {'Load All the file in the memory if available. Use this if you have more than 128GB RAM usually and if you are working with local files.'};
        app.LoadAllCheckBox.Text = '';
        app.LoadAllCheckBox.Position = [8 837 14 22];

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
        app.AdvancedProcessingPanel.Visible = 'off';
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
        app.ShackHartmannCheckBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
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
        app.shackhartmannzernikeranksEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
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
        app.subaperturemarginEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.subaperturemarginEditField.FontColor = [0.8 0.8 0.8];
        app.subaperturemarginEditField.BackgroundColor = [0.149 0.149 0.149];
        app.subaperturemarginEditField.Tooltip = {'Number of subapertures used for Shack-Hartmann simulation'};
        app.subaperturemarginEditField.Position = [142 161 43 22];
        app.subaperturemarginEditField.Value = 0.15;

        % Create IterativeoptimizationCheckBox
        app.IterativeoptimizationCheckBox = uicheckbox(app.AberrationcompensationPanel);
        app.IterativeoptimizationCheckBox.Visible = 'off';
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
        app.SubAp_PCACheckBox.Visible = 'off';
        app.SubAp_PCACheckBox.Text = 'SubAp_PCA';
        app.SubAp_PCACheckBox.FontColor = [1 1 1];
        app.SubAp_PCACheckBox.Position = [10 337 89 22];

        % Create minEditField_2Label
        app.minEditField_2Label = uilabel(app.AberrationcompensationPanel);
        app.minEditField_2Label.HorizontalAlignment = 'right';
        app.minEditField_2Label.FontColor = [1 1 1];
        app.minEditField_2Label.Visible = 'off';
        app.minEditField_2Label.Position = [9 314 25 22];
        app.minEditField_2Label.Text = 'min';

        % Create minSubAp_PCAEditField
        app.minSubAp_PCAEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
        app.minSubAp_PCAEditField.Limits = [1 Inf];
        app.minSubAp_PCAEditField.ValueChangedFcn = createCallbackFcn(app, @minSubApPCAEditField_2ValueChanged, true);
        app.minSubAp_PCAEditField.Visible = 'off';
        app.minSubAp_PCAEditField.Position = [41 317 24 16];
        app.minSubAp_PCAEditField.Value = 1;

        % Create maxEditField_2Label
        app.maxEditField_2Label = uilabel(app.AberrationcompensationPanel);
        app.maxEditField_2Label.HorizontalAlignment = 'right';
        app.maxEditField_2Label.FontColor = [1 1 1];
        app.maxEditField_2Label.Visible = 'off';
        app.maxEditField_2Label.Position = [73 314 28 22];
        app.maxEditField_2Label.Text = 'max';

        % Create maxSubAp_PCAEditField
        app.maxSubAp_PCAEditField = uieditfield(app.AberrationcompensationPanel, 'numeric');
        app.maxSubAp_PCAEditField.Limits = [1 Inf];
        app.maxSubAp_PCAEditField.ValueChangedFcn = createCallbackFcn(app, @maxSubAp_PCAEditField_2_2ValueChanged, true);
        app.maxSubAp_PCAEditField.Visible = 'off';
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
        app.savecoefsCheckBox.Visible = 'off';
        app.savecoefsCheckBox.Text = 'save coefs';
        app.savecoefsCheckBox.FontColor = [0.8 0.8 0.8];
        app.savecoefsCheckBox.Position = [14 51 90 22];

        % Create ZernikeProjectionCheckBox
        app.ZernikeProjectionCheckBox = uicheckbox(app.AberrationcompensationPanel);
        app.ZernikeProjectionCheckBox.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.ZernikeProjectionCheckBox.Tooltip = {'Perform aberration compensation with Shack Hartmann simulation'};
        app.ZernikeProjectionCheckBox.Text = 'Zernike Projection';
        app.ZernikeProjectionCheckBox.FontColor = [0.902 0.902 0.902];
        app.ZernikeProjectionCheckBox.Position = [13 255 119 22];
        app.ZernikeProjectionCheckBox.Value = true;

        % Create referenceimageDropDownLabel
        app.referenceimageDropDownLabel = uilabel(app.AberrationcompensationPanel);
        app.referenceimageDropDownLabel.HorizontalAlignment = 'right';
        app.referenceimageDropDownLabel.FontColor = [0.902 0.902 0.902];
        app.referenceimageDropDownLabel.Position = [7 135 92 22];
        app.referenceimageDropDownLabel.Text = 'reference image';

        % Create referenceimageDropDown
        app.referenceimageDropDown = uidropdown(app.AberrationcompensationPanel);
        app.referenceimageDropDown.Items = {'central subaperture', 'resized image'};
        app.referenceimageDropDown.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
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
        app.subapnumpositionsEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
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
        app.imagesubapsizeratioEditField.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
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

        % Create RenderingparametersPanel
        app.RenderingparametersPanel = uipanel(app.GridLayout3);
        app.RenderingparametersPanel.ForegroundColor = [0.8 0.8 0.8];
        app.RenderingparametersPanel.Title = 'Rendering parameters';
        app.RenderingparametersPanel.BackgroundColor = [0.2 0.2 0.2];
        app.RenderingparametersPanel.Layout.Row = 1;
        app.RenderingparametersPanel.Layout.Column = 1;

        % Create svd_threshold_reset_button
        app.svd_threshold_reset_button = uibutton(app.RenderingparametersPanel, 'push');
        app.svd_threshold_reset_button.ButtonPushedFcn = createCallbackFcn(app, @svd_threshold_reset_buttonPushed, true);
        app.svd_threshold_reset_button.BackgroundColor = [0.149 0.149 0.149];
        app.svd_threshold_reset_button.FontColor = [0.9412 0.9412 0.9412];
        app.svd_threshold_reset_button.Position = [152 235 90 23];
        app.svd_threshold_reset_button.Text = 'svd_threshold';

        % Create spatial_filter
        app.spatial_filter = uicheckbox(app.RenderingparametersPanel);
        app.spatial_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_filter.Tooltip = {'Filter the spatial frequencies of the interferograms keeping only those between spatial filter range1 and 2 (between 0 and 1-> highest dimension)'};
        app.spatial_filter.Text = 'spatial_filter';
        app.spatial_filter.FontColor = [0.9412 0.9412 0.9412];
        app.spatial_filter.Position = [9 331 86 22];

        % Create hilbert_filter
        app.hilbert_filter = uicheckbox(app.RenderingparametersPanel);
        app.hilbert_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.hilbert_filter.Tooltip = {'Apply a hilbert transformation on the interferogram batch to get an analytical signal of each pixel.'};
        app.hilbert_filter.Text = 'hilbert_filter';
        app.hilbert_filter.FontColor = [0.9412 0.9412 0.9412];
        app.hilbert_filter.Position = [9 307 84 22];

        % Create spatial_filter_range
        app.spatial_filter_range = uilabel(app.RenderingparametersPanel);
        app.spatial_filter_range.FontColor = [0.9412 0.9412 0.9412];
        app.spatial_filter_range.Position = [94 331 106 22];
        app.spatial_filter_range.Text = 'spatial_filter_range';

        % Create spatial_filter_range1
        app.spatial_filter_range1 = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.spatial_filter_range1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_filter_range1.FontColor = [1 1 1];
        app.spatial_filter_range1.BackgroundColor = [0.149 0.149 0.149];
        app.spatial_filter_range1.Position = [199 331 29 22];

        % Create spatial_filter_range2
        app.spatial_filter_range2 = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.spatial_filter_range2.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_filter_range2.FontColor = [1 1 1];
        app.spatial_filter_range2.BackgroundColor = [0.149 0.149 0.149];
        app.spatial_filter_range2.Position = [240 331 28 22];

        % Create spatial_transformationDropDownLabel
        app.spatial_transformationDropDownLabel = uilabel(app.RenderingparametersPanel);
        app.spatial_transformationDropDownLabel.HorizontalAlignment = 'right';
        app.spatial_transformationDropDownLabel.FontColor = [0.9412 0.9412 0.9412];
        app.spatial_transformationDropDownLabel.Position = [9 285 123 22];
        app.spatial_transformationDropDownLabel.Text = 'spatial_transformation';

        % Create spatial_transformation
        app.spatial_transformation = uidropdown(app.RenderingparametersPanel);
        app.spatial_transformation.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_transformation.Tooltip = {'Type of light propagation calculation to perform (depends of the experimental setup)'};
        app.spatial_transformation.FontColor = [1 1 1];
        app.spatial_transformation.BackgroundColor = [0.502 0.502 0.502];
        app.spatial_transformation.Position = [147 285 100 22];

        % Create spatial_propagationEditFieldLabel
        app.spatial_propagationEditFieldLabel = uilabel(app.RenderingparametersPanel);
        app.spatial_propagationEditFieldLabel.HorizontalAlignment = 'right';
        app.spatial_propagationEditFieldLabel.FontColor = [0.9412 0.9412 0.9412];
        app.spatial_propagationEditFieldLabel.Position = [15 261 110 22];
        app.spatial_propagationEditFieldLabel.Text = 'spatial_propagation';

        % Create spatial_propagation
        app.spatial_propagation = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.spatial_propagation.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.spatial_propagation.FontColor = [1 1 1];
        app.spatial_propagation.BackgroundColor = [0.149 0.149 0.149];
        app.spatial_propagation.Tooltip = {'Distance of spatial reconstruction using the preceding calculation scheme in (m) '};
        app.spatial_propagation.Position = [140 261 60 22];

        % Create svd_filter
        app.svd_filter = uicheckbox(app.RenderingparametersPanel);
        app.svd_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svd_filter.Tooltip = {'Filter to remove intense time correlated feature images of the output fluctuation hologram using eigenvalue decomposition of the correlation matrix of frames.'};
        app.svd_filter.Text = 'svd_filter';
        app.svd_filter.FontColor = [0.9412 0.9412 0.9412];
        app.svd_filter.Position = [17 236 70 22];

        % Create svdx_filter
        app.svdx_filter = uicheckbox(app.RenderingparametersPanel);
        app.svdx_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_filter.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.svdx_filter.Text = 'svdx_filter';
        app.svdx_filter.FontColor = [0.9412 0.9412 0.9412];
        app.svdx_filter.Position = [17 209 76 22];

        % Create svd_threshold
        app.svd_threshold = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.svd_threshold.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svd_threshold.FontColor = [1 1 1];
        app.svd_threshold.BackgroundColor = [0.149 0.149 0.149];
        app.svd_threshold.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svd_threshold.Position = [246 236 31 22];

        % Create time_transformDropDownLabel
        app.time_transformDropDownLabel = uilabel(app.RenderingparametersPanel);
        app.time_transformDropDownLabel.HorizontalAlignment = 'right';
        app.time_transformDropDownLabel.FontColor = [0.9412 0.9412 0.9412];
        app.time_transformDropDownLabel.Position = [15 155 85 22];
        app.time_transformDropDownLabel.Text = 'time_transform';

        % Create time_transform
        app.time_transform = uidropdown(app.RenderingparametersPanel);
        app.time_transform.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.time_transform.Tooltip = {'Time tranformation to aggregate the fluctuation hologram. FFT is a frequency domain tranform and pass bad filter, PCA is a projection on intensity ordered eigen vectors, ICA is experimental.'};
        app.time_transform.FontColor = [1 1 1];
        app.time_transform.BackgroundColor = [0.502 0.502 0.502];
        app.time_transform.Position = [115 155 100 22];

        % Create frequency_rangeLabel
        app.frequency_rangeLabel = uilabel(app.RenderingparametersPanel);
        app.frequency_rangeLabel.FontColor = [0.9412 0.9412 0.9412];
        app.frequency_rangeLabel.Position = [17 130 95 22];
        app.frequency_rangeLabel.Text = 'frequency_range';

        % Create time_range1
        app.time_range1 = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.time_range1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.time_range1.FontColor = [1 1 1];
        app.time_range1.BackgroundColor = [0.149 0.149 0.149];
        app.time_range1.Position = [122 130 38 22];

        % Create time_range2
        app.time_range2 = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.time_range2.ValueChangedFcn = createCallbackFcn(app, @time_range2ValueChanged, true);
        app.time_range2.FontColor = [1 1 1];
        app.time_range2.BackgroundColor = [0.149 0.149 0.149];
        app.time_range2.Position = [177 130 38 22];

        % Create flat_field_gwEditFieldLabel
        app.flat_field_gwEditFieldLabel = uilabel(app.RenderingparametersPanel);
        app.flat_field_gwEditFieldLabel.HorizontalAlignment = 'right';
        app.flat_field_gwEditFieldLabel.FontColor = [0.9412 0.9412 0.9412];
        app.flat_field_gwEditFieldLabel.Position = [17 79 72 22];
        app.flat_field_gwEditFieldLabel.Text = 'flat_field_gw';

        % Create flat_field_gw
        app.flat_field_gw = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.flat_field_gw.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flat_field_gw.FontColor = [1 1 1];
        app.flat_field_gw.BackgroundColor = [0.149 0.149 0.149];
        app.flat_field_gw.Tooltip = {'flat_filed parameter to apply to some of the output images (gaussian width in pixels to divide the image to correct uneven illumination of images).'};
        app.flat_field_gw.Position = [104 79 100 22];

        % Create RenderPreviewButton
        app.RenderPreviewButton = uibutton(app.RenderingparametersPanel, 'push');
        app.RenderPreviewButton.ButtonPushedFcn = createCallbackFcn(app, @RenderPreviewButtonPushed, true);
        app.RenderPreviewButton.BackgroundColor = [0.502 0.502 0.502];
        app.RenderPreviewButton.FontColor = [1 1 1];
        app.RenderPreviewButton.Position = [204 42 100 23];
        app.RenderPreviewButton.Text = 'Render Preview';

        % Create SavePreviewButton
        app.SavePreviewButton = uibutton(app.RenderingparametersPanel, 'push');
        app.SavePreviewButton.ButtonPushedFcn = createCallbackFcn(app, @SavePreviewButtonPushed, true);
        app.SavePreviewButton.BackgroundColor = [0.502 0.502 0.502];
        app.SavePreviewButton.FontColor = [1 1 1];
        app.SavePreviewButton.Position = [204 7 100 23];
        app.SavePreviewButton.Text = 'Save Preview';

        % Create RenderPreviewLamp
        app.RenderPreviewLamp = uilamp(app.RenderingparametersPanel);
        app.RenderPreviewLamp.Position = [188 48 12 12];

        % Create svdx_t_filter
        app.svdx_t_filter = uicheckbox(app.RenderingparametersPanel);
        app.svdx_t_filter.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_t_filter.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.svdx_t_filter.Text = 'svd_x_t_filter';
        app.svdx_t_filter.FontColor = [0.9412 0.9412 0.9412];
        app.svdx_t_filter.Position = [17 183 93 22];

        % Create index_rangeLabel
        app.index_rangeLabel = uilabel(app.RenderingparametersPanel);
        app.index_rangeLabel.FontColor = [0.9412 0.9412 0.9412];
        app.index_rangeLabel.Position = [17 105 71 22];
        app.index_rangeLabel.Text = 'index_range';

        % Create index_range1
        app.index_range1 = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.index_range1.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.index_range1.FontColor = [1 1 1];
        app.index_range1.BackgroundColor = [0.149 0.149 0.149];
        app.index_range1.Position = [122 105 38 22];

        % Create index_range2
        app.index_range2 = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.index_range2.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.index_range2.FontColor = [1 1 1];
        app.index_range2.BackgroundColor = [0.149 0.149 0.149];
        app.index_range2.Position = [177 105 38 22];

        % Create svdx_threshold
        app.svdx_threshold = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.svdx_threshold.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_threshold.FontColor = [1 1 1];
        app.svdx_threshold.BackgroundColor = [0.149 0.149 0.149];
        app.svdx_threshold.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svdx_threshold.Position = [246 207 31 22];

        % Create svdx_t_threshold
        app.svdx_t_threshold = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.svdx_t_threshold.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_t_threshold.FontColor = [1 1 1];
        app.svdx_t_threshold.BackgroundColor = [0.149 0.149 0.149];
        app.svdx_t_threshold.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svdx_t_threshold.Position = [246 182 31 22];

        % Create svdx_Nsub
        app.svdx_Nsub = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.svdx_Nsub.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_Nsub.FontColor = [1 1 1];
        app.svdx_Nsub.BackgroundColor = [0.149 0.149 0.149];
        app.svdx_Nsub.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svdx_Nsub.Position = [189 207 31 22];

        % Create svdx_t_Nsub
        app.svdx_t_Nsub = uieditfield(app.RenderingparametersPanel, 'numeric');
        app.svdx_t_Nsub.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.svdx_t_Nsub.FontColor = [1 1 1];
        app.svdx_t_Nsub.BackgroundColor = [0.149 0.149 0.149];
        app.svdx_t_Nsub.Tooltip = {'number of first eigenvectors to remove from the fluctuation holograms (zero means default => time_range(1)/fs * batch_size * 2)'};
        app.svdx_t_Nsub.Position = [189 182 31 22];

        % Create NsubxLabel
        app.NsubxLabel = uilabel(app.RenderingparametersPanel);
        app.NsubxLabel.HorizontalAlignment = 'right';
        app.NsubxLabel.FontColor = [0.902 0.902 0.902];
        app.NsubxLabel.Position = [144 206 42 22];
        app.NsubxLabel.Text = 'Nsub x';

        % Create NsubxtLabel
        app.NsubxtLabel = uilabel(app.RenderingparametersPanel);
        app.NsubxtLabel.HorizontalAlignment = 'right';
        app.NsubxtLabel.FontColor = [0.902 0.902 0.902];
        app.NsubxtLabel.Position = [140 183 46 22];
        app.NsubxtLabel.Text = 'Nsub xt';

        % Create flip_y
        app.flip_y = uicheckbox(app.RenderingparametersPanel);
        app.flip_y.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_y.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.flip_y.Text = 'flip_y';
        app.flip_y.FontColor = [0.9412 0.9412 0.9412];
        app.flip_y.Position = [15 50 50 22];

        % Create flip_x
        app.flip_x = uicheckbox(app.RenderingparametersPanel);
        app.flip_x.ValueChangedFcn = createCallbackFcn(app, @refreshClass, true);
        app.flip_x.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.flip_x.Text = 'flip_x';
        app.flip_x.FontColor = [0.9412 0.9412 0.9412];
        app.flip_x.Position = [15 33 50 22];

        % Create square
        app.square = uicheckbox(app.RenderingparametersPanel);
        app.square.Tooltip = {'Same filter but decomposition bloc by bloc of frames'};
        app.square.Text = 'square';
        app.square.FontColor = [0.9412 0.9412 0.9412];
        app.square.Position = [15 16 59 22];

        % Create ImageRight
        app.ImageRight = uiimage(app.GridLayout4);
        app.ImageRight.ScaleMethod = 'stretch';
        app.ImageRight.ImageClickedFcn = createCallbackFcn(app, @ImageRightClicked, true);
        app.ImageRight.Layout.Row = 1;
        app.ImageRight.Layout.Column = 3;

        % Create ImageLeft
        app.ImageLeft = uiimage(app.GridLayout4);
        app.ImageLeft.ImageClickedFcn = createCallbackFcn(app, @ImageLeftClicked, true);
        app.ImageLeft.Layout.Row = 1;
        app.ImageLeft.Layout.Column = 2;

        % Create PanelPlot
        app.PanelPlot = uipanel(app.GridLayout4);
        app.PanelPlot.Title = 'Plot';
        app.PanelPlot.Visible = 'off';
        app.PanelPlot.BackgroundColor = [1 1 1];
        app.PanelPlot.Layout.Row = 1;
        app.PanelPlot.Layout.Column = 3;

        % Create RightClickImageContextMenu
        app.RightClickImageContextMenu = uicontextmenu(app.HoloDopplerUIFigure);

        % Create NextMenu
        app.NextMenu = uimenu(app.RightClickImageContextMenu);
        app.NextMenu.MenuSelectedFcn = createCallbackFcn(app, @NextMenuSelected, true);
        app.NextMenu.Text = 'Next';

        % Create ViewAllMenu
        app.ViewAllMenu = uimenu(app.RightClickImageContextMenu);
        app.ViewAllMenu.MenuSelectedFcn = createCallbackFcn(app, @ViewAllMenuSelected, true);
        app.ViewAllMenu.Text = 'ViewAll';

        % Assign app.RightClickImageContextMenu
        app.ImageLeft.ContextMenu = app.RightClickImageContextMenu;

        % Show the figure after all components are created
        app.HoloDopplerUIFigure.Visible = 'on';
    end

end

% App creation and deletion
methods (Access = public)

    % Construct app
    function app = HDapp

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
