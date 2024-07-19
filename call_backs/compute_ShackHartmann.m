function coefs = compute_ShackHartmann(app, peripheral_flag)
if ~app.file_loaded
    return
end

compute_FH(false);

zernike_ranks = app.shackhartmannzernikeranksEditField.Value;
num_subapertures_positions = app.subapnumpositionsEditField.Value;
image_subapertures_size_ratio = app.imagesubapsizeratioEditField.Value;
subaperture_margin = app.subaperturemarginEditField.Value;
ref_image = app.referenceimageDropDown.Value;
%             zernike_projection = app.ZernikeProjectionCheckBox.Value;

%num_subapertures_inter = 7;

calibration_factor = 60;
corrmap_margin = 0.4;

power_filter_corrector = 1;
sigma_filter_corrector = 1;

% 3D PSF parameters in iterative Shack-Hartmann
m = 128;
defocus_range = 0.05;
num_iter = 1;
iter_phase = zeros(app.Ny, app.Nx, num_iter);
psf_3d = zeros(app.Ny, app.Nx, m);


[~, output_file_name, ~] = fileparts(app.filename);
output_file_name = strcat(output_file_name, '_coefs');
suffix = 0;

while exist(fullfile(app.filepath, sprintf("%s_%d.txt", output_file_name, suffix)), 'file')
    suffix = suffix + 1;
    %                     disp(suffix);
end
output_file_name = sprintf("%s_%d", output_file_name, suffix);

output_file_name = strcat(output_file_name, '.txt');
output_file = fullfile(app.filepath, output_file_name);
disp(output_file);

% select subapertures to exclude, depending on the number
% of subaperture used. This is chosen experimentally, the
% value of the number of subapertures is constrained in the
% GUI so the following switch should always branch to a
% valid choice of excluded_subapertures
%                 switch num_subapertures
%                     case 3
%                         excluded_subapertures = [];
%                     case 4
%                         excluded_subapertures = [1; 4; 13; 16];
%                     case 5
%                         excluded_subapertures = [1; 5; 21; 25];
%                     case 6
%                         excluded_subapertures = [1; 2; 5; 6; 7; 12; 25; 30; 31; 32; 35; 36];
%
%                     case 7
%                         excluded_subapertures = [1; 2; 6; 7; 8; 14; 36; 42; 43; 44; 48; 49];
%                     case 8
%                         excluded_subapertures = [1; 2; 7; 8; 9; 16; 49; 56; 57; 58; 63; 64];
%                     otherwise
%                         error('Unreachable code was reached. Check value of num_subapertures');
%                 end


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
        error('Unreachable code was reached. Check value of num_subapertures');
end

if peripheral_flag
    zernike_indices = 4;
end

shack_hartmann = ShackHartmann(image_subapertures_size_ratio, num_subapertures_positions, zernike_indices, calibration_factor,subaperture_margin,corrmap_margin,power_filter_corrector,sigma_filter_corrector, ref_image);
acquisition = DopplerAcquisition(app.Nx,app.Ny,app.Fs/1000, app.z_reconstruction, app.z_retina, app.z_iris, app.wavelengthEditField.Value, app.DX, app.DY, app.pix_width, app.pix_height);


%                 SubFH = shack_hartmann.SubField(app.FH);




%             num_SubFH_x = floor((app.Nx - shack_hartmann.subimage_size) / shack_hartmann.subimage_stride) + 1;
%             num_SubFH_y = floor((app.Ny - shack_hartmann.subimage_size) / shack_hartmann.subimage_stride) + 1;


num_SubFH_z = 1;

%             shift_cell = cell(1, num_SubFH_z);
coefs = cell(1,num_SubFH_z);
idx_to_freq_coef = acquisition.fs/size(app.FH,3);
layer_freq_thickness = floor(size(app.FH, 3)/2/num_SubFH_z) * idx_to_freq_coef;
[M_aso, StitchedMomentsInMaso] = shack_hartmann.construct_M_aso(app.f1EditField.Value, app.f2EditField.Value,app.blur,acquisition);
%             M_aso = M_aso / (512/shack_hartmann.n_SubAp); %why do we do this?
M_aso = M_aso / (app.Nx/shack_hartmann.n_SubAp); %why do we do this?



%                 M_aso = permute(M_aso, [2 1]);
%                 M_aso = reshape(M_aso, 1, size(M_aso,1), size(M_aso, 2));
%                 M_aso = svd_filter(M_aso, 1, 2);


