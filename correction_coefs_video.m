function [video_shack, video_iterative] = correction_coefs_video(aberration_correction)
% Generates a video of the variation of the zernike coefficients computed
% over time
%
% aberration_correction: an object of type AberrationCorrection containing
% data to plot

% /!\ this is cringy and utterly slow, but it works

fig = figure(97);
set(fig, 'Visible', 'off');
frame = getframe(fig);
[width, height, ~] = size(frame.cdata);

num_frames = max(size(aberration_correction.shack_hartmann_zernike_coefs, 2),...
                 size(aberration_correction.iterative_opt_zernike_coefs, 2));

if ~isempty(aberration_correction.shack_hartmann_zernike_indices)
    video_shack = zeros(width, height, 3, num_frames);
    
    min_shack = min(aberration_correction.shack_hartmann_zernike_coefs(:));
    max_shack = max(aberration_correction.shack_hartmann_zernike_coefs(:));
    for i = 1:num_frames
        bar(aberration_correction.shack_hartmann_zernike_coefs(:,i));
        ylim([min_shack-1 max_shack+1]);
        current_img = getframe(fig);
        video_shack(:,:,:,i) = current_img.cdata;
    end
else
    video_shack = [];
end

if ~isempty(aberration_correction.iterative_opt_zernike_indices)
    video_iterative = zeros(width, height, 3, num_frames);
    
    min_iterative = min(aberration_correction.iterative_opt_zernike_coefs(:));
    max_iterative = max(aberration_correction.iterative_opt_zernike_coefs(:));
    for i = 1:num_frames
        bar(aberration_correction.iterative_opt_zernike_coefs(:,i));
        ylim([min_iterative-1 max_iterative+1]);
        current_img = getframe(fig);
        video_iterative(:,:,:,i) = current_img.cdata;
    end
else
    video_iterative = [];
end
end