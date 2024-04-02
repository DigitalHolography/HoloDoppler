function FH = rephase_FH_OCT(FH, rephasing_data, batch_size, frame_offset, num_frames)

if isempty(rephasing_data)
    return
end

for rephasing_data = rephasing_data
    shifts = rephasing_data.aberration_correction.rephasing_in_z_coefs;
    if ~isempty(shifts)
        coefs = zeros(1, num_frames);
        for j = 1 : length(shifts)
            coefs(rephasing_data.frame_ranges(1, j):rephasing_data.frame_ranges(2, j)) = shifts(j);
            if j + 1 < length(shifts)
                coefs(rephasing_data.frame_ranges(2, j): rephasing_data.frame_ranges(1, j + 1)) = (shifts(j) + shifts(j+1))/2;
            end
        end
        coefs(1:rephasing_data.frame_ranges(1, 1)) = shifts(1);
        coefs(rephasing_data.frame_ranges(2, length(shifts)):end) = shifts(end);

        % global idx of first/last frames of current batch
        first_frame_idx = frame_offset + 1;
        last_frame_idx = frame_offset + batch_size;

        shift = squeeze(mean(coefs(first_frame_idx : last_frame_idx)));

        [Nx, ~, j_win] = size(FH);
        tilt = evaluate_zernikes(1, 1, Nx, j_win);
        phase_3d = ones(size(FH));
        for idx_z = 1 : j_win
            phase_3d(:,:,idx_z) = phase_3d(:,:,idx_z) .* squeeze(tilt(1, idx_z, 1));
        end

        phase_3d = shift .* phase_3d;
        FH = FH .* exp(1i.*phase_3d);
    end
end
end