function output_fullfile = create_output_filename(input_filepath, input_filename, suffix_name, extension)
% construct output filename 
% name.cine -> name_<suffix_number>_<suffix_name>.<extension>
% <suffix_number> is computed such that the generated name does
% not collide with an existing file.
path = input_filepath;
[~,file_M0,~] = fileparts(input_filename);
suffix = 0;

while exist(fullfile(path, sprintf("%s_%d", file_M0, suffix)))
    suffix = suffix + 1;
end

output_fullfile = sprintf("%s_%d_%s.%s", file_M0, suffix, suffix_name, extension);
end