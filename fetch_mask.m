function [mask, found] = fetch_mask(filepath, filename, file_ext)
% check if there is already an output folder for the current
% file_M0. If there is one, load GUI parameters cache from
% exported data
%
% file_ext: '.cine' or '.raw'

[selected_dir, found] = get_last_output_dir(filepath, filename, file_ext);

if ~isempty(selected_dir)
    found = true;
%     disp(fullfile(filepath, selected_dir, 'png', sprintf('%s.png', strcat(selected_dir, '_arteries_mask'))));
    mask = load(fullfile(filepath, selected_dir, 'png', sprintf('%s.png', strcat(selected_dir, '_arteries_mask'))));
else
    mask = [];
end
end