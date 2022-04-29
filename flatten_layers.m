function OCT_stack = flatten_layers(OCTdata)
%UNTITLED4 Summary of this function goes here
%   Detailed explanation goes here
% OCT_stack = mat2gray(OCTdata.stack(:, :, :)); 
OCT_stack = (OCTdata.stack(:, :, 16:end)); 

% OCT_stack = imgaussfilt3(OCT_stack, 3);
% OCT_stack = log(OCT_stack/mean(OCT_stack, "all"));
% M = (OCT_stack > 2);
% OCT_stack(M) = 2;
% OCT_stack(~M) = 1;

% z_profile_matrix = squeeze(OCT_stack(:,2,:));
z_profile_matrix = reshape(OCT_stack, size(OCT_stack,1)*size(OCT_stack,2), size(OCT_stack, 3));


figure(3)
imagesc(mat2gray(z_profile_matrix));

ref_profile = mat2gray(squeeze(mean(OCTdata.stack(:, OCTdata.range_y(10), 16:end), [1 2])));
ref_profile = imbinarize(ref_profile, 0.7);

z_profile_matrix = permute(z_profile_matrix, [2 1]);
z_profile_video = z_profile_matrix;
z_profile_matrix = imgaussfilt(z_profile_matrix, 2);
shifts = calculate_shifts_from_z_profile(z_profile_matrix, ref_profile);

% z_profile_matrix = reshape(OCTdata.stack(:, OCTdata.range_y, 16:end), size(OCT_stack,1)*size(OCT_stack,2), size(OCT_stack, 3));
for ii = 1 : size(OCT_stack,1)*size(OCT_stack,2)
   z_profile_video(:, ii) = circshift(z_profile_matrix(:, ii), shifts(ii), 1);
end

z_profile_video = permute((z_profile_video), [2 1]);
figure(44)
imagesc(z_profile_video);


OCT_stack = reshape(z_profile_video, size(OCT_stack,1), size(OCT_stack,2), size(OCT_stack, 3));

end