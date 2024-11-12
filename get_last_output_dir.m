function [found_dir, found] = get_last_output_dir(filepath, filename, file_ext)
% Finds the directory containing the output from last run for a given
% cine file_M0. If no such directory exists, found is set to
% false.

dir_name_stem = strrep(filename, file_ext, '');
list_dir = dir(filepath);
idx = 0;
for ii = 1:length(list_dir)
    if contains(list_dir(ii).name, dir_name_stem)
        match = regexp(list_dir(ii).name, '\d+$', 'match');
        if ~isempty(match) && str2double(match{1}) >= idx
            idx = str2double(match{1}) + 1; %suffix
        end
    end
end

if idx == 0
    found = 0;
    found_dir = [];
else
    found = 1;
    found_dir = sprintf('%s_HD_%d', dir_name_stem, idx-1);
end

end