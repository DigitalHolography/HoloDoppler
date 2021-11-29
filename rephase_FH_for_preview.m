function [FH, phasePlane] = rephase_FH_for_preview(FH, coefs)

%translate coefs to the form of obj.shack_hart... 
%phase = rephasing_data.aberration_correction.compute_total_phase(j,rephasing_zernikes,shack_zernikes,iterative_opt_zernikes);
% 
% [frame_width, frame_height, ~] = size(FH);
% [rephasing_zernikes, shack_zernikes, iterative_opt_zernikes] = ...
%     rephasing_data.aberration_correction.generate_zernikes(frame_width, frame_height);

% app.PreviewLabel.Text = sprintf('astig_1 : %0.1f\ndefocus: %0.1f\nastig_2 : %0.1f', coefs(1), coefs(2), coefs(3));

[frame_width, frame_height, ~] = size(FH);
zernike_indices = [ 3 4 5 ]; %check if this is the correct numeration


[ ~, zern ] = zernike_phase(zernike_indices, frame_width, frame_height);

% figure(1)
% imagesc(zern(:,:,3));

phase = 0;

for i = 1:numel(coefs)
    phase = phase + coefs(i) * zern(:,:,i);
end

phasePlane = phase;
correction = exp(-1i * phase);
FH = FH .* correction;

end