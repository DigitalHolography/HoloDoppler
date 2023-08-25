function FH = SVD_tests(FH)
%% set parameters
n1 = 30;
n2 = 256;
gaussian_width = 35;

Nz = size(FH, 3);
Nx = size(FH, 1);
Ny = size(FH, 2);


eigen_list_FH = ones(size(FH, 3),1);
eigen_list_subFH = ones(size(FH, 3),1);

eigen_list_SFH = ones(size(FH, 3),1);
eigen_list_subSFH = ones(size(FH, 3),1);
eigen_list_SFH(10:end) = 0;
eigen_list_subSFH(1) = 0;

eigen_list_H = ones(size(FH, 3),1);
% eigen_list_H(1:5) = 0;
% eigen_list_H(10:end) = 0;
eigen_list_subH = ones(size(FH, 3),1);

eigen_list_SH = ones(size(FH, 3),1);
eigen_list_SH(2:end) = 0;
eigen_list_subSH = ones(size(FH, 3),1);
eigen_list_subSH(10:end) = 0;

%% 1. FH
%% 2. SFH
% SFH = fft(FH, [], 3);
% A = reshape(SFH, [Nx*Ny Nz]);
% [A, T, ~] = my_svd_filter(A', eigen_list_SFH);
% SFH = reshape(A', [Nx Ny Nz]);

% figure(401)
% for i = 1 : 4
%     chunk = reshape(T(:, i), 1, Nz);
%     chunk = log(abs(chunk));
%     % chunk = permute(chunk, [2 1 3]);
% %     [img, ~] = moment0(chunk, n1, n2, 512, size(FH, 3), gaussian_width);
%     img = chunk;
%     subplot(2, 2, i)
%     %imagesc(img)
%     plot(chunk);
%     %colormap gray
%     axis square
%     axis on
% end

% FH = ifft(SFH, [], 3);
% %% 3. H
H = ifft2(FH);
% A = reshape(H, [Nx*Ny Nz]);
% [A, ~, ~] = my_svd_filter(A, eigen_list_H);
% H = reshape(A, [Nx Ny Nz]);
%% 4. SH
% SFH = SubAp_filtering(SFH, 5, true, false, eigen_list_subSFH, n1, n2, gaussian_width);
% SH = ifft2(SFH);
SH = fft(H, [], 3);
% SH = abs(SH);
SH = movmean(SH, 3, 3);
% %SH = imgaussfilt3(SH, 2);
A = reshape(SH, [Nx*Ny Nz]);
[A, T, ~] = my_svd_filter(A', eigen_list_SH);
SH = reshape(A', [Nx Ny Nz]);

figure(401)
for i = 1 : 4
    chunk = reshape(T(:, i), Nz, 1);
%     chunk = (abs(chunk).^2);
    chunk = abs(chunk);
%     chunk = permute(chunk, [2 1 3]);
    % [img, ~] = moment0(chunk, n1, n2, 512, size(FH, 3), gaussian_width);
    img = chunk;
    subplot(2, 2, i)
    plot(img)
%     imagesc(img)
%     colormap gray
    axis square
%     axis off
end

SH_filtered = SH;

%% 5. image reconstruction
SH_filtered = abs(SH_filtered);
SH_filtered = permute(SH_filtered, [2 1 3]);
[img, sqrt_img] = moment0(SH_filtered, 1, 512, 512, size(FH, 3), gaussian_width);

figure(504)
imagesc(flip(img))
colormap gray
axis square
axis off

end