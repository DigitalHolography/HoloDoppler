classdef FolderManagementUI < handle
% FolderManagementUI   User interface for batch rendering multiple files
%
%   FM = FolderManagementUI(APP) creates a non-modal figure that allows
%   managing a list of .cine/.holo files and their rendering configurations.
%   APP is the main HoloDoppler application object.

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

        newHeight = 100 + length(obj.drawerList) * 14;

        if newHeight > obj.Figure.Position(4)
            obj.Figure.Position(4) = newHeight;
        end

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
        % Define the file filter: description and extensions
        filters = { ...
                       '*.cine;*.holo', 'Supported Video Files (*.cine, *.holo)'; ...
                       '*.cine', 'Cine Files (*.cine)'; ...
                       '*.holo', 'Holo Files (*.holo)'; ...
                   };

        % Bring the FolderManagement figure to focus
        figure(obj.Figure);

        if ~isempty(obj.drawerList)
            % Start in the folder of the last file in the list
            startFolder = fileparts(obj.drawerList{end});
            [file, path] = uigetfile(filters, 'Select File', startFolder);
        else
            [file, path] = uigetfile(filters, 'Select File');
        end

        figure(obj.Figure);

        if isequal(file, 0), return; end

        [~, ~, ext] = fileparts(file);

        if ismember(ext, {'.cine', '.holo', '.h5'})
            obj.drawerList{end + 1} = fullfile(path, file);
        else
            uialert(obj.Figure, 'File must be .cine, .holo, .raw or .h5', 'Invalid File Type');
        end

        obj.MainApp.HD.drawer_list = obj.drawerList;
        obj.updateDisplay();
    end

    function selectCurrent(obj)
        app = obj.MainApp;

        if isempty(app.HD.file)
            uialert(obj.Figure, 'No current file loaded', 'No File');
            return;
        end

        filePath = app.HD.file.path;
        [~, ~, ext] = fileparts(filePath);

        if ismember(ext, {'.cine', '.holo'})
            obj.drawerList{end + 1} = filePath;
        else
            uialert(obj.Figure, 'File must be .cine or .holo', 'Invalid File Type');
        end

        app.HD.drawer_list = obj.drawerList;
        obj.updateDisplay();
    end

    function selectCurrentFolder(obj)
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
        app = obj.MainApp;

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

        app.HD.drawer_list = obj.drawerList;
        obj.updateDisplay();
    end

    function addFilesFromFolder(obj, folder)
        entries = dir(folder);

        for i = 1:numel(entries)

            if ~entries(i).isdir
                [~, ~, ext] = fileparts(entries(i).name);

                if ismember(ext, {'.cine', '.holo'})
                    obj.drawerList{end + 1} = fullfile(folder, entries(i).name);
                end

            end

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
                        obj.drawerList{end + 1} = lines{i};
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
        app = obj.MainApp;
        keepZ = obj.KeepZCheckbox.Value;
        defaultParamPath = fullfile(fileparts(mfilename('fullpath')), 'StandardConfigs', ...
        'Phantom S711 37kHz retinal analysis.json'); % use fullfile for robustness

        originalParams = app.HD.params;

        for i = 1:length(obj.drawerList)
            filePath = obj.drawerList{i};
            [dirName, name] = fileparts(filePath);
            % New fixed location
            configFile = fullfile(dirName, name, sprintf('%s_input_HD_params.json', name));

            if ~isfile(configFile) && isfile(defaultParamPath)
                % No config yet → load default and save
                app.HD.loadParams(defaultParamPath);
            end

            % Save (overwrites existing or creates new)
            app.HD.saveParams(filePath, keepZ);
            fprintf('Saved config for: %s\n', filePath);
        end

        app.HD.params = originalParams;
    end

    function fileList = buildDrawerFileList(obj)
        % Build a cell array: {filePath, {paramsStruct}, configPath} for each entry.
        fileList = cell(size(obj.drawerList));

        for i = 1:length(obj.drawerList)
            filePath = obj.drawerList{i};
            [dirName, name] = fileparts(filePath);
            configFile = fullfile(dirName, name, sprintf('%s_input_HD_params.json', name));

            if isfile(configFile)
                % Load the parameters (simple jsondecode)
                fid = fopen(configFile, 'r');
                raw = fread(fid, inf, '*char')';
                fclose(fid);
                params = jsondecode(raw);
                fileList{i} = {filePath, {params}, configFile}; % config_list as cell
            else
                % No config file – leave empty, but keep the path if needed later
                fileList{i} = {filePath, {}, configFile};
            end

        end

    end

    function renderVideos(obj)
        app = obj.MainApp;
        fileList = obj.buildDrawerFileList();

        % Determine number of workers from the first valid config
        numWorkers = 0;

        for i = 1:length(fileList)

            if ~isempty(fileList{i}) && ~isempty(fileList{i}{2})
                firstParams = fileList{i}{2}{1};
                numWorkers = firstParams.parforArg;
                break;
            end

        end

        if numWorkers > 0

            if isempty(app.HD.poolManager)
                app.HD.poolManager = ParallelPoolManager(numWorkers);
            end

            app.HD.poolManager.acquire();
            cleanupPool = onCleanup(@() app.HD.poolManager.release());

            pool = app.HD.poolManager.Pool;
            fprintf("Processing %d files with %d workers ...\n", ...
                length(fileList), pool.NumWorkers);
        else
            fprintf("Processing %d files in serial mode...\n", length(fileList));
        end

        % === Traitement des fichiers ===
        for i = 1:length(fileList)
            entry = fileList{i};

            if ~isempty(entry) && ~isempty(entry{2})

                for j = 1:length(entry{2})
                    app.HD.LoadFile(entry{1}, params = entry{2}{j});
                    app.HD.VideoRendering();
                    fprintf("Completed: %s [%d/%d]\n", entry{1}, j, length(entry{2}));
                end

            end

        end

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

end

end
