function [obj,subFolderPath] = findGUICache(folderPath)
    % FINDGUICACHE Searches for a GUICache object in .mat files within a folder
    %   obj = FINDGUICACHE(folderPath) looks for .mat files in the specified
    %   folder and checks if they contain a variable named 'cache' that is
    %   an instance of the GUICache class. If found, it returns the object.

    % Initialize output
    obj = [];

    % Validate folder path
    if ~isfolder(folderPath)
        error('The specified path is not a valid folder.');
    end

    % Get a list of all .mat files in the folder
    matFiles = dir(fullfile(folderPath, '*.mat'));

    % Loop through each .mat file
    for i = 1:length(matFiles)
        filePath = fullfile(folderPath, matFiles(i).name);

        % Load file variables
        fileVars = whos('-file', filePath);

        % Check if 'cache' variable exists
        if any(strcmp({fileVars.name}, 'cache'))
            % Load only 'cache' variable
            loadedData = load(filePath, 'cache');

            % Verify if 'cache' is an instance of GUICache
            if isa(loadedData.cache, 'GuiCache')
                obj = loadedData.cache;
                return; % Return the first found instance
            end
        end
    end

    % If no valid object found, look into subfolders recursively
    subFolders = dir(folderPath);
    subFolders = subFolders([subFolders.isdir]); % Keep only directories
    subFolders(ismember({subFolders.name}, {'.', '..'})) = []; % Remove '.' and '..'

    for i = 1:length(subFolders)
        subFolderPath = fullfile(folderPath, subFolders(i).name);
        obj = findGUICache(subFolderPath); % Recursive call
        if ~isempty(obj)
            return; % Stop searching once an object is found
        end
    end
end