function [jsonPath] = checkGuiParamsFromJson(path)

    % This function checks if in the folder you can find a GUI
    % parameter file. If not it creates a Default one. If you find obsolete files it also
    % fills them with the new parameters

    % Additionally this function returns the list of the names of all valid
    % GUIParameters files found (they must be in the form
    % 'InputGUIParams*.json')

    dir_path_json = fullfile(path, 'json');

    % We first check if an old txt parameter exists and write a json parameter file instead
    filename_txt = 'InputGUIParams.txt';
    filename_json = 'InputGUIParams.json';
    dir_path_txt = fullfile(path, 'txt');
    txtFilePath = fullfile(dir_path_txt, filename_txt);
    txt_exists = isfile(txtFilePath);

    jsonInput = fileread(fullfile("Parameters","DefaultGUIParams.json"));
    init_data = jsondecode(jsonInput);

    if txt_exists
        disp("Found an old txt file. Writing a new json parameter file instead")
        fileContent = fileread(txtFilePath);
        json_data = txt2json_param(fileContent);
        [correct_data, ~] = compare_json_data(init_data, json_data);
        jsonData = jsonencode(correct_data, PrettyPrint = true);
        if ~isfolder(dir_path_json)
            mkdir(dir_path_json);
            disp(['Directory ', dir_path_json, ' has been created.']);
        end
        jsonPath = fullfile(dir_path_json, filename_json);
        fileID = fopen(jsonPath, 'w');
        fprintf(fileID, jsonData);
        fclose(fileID);
    end

    % We now check all the existing json files named like 'InputGUIParams*.json'
    jsonFiles = dir(fullfile(dir_path_json, 'InputGUIParams*.json'));

    if ~isempty(jsonFiles)
        disp("Found parameter files : ")

        for i = 1:numel(jsonFiles)
            jsonPath = fullfile(dir_path_json,jsonFiles(i).name);
            disp(jsonPath)
            jsonData = fileread(jsonPath);
            parsedData = jsondecode(jsonData);

            [correct_data, ~] = compare_json_data(init_data, parsedData);

            delete(jsonPath)

            jsonData = jsonencode(correct_data, PrettyPrint = true);

            jsonPath = fullfile(dir_path_json, jsonFiles(i).name);

            fileID = fopen(jsonPath, 'w');
            fprintf(fileID, jsonData);
            fclose(fileID);
            
        end

        

    else
        disp("Parameter file does not exist, writing in process")

        jsonData = jsonencode(init_data, PrettyPrint = true);

        if ~isfolder(dir_path_json)
            mkdir(dir_path_json);
            disp(['Directory ', dir_path_json, ' has been created.']);
        end

        jsonPath = fullfile(dir_path_json, filename_json);

        fileID = fopen(jsonPath, 'w');
        fprintf(fileID, jsonData);
        fclose(fileID);

    end

end