%                 y = round(384-shack_hartmann.subimage_size/2);
FH = app.FH;
begin = floor(now * 100000);
for iter_idx = 1 : num_iter
    %                 H = ifft2(FH);
    % progress bar
    %                         current_index = (x-1)+(y-1)*num_SubFH_y+1;
    %                         last_index = num_SubFH_x*num_SubFH_y;
    %                         plop = (last_index - current_index) / current_index;
    %                         fprintf("%d / %d (%ds left)\n", current_index, last_index, floor(((now * 100000) - begin) * plop));
    %                         %
    %                         SubH = H(((y - 1) * shack_hartmann.subimage_stride) + 1:((y - 1) * shack_hartmann.subimage_stride) + shack_hartmann.subimage_size, ((x - 1) * shack_hartmann.subimage_stride) + 1:((x - 1) * shack_hartmann.subimage_stride) + shack_hartmann.subimage_size, :);
    %                         SubFH = fft2(SubH);
    SubFH = FH;

    for z = 1:num_SubFH_z
        [shifts, stiched_moments_subap, stiched_corr_subap] = shack_hartmann.compute_images_shifts(SubFH, app.time_transform.f1, app.time_transform.f2, app.blur, false, app.SVDCheckBox.Value, acquisition);
        % Constriction of the matrix of xcorrelations of
        % images in subapertures
        %                             figure;
        %                             imagesc(stiched_corr_subap);
        %                         [~] = shack_hartmann.compute_temporal_SVD_in_SubAp(SubH, app.time_transform.f1, app.time_transform.f2, app.blur, false, app.SVDCheckBox.Value, acquisition);
        shifts = shifts / (app.Nx/shack_hartmann.n_SubAp);
        %                         central_shift = shifts(ceil(length(shifts)/2));
        %                         shifts = shifts - central_shift;
        %                             shift_cell{y, x, z} = shifts;
        %                             disp(shifts);
        %                             disp('-------------');
        % remove corners
        %                                                 excluded_subap = isnan(shifts);
        excluded_subap = shack_hartmann.excluded_subapertures();
        %                         disp(shifts);
        shifts_original = shifts;
        shifts(excluded_subap) = [];
        M_aso_2 = M_aso;
        M_aso_2(excluded_subap, :) = [];
        %                         M_aso_2 = mat_mask(M_aso, excluded_subapertures);
        %                         shifts = mat_mask(shifts, excluded_subapertures);
        %
        % separate x shifts from y shifts
        Y = cat(1, real(shifts), imag(shifts));
        %                         disp(M_aso_2);
        M_aso_concat = cat(1,real(M_aso_2),imag(M_aso_2));
        %

        %                         % solve linear system
        coef = M_aso_concat \ Y;

        coefs{z} = coef * calibration_factor;
    end
    %                 disp(coefs{1, 1, 1});
    %FIXME
    % app.FH = SubFH;
    [FH, iter_phase(:,:,iter_idx)] = rephase_FH_for_preview(FH, coefs, zernike_indices);
end

for iter_idx = 1 : num_iter
    for i = -floor(m/2) + 1 : floor(m/2)
        kernel = propagation_kernelAngularSpectrum(app.Ny, app.Nx, i*(defocus_range/m) , acquisition.lambda, app.pix_width, app.pix_height, 0);
        psf_3d(:,:,i+floor(m/2)) = fftshift(ifft2(iter_phase(:,:,num_iter) .* kernel));
    end
    PSF2D_preview = (abs(squeeze(psf_3d(:,floor(app.Nx/2), :))));
    %figure;
    %imagesc(abs(squeeze(psf_3d(:,floor(app.Nx/2), :))));
    %figure;
    %volshow(abs(psf_3d));
end


%             A = zeros(size(coefs));

%                 disp('-----------------');
%             if app.savecoefsCheckBox.Value
%                 [~, output_file_name, ~] = fileparts(app.filename);
%                 output_file_name = strcat(output_file_name, '_coefs');
%                 suffix = 0;
%                 while exist(fullfile(app.filepath, sprintf("%s_%d.txt", output_file_name, suffix)), 'file')
%                     suffix = suffix + 1;
%                 end
%                 output_file_name = sprintf("%s_%d", output_file_name, suffix);
%                 output_file_name = strcat(output_file_name, '.txt');
%                 output_file = fullfile(app.filepath, output_file_name);
%                 z = 1;
%                 writematrix([size(coefs) shack_hartmann.subimage_size shack_hartmann.subimage_stride], output_file, 'Delimiter', ',');
%                 for pp = 1 : size(coefs{1,1,1}, 1)
%                     for y = 1:size(coefs, 1)
%                         for x = 1:size(coefs, 2)
%                             % pp denotes coeficients, {x,y} the
%                             % position of the sub image
%                             A(x, y) = coefs{y, x, z}(pp);
%                         end
%                     end
%                     writematrix(A, output_file, 'Delimiter', ',', 'WriteMode', 'append');
%                 end
%             end
if ~peripheral_flag

    %                 imshow(mat2gray(stiched_moments_subap), 'Parent', app.UIAxes_3,...
    %                     'XData', [1 app.UIAxes_3.Position(3)], ...
    %                     'YData', [1 app.UIAxes_3.Position(4)]);
    image = stiched_moments_subap;
    if (size(image, 3) == 1)
        image = repmat(image, 1, 1, 3);
    end
    app.ImageRight.ImageSource = image;

    centerY = ceil(size(coefs, 1) / 2);
    centerX = ceil(size(coefs, 2) / 2);
    centerZ = ceil(size(coefs, 3) / 2);
    app.PreviewLabel.Text = sprintf('astig_1 : %0.1f\ndefocus: %0.1f\nastig_2 : %0.1f', coefs{centerY, centerX, centerZ}(1), coefs{centerY, centerX, centerZ}(2), coefs{centerY, centerX, centerZ}(3));

    %Include the correction in the preview using calculated
    % zernike coefficients
    %% FIXME
    %                             shifts_original = M_aso(:,1);
    %             coefs{1} = [4, 0, 0];
    if app.ZernikeProjectionCheckBox.Value
        [app.FH, app.phasePlane] = rephase_FH_for_preview(app.FH, coefs, zernike_indices);
    else
        [~, app.phasePlane] = rephase_FH_for_preview(app.FH, coefs, zernike_indices);
        % alternative rephasing
        phase = stitch_phase(shifts_original, app.phasePlane, app.Nx, app.Ny, shack_hartmann);
        app.FH = app.FH .* exp(-1i.* phase);
    end
    app.show_aberration_correction();
    image_before_correction = app.ImageLeft.ImageSource;
    %                 disp(["entropy of the image before correction :", entropy(image_before_correction)])
end
end

