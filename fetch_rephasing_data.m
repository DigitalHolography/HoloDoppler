function [rephasing_data, found] = fetch_rephasing_data(filepath, filename, file_ext)
% check if there is already an output folder for the current
% file_M0. If there is one, load GUI parameters cache from
% exported data
%
% file_ext: '.cine' or '.raw'

[selected_dir, found] = get_last_output_dir(filepath, filename, file_ext);

if ~isempty(selected_dir)
    found = true;
    aberration_correction = load(fullfile(filepath, selected_dir, sprintf('%s.mat', selected_dir)), 'aberration_correction');
    aberration_correction = aberration_correction.aberration_correction;
    cache = load(fullfile(filepath, selected_dir, sprintf('%s.mat', selected_dir)), 'cache');
    cache = cache.cache;
    rephasing_data = RephasingData(cache.batch_size, cache.batch_stride, aberration_correction);
    
    rephasing_data = rephasing_data.compute_frame_ranges();
else
    rephasing_data = [];
end
end