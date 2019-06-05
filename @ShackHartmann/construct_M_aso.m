function M_aso = construct_M_aso(obj, acquisition, gaussian_width, use_gpu)
M_aso = zeros(obj.n_pup^2, obj.n_mode);
ac = acquisition;

for pp = 1:obj.n_mode
    % construct unit zernikes
    A = zeros(obj.n_mode, 1);
    A(pp) = 10;
    [phi,~] = zernike_phase(A, ac.Nx, ac.Ny);
    transmittance = exp(1i*phi);
    shifts = obj.compute_images_shifts(transmittance, true, acquisition, 3, 30, gaussian_width, use_gpu);
    shifts = reshape(shifts, obj.n_pup^2, 1);
    
    % each mode is a col of M_aso
    M_aso(:, pp) = shifts;
end
end