function config_list = get_config_files(file_path)
% Initialize the config list to store decoded structs
config_list = {};

% Get the directory from the provided file path
[path, name, ~] = fileparts(file_path);

% List all files in the directory
files = dir(path);

% Loop through each file in the directory
for i = 1:numel(files)
    % Get the file name
    file_name = files(i).name;

    % Check if the file is a JSON file and contains "_RenderingParameters" in its name
    if contains(file_name, strcat(name, '_RenderingParameters')) && endsWith(file_name, '.json')
        % Construct the full file path
        full_file_path = fullfile(path, file_name);

        % Try to read and decode the JSON file
        try
            % Read the JSON content
            json_data = fileread(full_file_path);

            % Decode the JSON content into a MATLAB struct
            decoded_data = jsondecode(json_data);

            % Add the decoded struct to the config list
            config_list{end + 1} = decoded_data;

        catch ME
            % If there's an error in reading or decoding, display a message
            disp(['Error reading or decoding file: ', full_file_path]);
            disp(ME.message);
        end

    end

end

end
