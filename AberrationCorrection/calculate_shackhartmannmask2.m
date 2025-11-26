
function [ShackHartmannMask, moment_chunks_crop_array, correlation_chunks_array] = calculate_shackhartmannmask2(FH, Params)
    
    Nx = size(FH, 1);
    Ny = size(FH, 2);
    correlation_chunks_array = [];

    ShackHartmannCorrection = Params.ShackHartmannCorrection;


    zernike_ranks = ShackHartmannCorrection.zernikeranks;
    nsubap = ShackHartmannCorrection.subapnumpositions;
    subap_ratio = ShackHartmannCorrection.imagesubapsizeratio;
    subap_marg = ShackHartmannCorrection.subaperturemargin;
    ref_image = ShackHartmannCorrection.referenceimage;
    only_defocus = 0;
    calibration_factor = 60;

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

    [shifts,moment_chunks_crop_array] = compute_images_shifts(FH, Params, nsubap, subap_ratio);

    if ShackHartmannCorrection.ZernikeProjection % if the phase should be a combination of zernike polynomials
        % Zernike projection
        M_aso = construct_M_aso(nsubap, zernike_indices, Nx, Ny, calibration_factor);
        Y = cat(1, real(shifts), imag(shifts));
        M_aso_concat = cat(1, real(M_aso), imag(M_aso));
        % solve linear system
        coefs = M_aso_concat \ Y;
        coefs = coefs * calibration_factor;
        % Calculate the phase mask finally
        fprintf("Zernike coefficients : \n");
        disp(coefs);

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

function [shifts,moment_chunks_crop_array] = compute_images_shifts(FH, Params, nsubap, subap_ratio)
    % 1 compute images 
    Nx = size(FH,1);
    Ny = size(FH,2);
    Nt = size(FH,3);
    vx = nsubap; % num of SubAp in x direction
    vy = nsubap; % num of SubAp in y direction
    Nxx = floor(Nx / vx * subap_ratio); % size of new SubAp in x Nsub_ap == size ratio n_SubAp_inter == num positions
    Nyy = floor(Ny / vy * subap_ratio); % size of new SubAp in y

    stridex = floor(Nx / vx); % stride x between two SubAp
    stridey = floor(Ny / vy); % stride y between two SubAp
    offsetx = floor(stridex/2); % center of SubAp in x
    offsety = floor(stridey/2); % center of SubAp in y

    moment_chunks_crop_array = zeros(Nx * subap_ratio, Ny * subap_ratio);

    images_mat = zeros(Nyy, Nxx, vx * vy);
    for idy = 1:vy        
        for idx = 1:vx
            
            % Construction of subaperture image
            
            idx_range = (idx-1) * stridex + 1 + offsetx - floor(Nxx/2) : (idx-1) * stridex + 1 + offsetx + floor(Nxx/2);
            idy_range = (idy-1) * stridey + 1 + offsety - floor(Nyy/2) : (idy-1) * stridey + 1 + offsety + floor(Nyy/2);

            idx_range = idx_range(idx_range > 0 & idx_range <= Nx);
            idy_range = idy_range(idy_range > 0 & idy_range <= Ny);
            
            fh = FH(idx_range, idy_range, :);
            % propagate wave

            switch Params.spatial_transformation
                case "angular spectrum"
                    h = ifft2(fh) .* sqrt(Nxx * Nyy);
                case "Fresnel"
                    h = fftshift(fftshift(fft2(fh), 1), 2) ./ sqrt(Nxx * Nyy); %.*obj.PhaseFactor;
                case "twin image removal"
                    h = single(fh);
                case "None"
                    h = single(fh);
            end

            % svd filtering
            [h,~,~] = svd_filter(h, Params.svd_threshold, Params.time_range(1), Params.fs, Params.svd_stride, Params.svd_mean);

            sh_mod = abs(fft(h,[],3)).^2;

            img = moment0(sh_mod, Params.time_range(1), Params.time_range(2), Params.fs, Nt, Params.flatfield_gw);

            if any(size(img) ~= [Nxx, Nyy]) % for edges without the full range
                img = imresize(img, [Nxx, Nyy]);
            end
            
            images_mat(:, :, (idy - 1) * vx + idx) = img';

            idx_range_big = (idx-1) * Nxx + 1 : (idx) * Nxx + 1;
            idy_range_big = (idy-1) * Nyy + 1 : (idy) * Nyy + 1;
            
            moment_chunks_crop_array(idx_range_big, idy_range_big) = imresize(img,[length(idx_range_big),length(idy_range_big)]);
            
        end 
        
    end 

    if strcmp(Params.ShackHartmannCorrection.referenceimage,"central subaperture")
        % use the central image as reference
        reference_image = images_mat(:, :, ceil((vx * vy) / 2));
    else
        reference_image = [];
    end
    
    % calculate the shifts between images and reference image
    shifts = zeros(vx * vy, 1) +  1j*zeros(vx * vy, 1);
    
    for i = 1 : vx * vy
        shift = calculate_image_shift(images_mat(:, :, i), reference_image, Params.registration_disc_ratio); % Here we take registration disc ratio as reticule radius
        shifts(i) = shift;
    end

    % figure, imagesc(reshape(real(shifts),vx,vy));
    % figure, imagesc(reshape(imag(shifts),vx,vy));

