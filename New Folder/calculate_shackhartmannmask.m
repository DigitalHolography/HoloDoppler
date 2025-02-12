function [ShackHartmannMask] = calculate_shackhartmannmask(FH,spatial_transformation,spatial_propagation,ShackHartmannCorrection)

Nx = size(FH,1);
Ny = size(FH,2);

shack_hartmann = ShackHartmann(ShackHartmannCorrection.num_subapertures, ShackHartmannCorrection.num_subapertures_inter, ShackHartmannCorrection.num_zernike_modes, ShackHartmannCorrection.calibration_factor, ShackHartmannCorrection.subaperture_margin, ShackHartmannCorrection.corrmap_margin, ShackHartmannCorrection.power_filter_corrector, ShackHartmannCorrection.sigma_filter_corrector, ShackHartmannCorrection.ref_img);
[M_aso, ~] = shack_hartmann.construct_M_aso(f1, f2, gw, acquisition);
[shifts, ~, ~] = shack_hartmann.compute_images_shifts(FH, f1, f2, gw, false, true, acquisition);

Y = cat(1, real(shifts), imag(shifts));
M_aso_concat = cat(1,real(M_aso),imag(M_aso));

% solve linear system
coefs = M_aso_concat \ Y;

coefs = coefs * shack_hartmann.calibration_factor;


magic_number = 710; % This is the magic number
zernikes = evaluate_zernikes([1 1], [1 -1], Nx, Ny);
zernike_coefs = shifts(:, i);
zernike_coefs(1) = zernike_coefs(1) * magic_number * 2 / Nx;
zernike_coefs(2) = zernike_coefs(2) * magic_number * 2 / Ny;
tilts = zernike_coefs(1) .* zernikes(:,:,1) + zernike_coefs(2) .* zernikes(:,:,2);
ShackHartmannMask = exp(-1i * tilts);
end