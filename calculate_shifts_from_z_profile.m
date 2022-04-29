function shifts = calculate_shifts_from_z_profile(z_profile_video, ref_z_profile)
%UNTITLED3 Summary of this function goes here
%   Detailed explanation goes here

shifts = zeros(1,size(z_profile_video,2));
% [min_profile, ~] = min(z_profile_video, [],  2);
% z_profile_video = z_profile_video - min_profile;
% z_profile_video = (z_profile_video > 1);
%% normalize through changing laser intensity
% we assume it is stable during one frame aquisition
for frame = 1 : size(z_profile_video, 2) 
z_profile_video(:, frame) = z_profile_video(:, frame)/ sum(z_profile_video(:, frame), "all");
end

% A = std(z_profile_video, 1, 2);
% mask = (A > median(A,"all"));
% z_profile_video = (z_profile_video .* mask);
figure (1)
imagesc(z_profile_video);
% z_profile_video = z_profile_video > sum(z_profile_video, "all")/nnz(z_profile_video);
% z_profile_video = imbinarize(mat2gray(z_profile_video),0.7);

toc

tic
for frame = 1 : size(z_profile_video, 2) 
    [c, lags] = xcorr(ref_z_profile, z_profile_video(:, frame));
    [~, idx] = max(c);
    shifts(frame) = lags(idx);
end

toc 

for frame = 1 : size(z_profile_video, 2) 
z_profile_video(:, frame) = circshift(z_profile_video(:, frame), shifts(frame), 1);
end

figure (2)
imagesc(z_profile_video);
end