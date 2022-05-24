function [M_aso,StitchedMomentsInMaso] = construct_M_aso(obj, f1, f2, gw, acquisition)
ac = acquisition;


M_aso = zeros(obj.n_SubAp^2, numel(obj.modes));
StitchedMomentsInMaso = zeros(512,512, numel(obj.modes)); %Stitched PowerDoppler moments in each subaperture


for p = 1:numel(obj.modes)
%     [~,phi] = zernike_phase(obj.modes(p), 512, 512);
    [~,Phi] = zernike_phase(obj.modes(p), floor(512* sqrt(2)), floor(512* sqrt(2)));
    phi = Phi(floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256, floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256 );
    phi = phi*obj.calibration_factor;
    transmittance = exp(1i*phi);
    figure;
    imagesc(angle(transmittance));
    [shifts, StichedMomentsInSubapertures] = obj.compute_images_shifts(transmittance, f1, f2, gw, true, false, ac);
    
    % each mode is a col of M_aso
    M_aso(:,p) = shifts;
    StitchedMomentsInMaso(:,:,p) = StichedMomentsInSubapertures;
end

end