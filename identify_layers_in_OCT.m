function [two_layer_data, layer_idx] = identify_layers_in_OCT(data)
    middle_y = ceil(size(data, 1)/2);
    middle_x = ceil(size(data, 2)/2);
%     middle_z = ceil(size(data, 3)/2);
% %     signal = squeeze(data(middle_y, middle_x, :));
%     % divide signal
    complex_data = data;
    data = sqrt(abs(data).^2);
    offset = floor(size(data, 3)/3);
    signal_1 = data(:,:, 6:offset);
    signal_2 = data(:,:, offset+1:end);
    two_layer_data = zeros(size(data, 1), size(data, 2), 2);
    layer_idx = zeros(size(data, 1), size(data, 2), 2);

    for idy = middle_y - 19 : middle_y + 20
        for idx = middle_x - 19 : middle_x + 20
            [peaks_1, locs_1] = findpeaks(squeeze(signal_1(idy, idx,:)));
            [peaks_2, locs_2] = findpeaks(squeeze(signal_2(idy, idx,:)));

            [~, I1] = sort(peaks_1);
            [~, I2] = sort(peaks_2);

            if ~isempty(I1) && ~isempty(I2)

                idx_RPE = locs_1(I1(end));
                idx_NFL = locs_2(I2(end));

                two_layer_data(idy,idx, 1) = complex_data(idy,idx, idx_RPE);
                two_layer_data(idy,idx, 2) = complex_data(idy,idx, idx_NFL);
                layer_idx(idy,idx, 1) = idx_RPE + 5;
                layer_idx(idy,idx, 2) = idx_NFL + offset;
            end
        end
    end
    
end