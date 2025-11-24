function [ShackHartmannMask, moment_chunks_crop_array, correlation_chunks_array] = calculate_shackhartmannmask(FH, spatial_transformation, spatial_propagation, time_range, fs, gw, ShackHartmannCorrection)

    Nx = size(FH, 1);
    Ny = size(FH, 2);

    zernike_ranks = ShackHartmannCorrection.zernikeranks;
    num_subapertures_positions = ShackHartmannCorrection.subapnumpositions;
    image_subapertures_size_ratio = ShackHartmannCorrection.imagesubapsizeratio;
    subaperture_margin = ShackHartmannCorrection.subaperturemargin;
    ref_image = ShackHartmannCorrection.referenceimage;

    calibration_factor = 60;
    corrmap_margin = 0.4;

    power_filter_corrector = 1;
    sigma_filter_corrector = 1;

    % 3D PSF parameters in iterative Shack-Hartmann (unused i think)
    % m = 128;
    % defocus_range = 0.05;
    % num_iter = 1;
    % iter_phase = zeros(Ny, Nx, num_iter);
    % psf_3d = zeros(app.Ny, app.Nx, m);

    switch zernike_ranks
        case 2
            zernike_indices = [3 4 5];
        case 3
            zernike_indices = [3 4 5 6 7 8 9];
        case 4
            zernike_indices = [3 4 5 6 7 8 9 10 11 12 13 14];
        case 5
            zernike_indices = [3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20];
        case 6
            zernike_indices = [3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27];
        otherwise
            error('Unreachable code was reached. Check value of zernike_ranks');
    end

    shack_hartmann = ShackHartmann(image_subapertures_size_ratio, num_subapertures_positions, zernike_indices, calibration_factor, subaperture_margin, corrmap_margin, power_filter_corrector, sigma_filter_corrector, ref_image, spatial_transformation);
    shack_hartmann.Nx = Nx;
    shack_hartmann.Ny = Ny;
    % Calculate the shifts
    ac.Nx = Nx;
    ac.Ny = Ny;
    ac.fs = fs;
    [shifts, moment_chunks_crop_array, correlation_chunks_array] = shack_hartmann.compute_images_shifts(FH, time_range(1), time_range(2), gw, false, true, ac);

    if ShackHartmannCorrection.ZernikeProjection % if the phase should be a combination of zernike polynomials
        % Zernike projection
        [M_aso, ~] = shack_hartmann.construct_M_aso(time_range(1), time_range(2), gw, []);
        Y = cat(1, real(shifts), imag(shifts));
        M_aso_concat = cat(1, real(M_aso), imag(M_aso));
        % solve linear system
        coefs = M_aso_concat \ Y;
        coefs = coefs * shack_hartmann.calibration_factor;
        % Calculate the phase mask finally
        fprintf("Zernike coefficients : \n");
        disp(coefs);
        [n_sub_x, n_sub_y, n_sub_z] = size(coefs);

        [~, zern] = zernikePhase(zernike_indices, Nx, Ny ,2); % Radius to 2 = full field no diaphragm
        phase = 0;

        for i = 1:numel(coefs)
            phase = phase + coefs(i) * zern(:, :, i);
        end

        ShackHartmannMask = exp(1i * phase);

    else
        ShackHartmannMask = exp(1i *-stitch_phase(shifts, ones(Nx, Ny), Nx, Ny, shack_hartmann));
    end

end
