function H_PCA = short_time_PCA(H)

% PCA
[width, height, batch_size] = size(H);
H_l = reshape(H, width * height, batch_size);

% SVD of spatio-temporal features
cov = H_l' * H_l;
[V, D] = eig(cov);
[~, sort_idx] = sort(diag(D), 'descend');
V = V(:, sort_idx);

% figure
% plot(log(diag(D)), '.')
% title('Eigenvalues distribution')
% threshold = round(f1 * batch_size / fs) * 2 + 1;

% selection of eigenvalues
%     X = ones(size(V));
%     X(:, x) = 0;
%     V = V .* X;

%projection of H
H_PCA = H_l * V;
H_PCA = reshape(H_PCA, width, height, batch_size);
end
