function output_directory_name = create_output_directory_name(input_filepath, input_filename)
% construct output directory
% name.cine -> name_<suffix_number>
% <suffix_number> is computed such that the generated name does
% not collide with an existing folder.
path = input_filepath;
[~,filename,~] = fileparts(input_filename);
suffix = 0;


while exist(fullfile(path, sprintf("%s_HW_%d", filename, suffix)), 'Dir')
    suffix = suffix + 1;
end

output_directory_name = sprintf("%s_HW_%d", filename, suffix);
end