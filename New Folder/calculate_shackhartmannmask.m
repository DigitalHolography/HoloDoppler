function [ShackHartmannMask] = calculate_shackhartmannmask(FH, spatial_transformation, spatial_propagation, time_range, fs, gw, ShackHartmannCorrection)
% Calculate the Shack-Hartmann mask based on input parameters

% Extract dimensions of the input field
[Nx, Ny, ~, ~] = size(FH);

% Extract parameters from ShackHartmannCorrection
zernike_ranks = ShackHartmannCorrection.zernikeranks;
num_subapertures_positions = ShackHartmannCorrection.subapnumpositions;
image_subapertures_size_ratio = ShackHartmannCorrection.imagesubapsizeratio;
subaperture_margin = ShackHartmannCorrection.subaperturemargin;
ref_image = ShackHartmannCorrection.referenceimage;

% Define constants
calibration_factor = 60;
corrmap_margin = 0.4;
power_filter_corrector = 1;
sigma_filter_corrector = 1;

% Define Zernike indices based on zernike_ranks
zernike_lookup = {
                  2, [3, 4, 5];
                  3, [3, 4, 5, 6, 7, 8, 9];
                  4, [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14];
                  5, [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20];
                  6, [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
                  };

zernike_indices = [];

for i = 1:size(zernike_lookup, 1)

    if zernike_ranks == zernike_lookup{i, 1}
        zernike_indices = zernike_lookup{i, 2};
        break;
    end

end

if isempty(zernike_indices)
    error('Invalid value for zernike_ranks. Supported values are 2, 3, 4, 5, or 6.');
end

% Initialize Shack-Hartmann object
shack_hartmann = ShackHartmann(image_subapertures_size_ratio, num_subapertures_positions, zernike_indices, calibration_factor, subaperture_margin, corrmap_margin, power_filter_corrector, sigma_filter_corrector, ref_image, spatial_transformation);

% Calculate the shifts
ac.Nx = Nx;
ac.Ny = Ny;
ac.fs = fs;
[shifts, ~, ~] = shack_hartmann.compute_images_shifts(FH, time_range(1), time_range(2), gw, false, true, ac);

% Apply Zernike projection if required
if ShackHartmannCorrection.ZernikeProjection
    % Construct M_aso matrix and solve for Zernike coefficients
    [M_aso, ~] = shack_hartmann.construct_M_aso(time_range(1), time_range(2), gw, []);
    Y = cat(1, real(shifts), imag(shifts));
    M_aso_concat = cat(1, real(M_aso), imag(M_aso));
    coefs = M_aso_concat \ Y;
    coefs = coefs * shack_hartmann.calibration_factor;

    % Display Zernike coefficients
    fprintf("Zernike coefficients:\n");
    disp(coefs);

    % Calculate the phase mask using Zernike polynomials
    [~, zern] = zernike_phase(zernike_indices, Nx, Ny);
    phase = sum(coefs .* permute(zern, [3, 1, 2]), 3); % Sum weighted Zernike polynomials
    ShackHartmannMask = exp(1i * phase); % Convert phase to complex mask
else
    % Stitch phase directly from shifts
    ShackHartmannMask = stitch_phase(shifts, ones(Nx, Ny), Nx, Ny, shack_hartmann);
end

end
