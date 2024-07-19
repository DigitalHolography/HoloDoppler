function [M_aso,StitchedMomentsInMaso] = construct_M_aso(obj, f1, f2, gw, acquisition)
ac = acquisition;


% M_aso = zeros(obj.n_SubAp^2, numel(obj.modes));
M_aso = zeros((obj.n_SubAp_inter^2), numel(obj.modes));
StitchedMomentsInMaso = zeros(512,512, numel(obj.modes)); %Stitched PowerDoppler moments in each subaperture


for p = 1:numel(obj.modes)
    [~,phi] = zernike_phase(obj.modes(p), 512, 512);
%     s = floor(512* sqrt(2));
%     [~,Phi] = zernike_phase(obj.modes(p), s, s);
%     phi = Phi(floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256, floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256 );
    phi = phi*obj.calibration_factor;
%     transmittance = (exp(1i*phi));

    Nxx = 512;
    num_subap = obj.n_SubAp_inter;

    size_subap = floor(Nxx/num_subap);

    mask = ~(phi~=0);
    mask = imgaussfilt(double(mask), 5);
    mask = (mask==0);
    shifts_2 = zeros(num_subap, num_subap);
    for idx = 1 : num_subap
        for idy = 1 : num_subap
            tmp_phi = phi.*3.14;
            range_x = (idx - 1) * size_subap + 1 : idx * size_subap;
            range_y = (idy - 1) * size_subap + 1 : idy * size_subap;
            chunk = tmp_phi(range_y, range_x);
            chunk_mask = mask(range_y, range_x);
            [FX,FY] = gradient(chunk, (2*3.14)/(512));
            FX = FX .*chunk_mask;
            FY = FY .*chunk_mask;
            fx = sum(FX, 'all')/nnz(chunk_mask);
            fy = sum(FY, 'all')/nnz(chunk_mask);
            shifts_2(idx, idy) = -(fy + 1i.*fx)/512 * (512/num_subap) / 3.14;
%             shifts_2(idx, idy) = shifts_2(idx, idy)/(512/num_subap)*512;
        end
    end
    shifts = reshape(shifts_2, [num_subap * num_subap 1]);

%     if p == 1
%         figure;
%         imagesc(angle(transmittance));
%     end
%      [~] = obj.compute_SVD_for_SubAp(transmittance, f1, f2, gw, true, false, ac);
%     [shifts, StichedMomentsInSubapertures] = obj.compute_images_shifts(transmittance, f1, f2, gw, true, false, ac);
    
    % each mode is a col of M_aso
    M_aso(:,p) = shifts;
%     StitchedMomentsInMaso(:,:,p) = StichedMomentsInSubapertures;
end

end