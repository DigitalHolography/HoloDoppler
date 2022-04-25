function shifts = calculate_shifts_from_z_profile(z_profile_video, ref_z_profile)
%UNTITLED3 Summary of this function goes here
%   Detailed explanation goes here

shifts = zeros(1,size(z_profile_video,2));
% [min_profile, ~] = min(z_profile_video, [],  2);
% z_profile_video = z_profile_video - min_profile;
% z_profile_video = (z_profile_video > 1);

A = std(z_profile_video, 1, 2);
mask = (A > 0.01);
z_profile_video = (z_profile_video .* mask);
figure (1)
imagesc(z_profile_video);
z_profile_video = z_profile_video > (1.1 * sum(z_profile_video, "all")/nnz(z_profile_video));
Z = zeros(size(z_profile_video, 1));
R = repmat(z_profile_video(:, 1), 1, size(z_profile_video, 1));


for frame = 1 : size(z_profile_video, 2) 
%     [c, lags] = xcorr(ref_z_profile, z_profile_video(:, frame));
%     [~, idx] = max(c);
    for csh = 1 : size(z_profile_video, 1)
        Z(:, csh) = circshift(z_profile_video(:, frame), csh);
    end
    C = R.* Z;
    IDX = sum(C, 1);
    [~, idx] = max(IDX);
    shifts(frame) = idx;
end

for frame = 1 : size(z_profile_video, 2) 
z_profile_video(:, frame) = circshift(z_profile_video(:, frame), shifts(frame), 1);
end

figure (2)
imagesc(z_profile_video);
end