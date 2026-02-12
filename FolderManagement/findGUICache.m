function [obj, subFolderPath] = findGUICache(folderPath, name)
% FINDGUICACHE Searches for a GUICache object in .mat files within a folder
%   obj = FINDGUICACHE(folderPath) looks for .mat files in the specified
%   folder and checks if they contain a variable named 'cache' that is
%   an instance of the GUICache class. If found, it returns the object.
warning('off', 'MATLAB:load:cannotLoadObjectClass'); % old class type wause warnings like Warning: Cannot load an object of class 'OCTdata'
% Initialize output
obj = [];
subFolderPath = [];

% Validate folder path
if ~isfolder(folderPath)
    error('The specified path is not a valid folder.');
end

% Get a list of all .mat files in the folder
matFiles = dir(fullfile(folderPath, '*.mat'));

% Loop through each .mat file
for i = 1:length(matFiles)
    filePath = fullfile(folderPath, matFiles(i).name);

    if ~contains(matFiles(i).name, name)
        continue
    end

    % Load file variables
    fileVars = whos('-file', filePath);

    % Check if 'cache' variable exists
    if any(strcmp({fileVars.name}, 'cache'))
        % Load only 'cache' variable
        loadedData = load(filePath, 'cache');

        % Verify if 'cache' is an instance of GUICache
        if isa(loadedData.cache, 'GuiCache')
            obj = loadedData.cache;
            % Return the last found instance
        end

    end

end

if ~isempty(obj)
    return
end

% If no valid object found, look into subfolders recursively
subFolders = dir(folderPath);
subFolders = subFolders([subFolders.isdir]); % Keep only directories
subFolders(ismember({subFolders.name}, {'.', '..'})) = []; % Remove '.' and '..'

for i = 1:length(subFolders)
    subFolderPath = fullfile(folderPath, subFolders(i).name);
    obj = findGUICache(subFolderPath, name); % Recursive call

    if ~isempty(obj)
        return; % Stop searching once an object is found
    end

end

warning('on', 'MATLAB:load:cannotLoadObjectClass');
end
