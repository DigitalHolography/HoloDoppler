function fmean_video = construct_fmean_video(M1sM0r, M0, temporal_filter_sigma)
[Nx, Ny, ~, num_frames] = size(M1sM0r);

hue = M1sM0r - mean(mean(M1sM0r, 1), 2);
hue = mat2gray(-hue);

sigma = [0.0001 0.0001 temporal_filter_sigma];
hue(:,:,1,:) = imgaussfilt3(squeeze(hue), sigma);

tol = [0.0003, 0.999];
hue = 0.66 * imadjustn(hue, stretchlim(hue(:), tol));

sat = mat2gray(M0 - mean(mean(M0, 1), 2));
sat(:,:,1,:) = imgaussfilt3(squeeze(sat), sigma);

val = sat;

tol = [0.005 0.999];
sat = imadjustn(sat, stretchlim(sat(:), tol));

tol = [0.005, 1];
val = imadjustn(val, stretchlim(val(:), tol));

fmean_video = zeros(Nx, Ny, 3, num_frames, 'single');
for n = 1:num_frames
   fmean_video(:,:,:,n) = hsv2rgb(hue(:,:,:,n), sat(:,:,:,n), val(:,:,:,n)); 
end

fmean_video = mat2gray(fmean_video);
tol = [0.005, 0.995];
fmean_video = imadjustn(fmean_video, stretchlim(fmean_video(:), tol));
% fmean_video = im2uint8(fmean_video);
end