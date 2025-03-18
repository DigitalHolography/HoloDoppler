function H = svd_x_t_filter(H, thresh, f1, fs, NbSubAp)
% SVD filtering of spatial correlation
%
% H: an frame batch already propagated to the distance of reconstruction
% f1: frequency
% fs: sampling frequency
% NbSubAp : number N of subapertures to divide SVD filtering over NxN zones

%%
if ~thresh
    % thresh parameter does not exist or is zero, so default it to something
    thresh = ceil(f1 * size(H, 3) / fs * 2);
end

[width, height, batch_size] = size(H);
Lx = linspace(1, width, NbSubAp + 1);
Ly = linspace(1, height, NbSubAp + 1);

if nargin == 4
    % third parameter does not exist, so default it to something
    thresh = round(f1 * width * height / NbSubAp ^ 2 / fs) * 2 + 1;
end

fprintf('Progress: [');

for ii = 1:NbSubAp

    for kk = 1:NbSubAp
        fprintf('=');
        H1 = H(round(Lx(ii)):round(Lx(ii + 1) - 1), round(Ly(kk)):round(Ly(kk + 1) - 1), :);
        H1 = reshape(H1, (round(Lx(ii + 1)) - round(Lx(ii))) * (round(Ly(kk + 1)) - round(Ly(kk))), batch_size);

        % SVD of spatio-temporal features
        cov = H1 * H1'; % spatial covariance
        [V, S] = eigs(double(cov), thresh); % uses eigs for speed
        [~, sort_idx] = sort(diag(S), 'descend');
        V = V(:, sort_idx);
        H_tissue = (H1' * V(:, 1:thresh) * V(:, 1:thresh)')';
        H1 = reshape(H1 - H_tissue, (round(Lx(ii + 1)) - round(Lx(ii))), (round(Ly(kk + 1)) - round(Ly(kk))), batch_size);
        H(round(Lx(ii)):round(Lx(ii + 1) - 1), round(Ly(kk)):round(Ly(kk + 1) - 1), :) = reshape(H1, (round(Lx(ii + 1)) - round(Lx(ii))), (round(Ly(kk + 1)) - round(Ly(kk))), batch_size);
    end

end

fprintf('] Done!\n');

end
