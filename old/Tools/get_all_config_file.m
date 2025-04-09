function config_file_list = get_all_config_file(input_filepath, input_filename)
    config_file_list = {};
    [~, file_name, ~] = fileparts(input_filename);
    FolderInfo = dir(input_filepath);
    for i = 1:length(FolderInfo)
        result = regexp(FolderInfo(i).name, sprintf("^%s-config_([0-9]+).mat$", file_name), 'match');
        if (~isempty(result))
            config_file_list{end + 1} = char(result); %#ok<AGROW> 
        end
    end
end