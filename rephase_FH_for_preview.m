function [FH, phasePlane] = rephase_FH_for_preview(FH, coefs, zernike_indices)

%translate coefs to the form of obj.shack_hart... 
%phase = rephasing_data.aberration_correction.compute_total_phase(j,rephasing_zernikes,shack_zernikes,iterative_opt_zernikes);
% 
% [frame_width, frame_height, ~] = size(FH);
% [rephasing_zernikes, shack_zernikes, iterative_opt_zernikes] = ...
%     rephasing_data.aberration_correction.generate_zernikes(frame_width, frame_height);

% app.PreviewLabel.Text = sprintf('astig_1 : %0.1f\ndefocus: %0.1f\nastig_2 : %0.1f', coefs(1), coefs(2), coefs(3));
[n_sub_x, n_sub_y, n_sub_z] = size(coefs);
layer_thickness = floor(size(FH, 3)/2/n_sub_z);
[frame_width, frame_height, ~] = size(FH);
% zernike_indices = [ 3 4 5 ]; %check if this is the correct numeration

[~,Zern] = zernike_phase(zernike_indices, floor(512* sqrt(2)), floor(512* sqrt(2)));
zern = Zern(floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256, floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256, : );
% figure(1)
% imagesc(zern(:,:,3));

for z = 1:n_sub_z
    phase = 0;
    for i = 1:numel(coefs{1,1,1})
        phase = phase + coefs{1,1,z}(i) * zern(:,:,i);
    end
%     disp(coefs{1,1,z}(1))
%     disp(coefs{1,1,z}(2))
%     disp(coefs{1,1,z}(3))
%     disp('--------------')
    phasePlane = phase;
    correction = exp(-1i * phase);
    correction = imresize(correction, [frame_width frame_height]);
    n1 = (z - 1) * layer_thickness + 1;
    n2 = z * layer_thickness;
    n3 = size(FH, 3) - n2;
    n4 = size(FH, 3) - n1;
    FH(:,:,n1:n2) = FH(:,:,n1:n2) .* correction;
    FH(:,:,n3:n4) = FH(:,:,n3:n4) .* correction;
end

end