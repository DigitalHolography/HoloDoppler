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
% tmp = abs(z_profile_matrix - circshift(z_profile_matrix, 3, 2));
% z_profile_matrix = tmp;



%calculate reference profile
Nx = size(OCTdata.stack, 1);
Ny = size(OCTdata.stack, 2);
% ref_OCT_stack = OCTdata.stack(floor(Nx/2) - 1:floor(Nx/2) + 1, floor(Ny/2) - 1:floor(Ny/2) + 1, 16:end);
% ref_profile_matrix = log(reshape(ref_OCT_stack, size(ref_OCT_stack,1)*size(ref_OCT_stack,2), size(ref_OCT_stack, 3))); 
% ref_profile = ref_profile_matrix(1, :);
% 
% for jj = 2 : size(ref_profile_matrix, 1)
%     ref_profile = ref_profile .* (ref_profile_matrix(jj, :));
% end
% 
% ref_profile = mat2gray(ref_profile);
ref_profile = OCTdata.stack(floor(Nx/2), floor(Ny/2), 16:end);

% ref_profile = mat2gray(squeeze, [1 2])));
% ref_profile = imbinarize(ref_profile, 0.7);

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