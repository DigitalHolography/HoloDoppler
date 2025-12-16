
function [ShackHartmannMask, moment_chunks_crop_array, correlation_chunks_array] = calculate_shackhartmannmask2(FH, Params)
   
    
    FH = (FH); % extract central to get a square only
   
    ShackHartmannCorrection = Params.ShackHartmannCorrection;
    if ShackHartmannCorrection.iterate
        IterShackHartmannMask = ones(Nx,Ny)+1j*zeros(Nx,Ny); % init the phase mask to zero phase
        for ii = 1:ShackHartmannCorrection.N_iterate
            FH = FH .* IterShackHartmannMask;
            [ShackHartmannMask, moment_chunks_crop_array, correlation_chunks_array, coefs] = calculate_shackhartmannmask_once(FH, Params);
            IterShackHartmannMask = IterShackHartmannMask .* ShackHartmannMask;
        end
        ShackHartmannMask = IterShackHartmannMask;
    else
        [ShackHartmannMask, moment_chunks_crop_array, correlation_chunks_array] = calculate_shackhartmannmask_once(FH, Params);
    end

end

function [ShackHartmannMask, moment_chunks_crop_array, correlation_chunks_array, coefs] = calculate_shackhartmannmask_once(FH, Params)
    Nx = size(FH, 1);
    Ny = size(FH, 2);
    correlation_chunks_array = [];

    ShackHartmannCorrection = Params.ShackHartmannCorrection;


    zernike_ranks = ShackHartmannCorrection.zernikeranks;
    nsubap = ShackHartmannCorrection.subapnumpositions;
    subap_ratio = ShackHartmannCorrection.imagesubapsizeratio;
    ref_image = ShackHartmannCorrection.referenceimage;
    only_defocus = ShackHartmannCorrection.onlydefocus;
    calibration_factor = ShackHartmannCorrection.calibrationfactor;

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

    figure, imagesc(real(shifts))

    shifts = reshape(shifts,1,[]);

    

    if ShackHartmannCorrection.ZernikeProjection % if the phase should be a combination of zernike polynomials
        % Zernike projection
        M_aso = construct_M_aso(Nx, Ny, zernike_indices, nsubap, nsubap);
        Y = cat(2, real(shifts), imag(shifts))';

        for k=1:size(M_aso,4)
            M_aso_concat(:,k) = cat(2, reshape(M_aso(1,:,:,k),1,[]),reshape(M_aso(2,:,:,k),1,[]));
        end

        % solve linear system
        coefs = M_aso_concat \ Y;
        % Calculate the phase mask finally
        fprintf("Zernike coefficients : \n");
        if only_defocus
            disp(coefs(2));
        else
            disp(coefs);
        end

        [~, zern] = zernikePhase(zernike_indices, Nx, Ny, 2 ); % Radius to 2 = full field no diaphragm
        phase = 0;
        
        if only_defocus
            phase = coefs(2) * zern(:, :, 2);
        else
            for i = 1:numel(coefs)
                phase = phase + coefs(i) * zern(:, :, i);
            end
        end

        ShackHartmannMask = exp(1i * phase);

    else
        warning("Being changed");
        ShackHartmannMask = ones(Nx,Ny)+1j*zeros(Nx,Ny);
    end

end


