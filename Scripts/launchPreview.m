%% Get the list of holofiles to be processed from user
fprintf("=== HOLOPROCESS START ===\n");

version_tag = readlines("version.txt");

fprintf("HoloDoppler version : %s\n", version_tag);

fprintf('Select input list (.txt) containing file paths\n');
[txt_name, txt_path] = uigetfile('*.txt', 'Select input list (.txt) containing file paths');

if isequal(txt_name, 0)
    error("No input .txt file selected. Exiting process.");
end

try
    paths = strtrim(readlines(fullfile(txt_path, txt_name)));
    paths = paths(paths ~= ""); % remove empty lines
catch ME
    error("Error reading the input .txt file: %s", ME.message);
end

if isempty(paths)
    error("The input list is empty. Please provide a valid list of holofiles.");
end

fprintf("Loaded %d paths from input list.\n", numel(paths));

%% Get default or user-defined parameter file
paramspath = [];

% Load default config if available
defaultConfigFile = fullfile("StandardConfigs", "CurrentDefault.txt");

if isfile(defaultConfigFile)
    DefConfName = strtrim(readlines(defaultConfigFile));

    if ~isempty(DefConfName)
        defaultParamPath = fullfile("StandardConfigs", sprintf("%s.json", DefConfName(1)));

        if isfile(defaultParamPath)
            paramspath = defaultParamPath;
            fprintf("Default parameter file found: %s\n", paramspath);
        else
            fprintf("Default parameter JSON not found: %s\n", defaultParamPath);
        end

    end

end

% Allow user to override
fprintf('Select parameter file (.json) or Cancel to use default\n');
[json_name, json_path] = uigetfile('*.json', 'Select parameter file (.json) or Cancel to use default');

if ~isequal(json_name, 0)
    paramspath = fullfile(json_path, json_name);
    fprintf("Using user-selected parameter file: %s\n", paramspath);
elseif isempty(paramspath)
    error("No parameter file selected and no default available.");
else
    fprintf("Using default parameter file: %s\n", paramspath);
end

%% Launch HoloDoppler preview processing
HD = HoloDopplerClass;

fprintf("\n=== STARTING HOLOFILE PROCESSING ===\n");

imgs = cell(1, numel(paths));

for ind = 1:numel(paths)
    currentPath = strtrim(paths(ind));

    if ~isfile(currentPath)
        fprintf("Skipping missing file: %s\n", currentPath);
        continue;
    end

    fprintf("Processing file %d of %d: %s\n", ind, numel(paths), currentPath);

    try
        HD.LoadFile(currentPath); % Load holo file
        HD.loadParams(paramspath); % Load parameter settings
        HD.PreviewRendering();

        if HD.params.applyautofocusfromref
            HD.params.spatial_propagation = autofocus(HD.view, HD.params); % Autofocus
        end

        HD.PreviewRendering(); % Render the preview
        img = HD.view.getImages({"power_Doppler"});
        imgs{ind} = img{1};
    catch ME
        fprintf("Error processing %s: %s\n", currentPath, ME.message);
    end

end

fprintf("\n=== PROCESSING COMPLETE ===\n");

%% Show the previews
valid = imgs(~cellfun(@isempty, imgs));
figure;
montage(valid, 'BorderSize', 5);
title('Preview');
