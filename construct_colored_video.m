function vid = construct_colored_video(M_freq_low, M_freq_high)
% Constructs a colored video from hologram stacks made with different
% frequency bands
%
% M_freq_low: hologram stack made with a low frequency band
% M_freq_high: hologram stack made with a high frequency band

std_gauss = 3;

M_freq_low = squeeze(M_freq_low);
M_freq_high = squeeze(M_freq_high);

imgaussfilt3(M_freq_low, [1e-4, 1e-4, std_gauss]);
imgaussfilt3(M_freq_high, [1e-4, 1e-4, std_gauss]);

M_freq_low = mat2gray(M_freq_low - mean(mean(M_freq_high, 1), 2));
M_freq_high = mat2gray(M_freq_high - mean(mean(M_freq_high, 1), 2));


tol = [0.2, 0.999];

low_high = stretchlim(M_freq_low(:), tol);
M_freq_low = imadjustn(M_freq_low, low_high);

low_high = stretchlim(M_freq_high(:), tol);
M_freq_high = imadjustn(M_freq_high, low_high);

[Nx, Ny, Nt] = size(M_freq_low);
vid = zeros(Nx,Ny,3,Nt,'single');

alpha1 = [51 255 255]/255;
alpha2 =  [255 51 51]/255;
vid(:,:,1,:) = alpha1(1) * M_freq_low + alpha2(1) * M_freq_high;
vid(:,:,2,:) = alpha1(2) * M_freq_low + alpha2(2) * M_freq_high;
vid(:,:,3,:) = alpha1(3) * M_freq_low + alpha2(3) * M_freq_high;

gamma = 0.8;
low_high = [0 1];
vid = imadjustn(vid, low_high, low_high, gamma);
end