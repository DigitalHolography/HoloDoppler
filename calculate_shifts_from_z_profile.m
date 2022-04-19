function shifts = calculate_shifts_from_z_profile(z_profile_video, ref_z_profile)
%UNTITLED3 Summary of this function goes here
%   Detailed explanation goes here
Z = zeros(length(ref_z_profile),length(ref_z_profile));
R = repmat(ref_z_profile, 1, length(ref_z_profile));
shifts = zeros(1,size(z_profile_video,2));

for frame = 1 : size(z_profile_video, 2)
    for idx = 1 : length(ref_z_profile)
        Z(:, idx) = circshift(z_profile_video(:,frame), idx);
    end
    C = R .* Z;
    IDX = squeeze(mean(C, 1));
    [~, shifts(frame)] = max(IDX);
end

end