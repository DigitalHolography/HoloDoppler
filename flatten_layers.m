function OCT_stack = flatten_layers(OCTdata)
%UNTITLED4 Summary of this function goes here
%   Detailed explanation goes here
% OCT_stack = mat2gray(OCTdata.stack(:, :, :)); 
OCT_stack = mat2gray(OCTdata.stack(:, OCTdata.range_y, 20:150)); 
%OCT_stack = imgaussfilt3(OCT_stack, 3);
% OCT_stack = log(OCT_stack/mean(OCT_stack, "all"));
% M = (OCT_stack > 2);
% OCT_stack(M) = 2;
% OCT_stack(~M) = 1;

% z_profile_matrix = squeeze(OCT_stack(:,2,:));
z_profile_matrix = reshape(log(OCT_stack/mean(OCT_stack, "all")), size(OCT_stack,1)*size(OCT_stack,2), size(OCT_stack, 3));
z_profile_matrix = imgaussfilt(z_profile_matrix, 3);
figure(3)
imagesc(z_profile_matrix);

shifts = calculate_shifts_from_z_profile(permute(z_profile_matrix, [2 1]), permute(z_profile_matrix(:, 1), [2 1]));

z_profile_matrix = reshape(OCT_stack, size(OCT_stack,1)*size(OCT_stack,2), size(OCT_stack, 3));
for ii = 1 : size(OCT_stack,1)*size(OCT_stack,2)
    z_profile_matrix(ii,:) = circshift(z_profile_matrix(ii,:), shifts(ii), 1);
end

OCT_stack = reshape(z_profile_matrix, size(OCT_stack,1), size(OCT_stack,2), size(OCT_stack, 3));

end