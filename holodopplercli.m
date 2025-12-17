function holodopplercli(varargin)
    % Initialize Application
    appRoot = fileparts(mfilename('fullpath'));
    versionFile = fullfile(appRoot, "version.txt");

    if isfile(versionFile)
        version_tag = readlines(versionFile);
        fprintf("HoloDoppler version : %s\n", version_tag);
    else
        fprintf("HoloDoppler version : Unknown (version.txt not found)\n");
    end

    % --- ARGUMENT PARSING & PATH SELECTION ---
    mode = 'single';
    inputPath = "";
    paths = string.empty;

    % Check arguments
    if nargin > 0
        arg1 = string(varargin{1});

        if arg1 == "-b"
            mode = 'batch';

            if nargin > 1
                inputPath = string(varargin{2});
            end

        else
            mode = 'single';
            inputPath = arg1;
        end

    end

    try

        if strcmp(mode, 'batch')
            % Batch Mode: Expecting a .txt file list
            if inputPath == ""
                [txt_name, txt_path] = uigetfile('*.txt', 'Select the input list (.txt) of holofiles');
                if isequal(txt_name, 0); return; end
                fullInputPath = fullfile(txt_path, txt_name);
            else
                fullInputPath = inputPath;

                if ~isfile(fullInputPath)
                    error("Batch file not found: %s", fullInputPath);
                end

            end

            fprintf("Running in Batch Mode: %s\n", fullInputPath);
            paths = strtrim(readlines(fullInputPath));
            paths = paths(paths ~= ""); % remove empty lines

        else
            % Single Mode: Expecting a .holo file
            if inputPath == ""
                [holo_name, holo_path] = uigetfile('*.holo', 'Select the .holo file');
                if isequal(holo_name, 0); return; end
                fullInputPath = fullfile(holo_path, holo_name);
            else
                fullInputPath = inputPath;
            end

            fprintf("Running in Single Mode: %s\n", fullInputPath);
            paths = string(fullInputPath);
        end

    catch ME
        fprintf("Error during path selection: %s\n", ME.message);
        return;
    end

    if isempty(paths)
        fprintf("No valid paths to process. Exiting.\n");
        return;
    end

    % --- PARAMETER SELECTION ---
    % Get default or user-defined parameter file
    paramspath = [];

    % Check for default config definition
    defaultConfigFile = fullfile(appRoot, "StandardConfigs", "CurrentDefault.txt");

    if isfile(defaultConfigFile)
        DefConfName = strtrim(readlines(defaultConfigFile));

        if ~isempty(DefConfName)
            defaultParamPath = fullfile(appRoot, "StandardConfigs", sprintf("%s.json", DefConfName(1)));

            if isfile(defaultParamPath)
                paramspath = defaultParamPath;
            end

        end

    end

    % If no default found, or if user needs to select (Optional: you can enforce UI here if preferred)
    if isempty(paramspath)
        fprintf('Select parameter file (.json)\n');
        [json_name, json_path] = uigetfile('*.json', 'Select parameter file (.json)');

        if ~isequal(json_name, 0)
            paramspath = fullfile(json_path, json_name);
        else
            error("No parameter file selected. Exiting.");
        end

    else
        fprintf("Using parameter file: %s\n", paramspath);
    end

    % --- EXECUTION LOOP ---
    fprintf("Initializing HoloDoppler Engine...\n");
    HD = HoloDopplerClass;

    for ind = 1:length(paths)
        currentPath = paths(ind);

        if currentPath == "" || ismissing(currentPath); continue; end

        if ~isfile(currentPath)
            fprintf("  [WARNING] File not found: %s\n", currentPath);
            continue;
        end

        fprintf("Processing (%d/%d): %s\n", ind, length(paths), currentPath);

        try
            HD.LoadFile(currentPath); % Load holo file
            HD.loadParams(paramspath); % Load parameter settings
            HD.VideoRendering(); % Render the video
        catch ME
            fprintf("  [ERROR] Processing failed for %s\n  %s\n", currentPath, ME.message);
        end

    end

    fprintf("All tasks completed.\n");
end
