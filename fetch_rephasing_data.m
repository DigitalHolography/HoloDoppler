function [rephasing_data, found] = fetch_rephasing_data(filepath, filename, file_ext)
% check if there is already an output folder for the current
% file_M0. If there is one, load GUI parameters cache from
% exported data
%
% file_ext: '.cine' or '.raw'

[selected_dir, found] = get_last_output_dir(filepath, filename, file_ext);

if ~isempty(selected_dir) && exist(fullfile(filepath, selected_dir, 'mat', sprintf('%s.mat', selected_dir)), "file")

    found = true;
    rephasing_data = load(fullfile(filepath, selected_dir, 'mat', sprintf('%s.mat', selected_dir)), 'rephasing_data');

    if size(rephasing_data)>2

        rephasing_data = rephasing_data.rephasing_data;
        for i = numel(rephasing_data)
            r = rephasing_data(i);
            rephasing_data(i) = r.compute_frame_ranges();
        end

    else
        rephasing_data = [];
    end

else
    rephasing_data = [];
end

end