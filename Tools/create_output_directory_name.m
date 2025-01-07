function output_directory_name = create_output_directory_name(input_filepath, input_filename)
% construct output directory
% name.cine -> name_<suffix_number>
% <suffix_number> is computed such that the generated name does
% not collide with an existing folder. Suffix will be the last number found + 1.
path = input_filepath;
[~,filename,file_ext] = fileparts(input_filename);

[found_dir, found] = get_last_output_dir(path, filename, file_ext);
if found
    match = regexp(found_dir, '\d+$', 'match'); 
    suffix = str2double(match{1}) + 1;
else
    suffix = 0;
end

output_directory_name = sprintf("%s_HD_%d", filename, suffix);
end