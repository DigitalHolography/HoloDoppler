function FH = rephase_FH(FH, rephasing_data, batch_size, frame_offset)
% Applies a phase to FH computed from rephasing data

if isempty(rephasing_data)
    return
end

for rephasing_data = rephasing_data
    % select indices of batches in rephasing data that corresponds
    % to current frame batch
    
    % skip empty rephasing (no correction at all)
    if isempty(rephasing_data.frame_ranges)
       continue; 
    end

    % global idx of first/last frames of current batch
    first_frame_idx = frame_offset+1;
    last_frame_idx = frame_offset + batch_size;
    
    indices1 = find(rephasing_data.frame_ranges >= first_frame_idx);
    indices2 = find(rephasing_data.frame_ranges <= last_frame_idx);

    [~,J1] = ind2sub(2, indices1);
    [~,J2] = ind2sub(2, indices2);
    J = intersect(J1,J2);
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
      phase = rephasing_data.aberration_correction.compute_total_phase(j,rephasing_zernikes,shack_zernikes,iterative_opt_zernikes);
      correction = exp(-1i * phase);
      
      % compute last frame to apply phase
      if jstop ~= size(rephasing_data.frame_ranges,2)
        last_frame_to_apply_phase_idx = min(rephasing_data.frame_ranges(1,jstop+1)-1, last_frame_idx);
      else
        last_frame_to_apply_phase_idx = min(rephasing_data.frame_ranges(2,jstop), last_frame_idx);
      end

      frame_range = 1:last_frame_to_apply_phase_idx - first_frame_idx + 1;
      range_size = numel(frame_range);
      Nj = jstop - jstart + 1;
      cur_j = j - jstart + 1;
      % apply correction to FH frames  
      idx_range = frame_range(ceil((cur_j-1)*range_size/Nj)+1:ceil(cur_j*range_size/Nj));
      FH(:,:,idx_range) = FH(:,:,idx_range) .* correction;
    end 
end

end