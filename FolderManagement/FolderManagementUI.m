classdef FolderManagementUI < handle
% FolderManagementUI   User interface for batch rendering multiple files
%
%   FM = FolderManagementUI(APP) creates a non-modal figure that allows
%   managing a list of .cine/.holo files and their rendering configurations.
%   APP is the main HoloDoppler application object.
%
%   Each file in the list has exactly one associated configuration.

properties (Access = private)
    MainApp % Reference to the main HoloDoppler app
    Figure % uifigure handle
    TextArea % uitextarea displaying the file list
    KeepZCheckbox % uicheckbox for 'Keep z distance' option
    drawerList % Local reference to the drawer list for easy access
end

methods

    function obj = FolderManagementUI(mainApp)
        % Constructor – builds and displays the UI.
        arguments
            mainApp
        end

        obj.MainApp = mainApp;
        obj.drawerList = mainApp.HD.drawer_list;
        obj.createUI();
    end

end

methods (Access = private)

    function createUI(obj)
        % Create the figure and all UI components.

        % Calculate initial height based on number of files
        initialHeight = 260 + length(obj.drawerList) * 14;

        mainApp = obj.MainApp;

        if isvalid(mainApp) && ismethod(mainApp, 'getMainFigure')
            mainFig = mainApp.getMainFigure();

            if isvalid(mainFig)
                mainPos = mainFig.Position;
                xPos = mainPos(1) + mainPos(3) + 20;
                yPos = mainPos(2);
            else
                xPos = 300; yPos = 300;
            end

        else
            xPos = 300; yPos = 300;
        end

        obj.Figure = uifigure('Position', [xPos, yPos, 700, initialHeight], ...
            'Color', [0.2, 0.2, 0.2], ...
            'Name', 'Folder management', ...
            'Resize', 'on', ...
            'WindowStyle', 'normal', ...
            'CloseRequestFcn', @(~, ~) obj.closeFigure());

        drawnow;

        % Main grid: list area (top) + button grid (bottom)
        mainGrid = uigridlayout(obj.Figure, [2, 1], ...
            'ColumnWidth', {'1x'}, ...
            'RowHeight', {'1x', 'fit'}, ...
            'Padding', [10, 10, 10, 10], ...
            'BackgroundColor', [0.2, 0.2, 0.2], ...
            'RowSpacing', 10, ...
            'ColumnSpacing', 10);

        % Text area for file list
        if isempty(obj.drawerList)
            displayValue = {''};
        else
            displayValue = obj.drawerList;
        end

        obj.TextArea = uitextarea('Parent', mainGrid, ...
            'BackgroundColor', [0.2, 0.2, 0.2], ...
            'FontColor', [0.8, 0.8, 0.8], ...
            'Value', displayValue, ...
            'Editable', 'off');
        obj.TextArea.Layout.Row = 1;
        obj.TextArea.Layout.Column = 1;

        % Button grid: 4 rows × 3 columns
        buttonGrid = uigridlayout(mainGrid, [4, 3], ...
            'ColumnWidth', {200, 200, 200}, ...
            'RowHeight', {'fit', 'fit', 'fit', 'fit'}, ...
            'Padding', [5, 5, 5, 5], ...
            'BackgroundColor', [0.2, 0.2, 0.2]);
        buttonGrid.Layout.Row = 2;
        buttonGrid.Layout.Column = 1;

        % Checkbox
        obj.KeepZCheckbox = uicheckbox('Parent', buttonGrid, ...
            'FontColor', [1 1 1], ...
            'Text', 'Keep z distance', ...
            'Value', 0);
        obj.KeepZCheckbox.Layout.Row = 2;
        obj.KeepZCheckbox.Layout.Column = 3;

        % Common button colors
        bkgColor = [0.5, 0.5, 0.5];
        fontColor = [1, 1, 1];
        renderColor = [0.2, 0.6, 0.2];

        % Column 1 buttons
        obj.makeButton(buttonGrid, [1, 1], 'Select file', ...
            @(~, ~) obj.selectFile(), bkgColor, fontColor);
        obj.makeButton(buttonGrid, [2, 1], 'Select folder', ...
            @(~, ~) obj.selectFolder(), bkgColor, fontColor);
        obj.makeButton(buttonGrid, [3, 1], 'Select current', ...
            @(~, ~) obj.selectCurrent(), bkgColor, fontColor);
        obj.makeButton(buttonGrid, [4, 1], 'Select current Folder', ...
            @(~, ~) obj.selectCurrentFolder(), bkgColor, fontColor);

        % Column 2 buttons
        obj.makeButton(buttonGrid, [1, 2], 'Clear list', ...
            @(~, ~) obj.clearList(), bkgColor, fontColor);
        obj.makeButton(buttonGrid, [3, 2], 'Save to txt', ...
            @(~, ~) obj.saveToTxt(), bkgColor, fontColor);
        obj.makeButton(buttonGrid, [4, 2], 'Load from txt', ...
            @(~, ~) obj.loadFromTxt(), bkgColor, fontColor);

        % Column 3 buttons
        obj.makeButton(buttonGrid, [3, 3], 'Save configs', ...
            @(~, ~) obj.saveConfigs(), bkgColor, fontColor);
        obj.makeButton(buttonGrid, [4, 3], 'Delete all configs', ...
            @(~, ~) obj.deleteAllConfigs(), bkgColor, fontColor);
        obj.makeButton(buttonGrid, [1, 3], 'Render Videos', ...
            @(~, ~) obj.renderVideos(), renderColor, fontColor);

        % Set consistent font
        fontname(obj.Figure, 'Arial');
        fontsize(obj.Figure, 12, "points");
    end

    function btn = makeButton(~, parent, pos, label, cb, bgColor, fontColor)
        btn = uibutton(parent, 'push', ...
            'BackgroundColor', bgColor, ...
            'FontColor', fontColor, ...
            'Text', label, ...
            'ButtonPushedFcn', cb);
        btn.Layout.Row = pos(1);
        btn.Layout.Column = pos(2);
    end

    function updateDisplay(obj)
        % Refresh the text area and adjust window height.

        if isempty(obj.drawerList)
            displayValue = {''};
        else
            displayValue = obj.drawerList;
        end

        obj.TextArea.Value = displayValue;

        newHeight = 188 + length(obj.drawerList) * 18;
        obj.Figure.Position(4) = max(newHeight, 206);

    end

    function closeFigure(obj)
        % Clean up and delete the figure.
        delete(obj.Figure);
        delete(obj); % object will be destroyed
    end

    % -----------------------------------------------------------------
    % Callback methods
    % -----------------------------------------------------------------

    function selectFile(obj)
        % Select a single .cine or .holo file.
        filters = { ...
                       '*.cine;*.holo', 'Supported Video Files (*.cine, *.holo)'; ...
                       '*.cine', 'Cine Files (*.cine)'; ...
                       '*.holo', 'Holo Files (*.holo)'; ...
                   };

        % Bring the FolderManagement figure to focus
        figure(obj.Figure);

        if ~isempty(obj.drawerList)
            startFolder = fileparts(obj.drawerList{end});
            [file, path] = uigetfile(filters, 'Select File', startFolder);
        else
            [file, path] = uigetfile(filters, 'Select File');
        end

        figure(obj.Figure);

        if isequal(file, 0), return; end

        [~, ~, ext] = fileparts(file);

        if ismember(ext, {'.cine', '.holo', '.h5'})
            obj.addUniqueFile(fullfile(path, file));
        else
            uialert(obj.Figure, 'File must be .cine, .holo, .raw or .h5', 'Invalid File Type');
        end

        obj.MainApp.HD.drawer_list = obj.drawerList;
        obj.updateDisplay();
    end

    function selectCurrent(obj)
        % Add the currently loaded file in the main application.
        app = obj.MainApp;

        if isempty(app.HD.file)
            uialert(obj.Figure, 'No current file loaded', 'No File');
            return;
        end

        filePath = app.HD.file.path;
        [~, ~, ext] = fileparts(filePath);

        if ismember(ext, {'.cine', '.holo'})
            obj.addUniqueFile(filePath);
        else
            uialert(obj.Figure, 'File must be .cine or .holo', 'Invalid File Type');
        end

        app.HD.drawer_list = obj.drawerList;
        obj.updateDisplay();
    end

    function selectCurrentFolder(obj)
        % Add all supported files from the folder of the currently loaded file.
        app = obj.MainApp;

        if isempty(app.HD.file)
            uialert(obj.Figure, 'No current file loaded', 'No File');
            return;
        end

        obj.addFilesFromFolder(app.HD.file.dir);
        app.HD.drawer_list = obj.drawerList;
        obj.updateDisplay();
    end

    function selectFolder(obj)
        % Let the user pick a folder and add all supported files.
        figureHandle = obj.Figure;
        figure(figureHandle);

        if ~isempty(obj.drawerList)
            lastFolder = fileparts(obj.drawerList{end});
        else
            lastFolder = '';
        end

        folder = uigetdir(lastFolder);

        figure(figureHandle);

        if folder == 0, return; end
        obj.addFilesFromFolder(folder);

        obj.MainApp.HD.drawer_list = obj.drawerList;
        obj.updateDisplay();
    end

    function addFilesFromFolder(obj, folder)
        % Append all .cine / .holo files from a folder, avoiding duplicates.
        entries = dir(folder);

        for i = 1:numel(entries)

            if ~entries(i).isdir
                [~, ~, ext] = fileparts(entries(i).name);

                if ismember(ext, {'.cine', '.holo'})
                    obj.addUniqueFile(fullfile(folder, entries(i).name));
                end

            end

        end

    end

    function addUniqueFile(obj, fullFilePath)
        % Add the file only if it is not already in the list.
        if ~any(strcmp(obj.drawerList, fullFilePath))
            obj.drawerList{end + 1} = fullFilePath;
        end

    end

    function clearList(obj)
        obj.drawerList = {};
        obj.updateDisplay();
    end

    function saveToTxt(obj)
        figureHandle = obj.Figure;
        figure(figureHandle);

        [file, path] = uiputfile('*.txt', 'Save list as text file');

        figure(figureHandle);

        if isequal(file, 0), return; end
        writelines(obj.drawerList, fullfile(path, file));
    end

    function loadFromTxt(obj)
        app = obj.MainApp;

        figureHandle = obj.Figure;
        figure(figureHandle);

        [file, path] = uigetfile('*.txt', 'Select File');

        figure(figureHandle);

        if isequal(file, 0), return; end
        lines = readlines(fullfile(path, file));

        for i = 1:numel(lines)

            if ~isempty(lines(i))

                try
                    [~, ~, ext] = fileparts(lines(i));

                    if ismember(ext, {'.cine', '.holo'})
                        obj.addUniqueFile(lines{i}); % avoid duplicates
                    end

                catch e
                    disp(e);
                end

            end

        end

        app.HD.drawer_list = obj.drawerList;
        obj.updateDisplay();
    end

    function saveConfigs(obj)
        % Save/update the HoloDoppler parameter config for every file in the list.
        app = obj.MainApp;
        keepZ = obj.KeepZCheckbox.Value;

        % Application root is one level above this class file
        appRoot = fileparts(fileparts(mfilename('fullpath')));
        defaultParamPath = fullfile(appRoot, 'StandardConfigs', ...
        'Phantom S711 37kHz retinal analysis.json');

        originalParams = app.HD.params;

        for i = 1:length(obj.drawerList)
            filePath = obj.drawerList{i};
            [dirName, name] = fileparts(filePath);
            configFile = fullfile(dirName, name, sprintf('%s_input_HD_params.json', name));

            if ~isfile(configFile)

                if isfile(defaultParamPath)
                    app.HD.loadParams(defaultParamPath);
                else
                    warning('FolderManagementUI:saveConfigs:NoDefaultConfig', ...
                        'Default config file "%s" not found. Skipping config creation for %s.', ...
                        defaultParamPath, filePath);
                    continue;
                end

            end

            app.HD.saveParams(filePath, keepZ);
            fprintf('Saved config for: %s\n', filePath);
        end

        % Restore original parameters
        app.HD.params = originalParams;
    end

    function fileList = buildDrawerFileList(obj)
        % Build cell array: {filePath, paramsStruct, configPath}
        % Each file now has exactly one configuration.
        fileList = cell(length(obj.drawerList), 3);

        for i = 1:length(obj.drawerList)
            parentPath = obj.drawerList{i}; % full path to .cine/.holo
            [parentDir, name] = fileparts(parentPath);
            configFile = fullfile(parentDir, name, sprintf('%s_input_HD_params.json', name));

            if isfile(configFile)

                try
                    fid = fopen(configFile, 'r');
                    raw = fread(fid, inf, '*char')';
                    fclose(fid);
                    params = jsondecode(raw);
                catch
                    params = struct(); % empty if load fails
                end

                fileList{i, 1} = parentPath;
                fileList{i, 2} = params;
                fileList{i, 3} = configFile;
            else
                fileList{i, 1} = parentPath;
                fileList{i, 2} = struct();
                fileList{i, 3} = configFile;
            end

        end

    end

    function renderVideos(obj)
        app = obj.MainApp;
        fileList = obj.buildDrawerFileList(); % {filePath, paramsStruct, configPath}

        % Determine number of workers from the first available config
        numWorkers = 0;
        cluster = parcluster;
        maxWorkers = cluster.NumWorkers;

        for i = 1:size(fileList, 1)

            if ~isempty(fileList{i, 2})
                params = fileList{i, 2};

                if isfield(params, 'parforArg')
                    numWorkers = params.parforArg;
                    break;
                end

            end

        end

        % Safeguard: ensure at least 1 worker and not exceeding pool maximum
        if numWorkers <= 0
            numWorkers = max(1, maxWorkers - 2);
        else

            if numWorkers > maxWorkers
                warning('FolderManagementUI:parforArgExceedsMaxWorkers', ...
                    'parforArg (%d) exceeds max workers (%d). Using %d.', ...
                    numWorkers, maxWorkers, maxWorkers);
                numWorkers = maxWorkers;
            end

        end

        if isempty(app.HD.poolManager)
            app.HD.poolManager = ParallelPoolManager(numWorkers);
        end

        app.HD.poolManager.acquire();
        cleanupPool = onCleanup(@() app.HD.poolManager.release());

        pool = app.HD.poolManager.Pool;
        fprintf("Processing %d files with %d workers ...\n", ...
            size(fileList, 1), pool.NumWorkers);

        % Load the default configuration (empty struct if unavailable)
        defaultConfig = loadDefaultConfig(obj);

        % === File processing ===
        for i = 1:size(fileList, 1)
            filePath = fileList{i, 1};
            params = fileList{i, 2};

            if isempty(params) || isempty(fieldnames(params))

                if isempty(fieldnames(defaultConfig))
                    warning('FolderManagementUI:noConfig', ...
                        'No config for %s – and no default config available. Skipping.', filePath);
                    continue;
                end

                params = defaultConfig;
            end

            % Use the single configuration for this file
            app.HD.LoadFile(filePath, params = params);
            app.HD.VideoRendering();
            fprintf("Completed: %s\n", filePath);
        end

        % NOTE: After this loop the main application points to the last rendered file.
        % Consider saving and restoring the original state if needed.
    end

    function deleteAllConfigs(obj)
        n = 0;

        for i = 1:length(obj.drawerList)
            filePath = obj.drawerList{i};
            [dirName, name] = fileparts(filePath);
            configFile = fullfile(dirName, name, sprintf('%s_input_HD_params.json', name));

            if isfile(configFile)
                delete(configFile);
                n = n + 1;
            end

        end

        fprintf('Deleted %d config files for %d entries\n', n, length(obj.drawerList));
    end

    function params = loadDefaultConfig(~)
        % Load the standard default parameter file.
        % Uses the application root (one level above FolderManagement).
        try
            appRoot = fileparts(fileparts(mfilename('fullpath')));
            defaultParamPath = fullfile(appRoot, 'StandardConfigs', ...
            'Phantom S711 37kHz retinal analysis.json');

            if isfile(defaultParamPath)
                fid = fopen(defaultParamPath, 'r');
                raw = fread(fid, inf, '*char')';
                fclose(fid);
                params = jsondecode(raw);
            else
                params = struct();
            end

        catch
            params = struct();
        end

    end

end

end