function [shifts,moment_chunks_crop_array] = compute_images_shifts(FH, Params, nsubap, subap_ratio)
    % 1 compute images 
    Nx = size(FH,1);
    Ny = size(FH,2);
    Nt = size(FH,3);
    vx = nsubap; % num of SubAp in x direction
    vy = nsubap; % num of SubAp in y direction
    kx = subap_ratio; % num of overlapping sub ap between two sub aps
    ky = subap_ratio; % num of overlapping sub ap between two sub aps

    Nxx = floor(Nx / vx); % size of new SubAp in x Nsub_ap 
    Nyy = floor(Ny / vy );

    stridex = floor(Nx / (vx*kx) ); % stride x between two SubAp
    stridey = floor(Ny / (vy*ky) ); % stride y between two SubAp

    offsetx = floor(stridex/2); % center of SubAp in x
    offsety = floor(stridey/2); % center of SubAp in y

    moment_chunks_crop_array = zeros(Nx * subap_ratio, Ny * subap_ratio);

    images_mat = zeros(Nyy, Nxx, vx * vy);
    for idy = 1:((vy-1)*ky+1)        
        for idx = 1:((vx-1)*kx+1)
            
            % Construction of subaperture image
            
            idx_range = (idx-1) * stridex + 1 + offsetx - floor(Nxx/2) : (idx-1) * stridex + 1 + offsetx + floor(Nxx/2);
            idy_range = (idy-1) * stridey + 1 + offsety - floor(Nyy/2) : (idy-1) * stridey + 1 + offsety + floor(Nyy/2);

            idx_range = idx_range(idx_range > 0 & idx_range <= Nx);
            idy_range = idy_range(idy_range > 0 & idy_range <= Ny);
            
            fh = pad3DToSquare(FH(idx_range, idy_range, :));
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
    shifts = zeros(vx, vy) +  1j*zeros(vx, vy);
    
    for i = 1 : vx 
        for j = 1 : vy
            shift = calculate_image_shift(images_mat(:, :, i), reference_image, Params.registration_disc_ratio); % Here we take registration disc ratio as reticule radius
            shifts(i,j) = shift;
        end
    end

    % figure, imagesc(reshape(real(shifts),vx,vy));
    % figure, imagesc(reshape(imag(shifts),vx,vy));

end

function shift = calculate_image_shift(img, ref_img, reticule_radius)

    numY = size(img, 2);
    numX = size(img, 1);

    p1 = prctile(img(:), 1);
    p99 = prctile(img(:), 99);
    img = min(max(img, p1), p99);

    p1r = prctile(ref_img(:), 1);
    p99r = prctile(ref_img(:), 99);
    ref_img = min(max(ref_img, p1r), p99r);

    if reticule_radius > 0
        disk_ratio = reticule_radius;
        disk = diskMask(numY, numX, disk_ratio);
        if size(disk, 1) ~= size(img, 1)
            disk = disk';
        end
    else
        disk = ones([numY, numX]);
    end

    img_reg = img .* disk - disk .* sum(img .* disk, [1, 2]) / nnz(disk);
    img_reg = img_reg ./ max(abs(img_reg), [], [1, 2]);

    ref_img = ref_img .* disk - disk .* sum(ref_img .* disk, [1, 2]) / nnz(disk);
    ref_img = ref_img ./ max(abs(ref_img), [], [1, 2]);

    [~, shift] = registerImagesCrossCorrelationSubPix(img_reg, ref_img);

     shift = shift(1) + 1i * shift(2);
end


function M = construct_M_aso(Nx, Ny, mode_indices, sub_nx, sub_ny, dx, dy)

    if nargin < 6
        dx = 1;
        dy = 1;
    end

    n_modes = numel(mode_indices);
    M = zeros(2, sub_ny, sub_nx, n_modes);

    for k = 1:n_modes
        Z = zernikePhase(mode_indices(k), Ny, Nx);

        [dZdx,dZdy] = gradient(Z, dx, dy);

        for iy = 1:sub_ny
            for ix = 1:sub_nx
                y_start = (iy - 1) * floor(Ny / sub_ny) + 1;
                y_end   = y_start + floor(Ny / sub_ny) - 1;
                x_start = (ix - 1) * floor(Nx / sub_nx) + 1;
                x_end   = x_start + floor(Nx / sub_nx) - 1;

                dZdx_sub = dZdx(y_start:y_end, x_start:x_end);
                dZdy_sub = dZdy(y_start:y_end, x_start:x_end);

                dZdx_avg = mean(dZdx_sub, "all", "omitnan");
                dZdy_avg = mean(dZdy_sub, "all", "omitnan");

                M(:, iy, ix, k) = [dZdx_avg; dZdy_avg];
            end
        end
    end
end
