function [file_name, suffix] = get_last_file_name(input_filepath, input_filename, ext)
    suffix = 0;
    [~, file_name, ~] = fileparts(input_filename);
    while exist(fullfile(input_filepath, sprintf("%s_%d.%s", file_name, suffix, ext)), 'file')
        suffix = suffix + 1;
    end
    suffix = suffix - 1;
end