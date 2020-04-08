function [M_aso,StitchedMomentsInMaso] = construct_M_aso(obj, f1, f2, gw, acquisition)
ac = acquisition;

M_aso = zeros(obj.n_SubAp^2, numel(obj.modes));
StitchedMomentsInMaso = zeros(ac.Nx,ac.Ny, numel(obj.modes)); %Stitched PowerDoppler moments in each subaperture

for p = 1:numel(obj.modes)
    [~,phi] = zernike_phase(obj.modes(p), ac.Nx, ac.Ny);
    phi = phi*obj.calibration_factor;
    transmittance = exp(1i*phi);
    
    [shifts, StichedMomentsInSubapertures] = obj.compute_images_shifts(transmittance, f1, f2, gw, true, false, ac);
    
    % each mode is a col of M_aso
    M_aso(:,p) = shifts;
    StitchedMomentsInMaso(:,:,p) = StichedMomentsInSubapertures;
end

end