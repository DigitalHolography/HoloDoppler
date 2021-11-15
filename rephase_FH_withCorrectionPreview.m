function FH = rephase_FH_withCorrectionPreview(FH, coefs)
% Applies a phase to FH computed from rephasing data
zernike_values = ;

[frame_width, frame_height, ~] = size(FH);
[rephasing_zernikes, shack_zernikes, iterative_opt_zernikes] = ...
rephasing_data.aberration_correction.generate_zernikes(frame_width, frame_height);

phase = compute_phase_correction(coefs, zernike_values);
correction = exp(-1i * phase);
FH(:,:,idx_range) = FH(:,:,idx_range) .* correction;
end