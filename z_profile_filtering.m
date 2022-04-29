function SH = z_profile_filtering(SH)
%you cannot do this filtering while including the frequency 0 because it
%dominates over everything



% FSH = fft(SH(:,:,16:end), [], 3);
%this works very well for finding the layers but it works on a full image
%this is not what we want, or maybe it can work very well but when we have 
z_profile_matrix = reshape(SH, 1,  size(SH,1)*size(SH,2), size(SH, 3));
z_profile_matrix = permute(z_profile_matrix, [1 3 2]);
size(z_profile_matrix, 3)
for ii = 1 : 20000
    z_profile_matrix(:, :, ii) = svd_filter(z_profile_matrix(:, :, ii), 50, 500);
end
z_profile_matrix = permute(z_profile_matrix, [1 3 2]);
SH = reshape(z_profile_matrix, size(SH,1), size(SH,2), size(SH, 3));
% FSH(:,:,220:end) = 0;
% SH = abs(ifft(FSH, [], 3));

% plot(squeeze(log(mean(abs(PCA_SH), [1 2]))));
% plot(squeeze(squeeze(abs(FSH(250, 25, :)))));

end