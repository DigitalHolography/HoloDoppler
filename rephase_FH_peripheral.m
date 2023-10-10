function FH = rephase_FH_peripheral(FH, coefs, zernike_indices)

%translate coefs to the form of obj.shack_hart... 
%phase = rephasing_data.aberration_correction.compute_total_phase(j,rephasing_zernikes,shack_zernikes,iterative_opt_zernikes);
% 
% [frame_width, frame_height, ~] = size(FH);
% [rephasing_zernikes, shack_zernikes, iterative_opt_zernikes] = ...
%     rephasing_data.aberration_correction.generate_zernikes(frame_width, frame_height);

% app.PreviewLabel.Text = sprintf('astig_1 : %0.1f\ndefocus: %0.1f\nastig_2 : %0.1f', coefs(1), coefs(2), coefs(3));
[frame_width, frame_height, ~] = size(FH);
% zernike_indices = [ 3 4 5 ]; %check if this is the correct numeration

[~,zern] = zernike_phase(zernike_indices, size(FH,1) , size(FH,2));
% zern = Zern(floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256, floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256, : );
% figure(1)
% imagesc(zern(:,:,3));

phase = coefs * zern;
correction = exp(-1i * phase);
correction = imresize(correction, [frame_width frame_height]);
FH = FH .* correction;

end