end

function shift = calculate_image_shift(img, ref_img, reticule_radius)

    numY = size(img, 2);
    numX = size(img, 1);

    if reticule_radius > 0
        disk_ratio = reticule_radius;
        disk = diskMask(numY, numX, disk_ratio);

        if size(disk, 1) ~= size(img, 1)
            disk = disk';
        end

    else
        disk = ones([numY, numX]);
    end

    img_reg = img .* disk - disk .* sum(img .* disk, [1, 2]) / nnz(disk); % minus the mean in the disc of each frame
    img_reg = img_reg ./ (max(abs(img_reg), [], [1, 2])); % rescaling each frame but keeps mean at zero

    ref_img = ref_img .* disk - disk .* sum(ref_img .* disk, [1, 2]) / nnz(disk); % minus the mean
    ref_img = ref_img ./ (max(abs(ref_img), [], [1, 2])); % rescaling but keeps mean at zero

     [~,shift] = registerImagesCrossCorrelation(img_reg,ref_img);

     shift(1) = shift(1)+numX;
     shift(2) = shift(2)+numY;
     shift = shift(1) + 1i * shift(2); % x + i y
end

function M_aso = construct_M_aso(nsubap, zernike_indices, Nx, Ny, calibration_factor)

    vx = nsubap; % num of SubAp in x direction
    vy = nsubap; % num of SubAp in y direction
    Nxx = floor(Nx / vx); % size of new SubAp in x
    Nyy = floor(Ny / vy); % size of new SubAp in y

    M_aso = zeros(nsubap ^ 2, length(zernike_indices));

    for p = 1:numel(zernike_indices)
        [~, phi] = zernikePhase(zernike_indices(p), Ny, Nx);
        phi = phi * calibration_factor;
        
        shifts_2 = zeros(nsubap, nsubap);

        for idx = 1:vx
            for idy = 1:vy
                tmp_phi = phi * pi;
                range_x = (idx - 1) * Nxx + 1:idx * Nxx;
                range_y = (idy - 1) * Nyy + 1:idy * Nyy;
                chunk = tmp_phi(range_y, range_x);
                [FX, FY] = gradient(chunk, (2 * pi) / (Nx), (2 * pi) / (Ny));
                fx = sum(FX,"all")/nnz(FX);
                fy = sum(FY,"all")/nnz(FY);
                shifts_2(idx, idy) = -(fy + 1i * fx) / nsubap / pi;
            end

        end

        shifts = reshape(shifts_2, [nsubap * nsubap 1]);
        M_aso(:, p) = shifts;
    end
end