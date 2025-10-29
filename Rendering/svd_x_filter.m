function [H, C, bigU] = svd_x_filter(H, thresh, f1, fs, NbSubAp)
% SVD filtering
%
% H: an frame batch already propagated to the distance of reconstruction
% f1: frequency
% fs: sampling frequency
% NbSubAp : number N of subapertures to divide SVD filtering over NxN zones

if ~thresh
    % thresh parameter does not exist or is zero, so default it to something
    thresh = ceil(f1 * size(H, 3) / fs * 2);
end

[width, height, batch_size] = size(H);
Lx = linspace(1, width, NbSubAp + 1);
Ly = linspace(1, height, NbSubAp + 1);

if nargin == 4
    % third parameter does not exist, so default it to something
    thresh = round(f1 * batch_size / fs / NbSubAp) * 2 + 1;
end

C = zeros([width, height], 'single');
bigU = zeros([width, height, 2], 'single');

for ii = 1:NbSubAp

    for kk = 1:NbSubAp
        H1 = H(round(Lx(ii)):round(Lx(ii + 1) - 1), round(Ly(kk)):round(Ly(kk + 1) - 1), :);
        H1 = reshape(H1, (round(Lx(ii + 1)) - round(Lx(ii))) * (round(Ly(kk + 1)) - round(Ly(kk))), batch_size);

        % SVD of spatio-temporal features
        cov = H1' * H1;
        [V, S] = eig(cov);
        [~, sort_idx] = sort(diag(S), 'descend');
        V = V(:, sort_idx);
        H_tissue = H1 * V(:, 1:thresh) * V(:, 1:thresh)';

        if nargout > 1 % just in case you want to see what is filtered
            sz = [(round(Lx(ii + 1)) - round(Lx(ii))), (round(Ly(kk + 1)) - round(Ly(kk)))];
            C(round(Lx(ii)):round(Lx(ii + 1) - 1), round(Ly(kk)):round(Ly(kk + 1) - 1)) = imresize(abs(cov), sz);
            U = reshape(H1 * V(:, 1:thresh), sz(1), sz(2), []);
            bigU(round(Lx(ii)):round(Lx(ii + 1) - 1), round(Ly(kk)):round(Ly(kk + 1) - 1), 2) = imresize(abs(U(:, :, 1)), sz);
            bigU(round(Lx(ii)):round(Lx(ii + 1) - 1), round(Ly(kk)):round(Ly(kk + 1) - 1), 2) = imresize(mean(abs(U(:, :, 2:end)), 3), sz);
        end

        H1 = reshape(H1 - H_tissue, (round(Lx(ii + 1)) - round(Lx(ii))), (round(Ly(kk + 1)) - round(Ly(kk))), batch_size);
        H(round(Lx(ii)):round(Lx(ii + 1) - 1), round(Ly(kk)):round(Ly(kk + 1) - 1), :) = reshape(H1, (round(Lx(ii + 1)) - round(Lx(ii))), (round(Ly(kk + 1)) - round(Ly(kk))), batch_size);

    end

end

end
