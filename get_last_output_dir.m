function [found_dir, found] = get_last_output_dir(filepath, filename, file_ext)
% Finds the directory containing the output from last run for a given
% cine file_M0. If no such directory exists, found is set to
% false.

folder_info = dir(filepath);
directory_list = folder_info([folder_info.isdir]);

dir_name_stem = strrep(filename, file_ext, '');

selected_dir = [];
found = false;
for i = 1:numel(directory_list)
    d = directory_list(i).name;
    if contains(d, dir_name_stem)
        if isempty(selected_dir)
            selected_dir = d;
        else
            parts = split(d, '_');
            number = parts(end);
            number = str2num(cell2mat(number));
            parts = split(selected_dir, '_');
            old_number = parts(end);
            old_number = str2num(cell2mat(old_number));

            if number > old_number
                selected_dir = d;
            end
        end
    end
end

found_dir = selected_dir;
end