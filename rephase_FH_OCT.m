function FH = rephase_FH_OCT(FH, rephasing_data, batch_idx, num_batches)


if isempty(rephasing_data)
    return
end

for rephasing_data = rephasing_data
    shifts = rephasing_data.aberration_correction.rephasing_in_z_coefs;
%     shifts = 180;
    [Nx, Ny, j_win] = size(FH);
    tilt = evaluate_zernikes(1, 1, Nx, j_win);
    phase_3d = ones(size(FH));
    for idx_z = 1 : j_win
        phase_3d(:,:,idx_z) = phase_3d(:,:,idx_z) .* squeeze(tilt(1, idx_z, 1));
    end

    %in the firts approximation if this condition is not verified we are
    %not compensating the movement
    if length(shifts) == num_batches
        phase_3d = shifts(batch_idx) .* phase_3d;
        FH = FH .* exp(1i.*phase_3d);
    end
end
% disp(tilt(1, :, 1))
end