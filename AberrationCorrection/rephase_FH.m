function FH = rephase_FH(FH, rephasing_data, batchSize, frame_offset)
% Applies a phase to FH computed from rephasing data

if isempty(rephasing_data)
    return
end

for rephasing_data = rephasing_data
    % select indices of batches in rephasing data that corresponds
    % to current frame batch

    % skip empty rephasing (no correction at all)
    if isempty(rephasing_data.frameRanges)
        continue;
    end

    % global idx of first/last frames of current batch
    first_frame_idx = frame_offset + 1;
    last_frame_idx = frame_offset + batchSize;

    indices1 = find(rephasing_data.frameRanges >= first_frame_idx);
    indices2 = find(rephasing_data.frameRanges <= last_frame_idx);

    [~, J1] = ind2sub(2, indices1);
    [~, J2] = ind2sub(2, indices2);
    J = intersect(J1, J2);

    if isempty(J)
        J = J2(end);
    end

    jstart = min(J);
    jstop = max(J);

    [frame_width, frame_height, ~] = size(FH);
    [rephasing_zernikes, shack_zernikes, iterative_opt_zernikes] = ...
        rephasing_data.aberration_correction.generate_zernikes(frame_width, frame_height);

    for j = jstart:jstop
        % load phase
        phase = rephasing_data.aberration_correction.compute_total_phase(j, rephasing_zernikes, shack_zernikes, iterative_opt_zernikes);

        correction = exp(-1i * phase);

        %FIXME this doesn't need to be in the loop
        % i do not see when this situation could arise
        % compute last frame to apply phase
        if jstop ~= size(rephasing_data.frameRanges, 2)
            last_frame_to_apply_phase_idx = min(rephasing_data.frameRanges(1, jstop + 1) - 1, last_frame_idx);
        else
            last_frame_to_apply_phase_idx = min(rephasing_data.frameRanges(2, jstop), last_frame_idx);
        end

        frameRange = 1:last_frame_to_apply_phase_idx - first_frame_idx + 1;
        range_size = numel(frameRange);
        Nj = jstop - jstart + 1;
        cur_j = j - jstart + 1;
        % apply correction to FH frames
        idxRange = frameRange(ceil((cur_j - 1) * range_size / Nj) + 1:ceil(cur_j * range_size / Nj));
        FH(:, :, idxRange) = FH(:, :, idxRange) .* correction;

        %       if ~isempty(rephasing_data.image_registration(3))
        %           FH = register_in_z_via_phase(FH, rephasing_data.image_registration(3, j));
        %       end
    end

end

end
