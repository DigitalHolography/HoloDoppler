function [img,img_low,img_high] = construct_colored_image(M_freq_low, M_freq_high)
% Constructs a colored image from hologram stacks made with different
% frequency bands
%
% M_freq_low: hologram stack made with a low frequency band
% M_freq_high: hologram stack made with a high frequency band
% is_low_frequency: true if the acquisity was made a low frequency, false
%                   otherwise

M_freq_low = squeeze(M_freq_low);
M_freq_high = squeeze(M_freq_high);

avg_M0_low = mean(M_freq_low, 3);
avg_M0_high = mean(M_freq_high, 3);

avg_M0_low = mat2gray(avg_M0_low);
avg_M0_high = mat2gray(avg_M0_high);

img_low = flipud(interp2(avg_M0_low, 1));
img_high = flipud(interp2(avg_M0_high, 1));

% composite generation
multiband_img = cat(3, img_high, cat(3, img_low, img_low));
DCR_imgs = decorrstretch(multiband_img);
img = DCR_imgs;

end