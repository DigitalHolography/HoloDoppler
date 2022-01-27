function [file_name, suffix] = get_last_config_file_name(input_filepath, input_filename)
    suffix = 0;
    [~, file_name, ~] = fileparts(input_filename);
    while exist(fullfile(input_filepath, sprintf("%s_%d.mat", file_name, suffix)), 'file')
        suffix = suffix + 1;
    end
    suffix = suffix - 1;
end