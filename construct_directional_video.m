function dir_video = construct_directional_video(M0_pos, M0_neg, temporal_filter_sigma)
[Nx, Ny, ~, num_frames] = size(M0_pos);

sigma = [0.0001 0.0001 temporal_filter_sigma];
M0_pos(:,:,1,:) = imgaussfilt3(squeeze(M0_pos), sigma);
M0_neg(:,:,1,:) = imgaussfilt3(squeeze(M0_neg), sigma);

min_M0 = min(min(M0_pos(:)), min(M0_neg(:)));
max_M0 = max(max(M0_pos(:)), max(M0_neg(:)));

M0_pos = mat2gray(M0_pos, double([min_M0, max_M0]));
M0_neg = mat2gray(M0_neg, double([min_M0, max_M0]));

M0_diff = M0_pos - M0_neg;
sat = abs(M0_diff);
tol = [0.6, 0.999];
sat = 0.7 * imadjustn(sat, stretchlim(sat(:), tol));

M0 = (M0_pos + M0_neg) / 2;
M0 = M0 - mean(mean(M0, 1), 2);
M0 = mat2gray(M0);
M0 = imadjustn(M0, stretchlim(M0(:), [0.02, 0.998]));

dir_video = zeros(Nx, Ny, 3, num_frames, 'single');
for n = 1:num_frames
    img1 = hsv2rgb(1 * ones(Nx, Ny), sat(:,:,n), M0(:,:,n));
    img2 = hsv2rgb(0.66 * ones(Nx, Ny), sat(:,:,n), M0(:,:,n));
    dir_video(:,:,:,n) = img1 .* (M0_diff(:,:,:,n) > 0) + img2 .* (M0_diff(:,:,:,n) < 0);
end

dir_video = mat2gray(dir_video);
% dir_video = im2uint8(dir_video);
end