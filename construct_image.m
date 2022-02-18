function img_type_list = construct_image(FH, wavelength, acquisition, gaussian_width, use_gpu, svd, phase_correction,...
                                                                  color_f1, color_f2, color_f3, img_type_list, is_low_frequency , ...
                                                                  spatial_transformation, time_transform, SubAp_PCA)

% FIXME : replace ifs by short name functions

j_win = size(FH, 3);
ac = acquisition;

% move data to gpu if available
if use_gpu
    if exist('phase_correction', 'var')
        phase_correction = gpuArray(phase_correction);
    end
end

if (SubAp_PCA.Value)
    FH = subaperture_PCA(FH, SubAp_PCA, acquisition, svd, f1, f2, gaussian_width);
end

if exist('phase_correction', 'var') && ~isempty(phase_correction)
    FH = FH .* exp(-1i * phase_correction);
end


% if we want dark field preview H is calculated by dark field function
if img_type_list.dark_field_image.select
    %for now we assume that both spatial transforms are the same
    H = dark_field(FH, ac.z_retina, spatial_transformation, ac.z_iris, spatial_transformation, ac.lambda, ac.x_step, ac.y_step);
    
else
    switch spatial_transformation
        case 'angular spectrum'
            H = ifft2(FH);
        case 'Fresnel'
            H = fftshift(ifft2(FH));
    end
end



clear FH;

%% SVD filtering
if svd
    H = svd_filter(H, time_transform.f1, ac.fs);
end

%% Compute moments based on dropdown value
if is_low_frequency
    sign = -1;
else 
    sign = 1;
end


switch time_transform.type
    case 'PCA' % if the time transform is PCA
        SH = short_time_PCA(H);
        n1 = time_transform.f1;
        n2 = time_transform.f2;
    
    case 'FFT' % if the time transform is FFT
        SH = fft(H, [], 3);
        f1 = time_transform.f1;
        f2 = time_transform.f2;
end

% clear("H");
SH = abs(SH).^2;

%% shifts related to acquisition wrong positioning
SH = permute(SH, [2 1 3]);
SH = circshift(SH, [-ac.delta_y, ac.delta_x, 0]);


if img_type_list.pure_PCA.select
    img_type_list.pure_PCA.image = cumulant(SH, n1, n2);
    img_type_list.pure_PCA.image = flat_field_correction(img_type_list.pure_PCA.image, gaussian_width);
end

if img_type_list.dark_field_image.select
    img_type_list.dark_field_image.image = cumulant(SH, f1, f2);
end

if img_type_list.phase_variation.select
    %FIXME : ecraser H
    C = angle(phase_fluctuation(H));
    C = permute(C, [2 1 3]);
    img_type_list.phase_variation.image = moment0(SH, f1, f2, ac.fs, j_win, gaussian_width);
end

if img_type_list.power_Doppler.select % Power Doppler has been chosen
    [img, sqrt_img] = moment0(SH, f1, f2, ac.fs, j_win, gaussian_width);
    img_type_list.power_Doppler.M0_sqrt = sqrt_img;
    img_type_list.power_Doppler.image = img;
end

if img_type_list.power_1_Doppler.select % Power 1 Doppler has been chosen
    img = moment1(SH, f1, f2, ac.fs, j_win, gaussian_width);
    img_type_list.power_1_Doppler.image = img;
end

if img_type_list.power_2_Doppler.select % Power 2 Doppler has been chosen
    img = moment2(SH, f1, f2, ac.fs, j_win, gaussian_width);
    img_type_list.power_2_Doppler.image = img;
end

if img_type_list.color_Doppler.select  % Color Doppler has been chosen
    [M0_neg, M0_pos] = composite(SH, color_f1, color_f2, color_f3, ac.fs, j_win, gaussian_width);
    img_type_list.color_Doppler.M0_pos = M0_pos;
    img_type_list.color_Doppler.M0_neg = M0_neg;
    img_type_list.color_Doppler.image = construct_colored_image(sign * gather(M0_neg), sign * gather(M0_pos), is_low_frequency);
end

if img_type_list.directional_Doppler.select % Directional Doppler has been chosen
    [freq_high, freq_low] = directional(SH, f1, f2, ac.fs, j_win, gaussian_width);
    img_type_list.directional_Doppler.freq_low = freq_low;
    img_type_list.directional_Doppler.freq_high = freq_high;
    img_type_list.directional_Doppler.image = construct_directional_image(sign * gather(freq_high), sign *gather(freq_low), is_low_frequency);
end

if img_type_list.M0sM1r.select % M1sM0r has been chosen
    img = fmean(SH, f1, f2, ac.fs, j_win, gaussian_width);
    img_type_list.M0sM1r.image = img;
end

if img_type_list.velocity_estimate.select % Velocity Estimate has been chosen
   img_type_list.velocity_estimate.image = construct_velocity_video(SH, f1, f2, ac.fs, j_win, gaussian_width, wavelength);
end

end