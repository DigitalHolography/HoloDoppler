function [img] = construct_colored_image(M0, M_freq_low, M_freq_high)
% Constructs a colored image from hologram stacks made with different
% frequency bands
%
% M_freq_low: hologram stack made with a low frequency band
% M_freq_high: hologram stack made with a high frequency band

[height, width] = size(M0);
Lab = zeros(height, width, 3); % initialize Lab image

% M0 will be used for the L of the Lab colorspace
Lab (:, :, 1) = rescale(M0, 0, 100); % rescale to [0, 100]

% M_freq_low and M_freq_high will be used for the a and b channels, respectively
% Manual rescaling, the mean should be 0 and the range should be at most[-128, 127]

a = M_freq_high;
b = M_freq_low;

mean_a = mean(a(:));
mean_b = mean(b(:));

a_center = a - mean_a;
b_center = b - mean_b;

boundary_a = max(abs(a_center(:)));
boundary_b = max(abs(b_center(:)));

rescaled_a = a_center * 127 / boundary_a; % rescale to [-127, 127]
rescaled_b = b_center * 127 / boundary_b; % rescale to [-127, 127]

Lab (:, :, 2) = rescaled_a - rescaled_b * 0.7; % rescale to [-127, 127]
Lab (:, :, 3) = rescaled_b * 0.3 - rescaled_b; % rescale to [-127, 127]

% composite generation
img = lab2rgb(Lab);

img(img > 255) = 255;
img(img < 0) = 0;
end
