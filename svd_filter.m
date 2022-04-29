function H = svd_filter(H, f1, fs)
% SVD filtering
%
% H: an frame batch already propagated to the distance of reconstruction
% f1: frequency
% fs: sampling frequency
[width, height, batch_size] = size(H);
H = reshape(H, width*height, batch_size);


threshold = round(f1 * batch_size / fs)*2 + 1;

% SVD of spatio-temporal features
cov = H'*H;
[V,S] = eig(cov);
[~, sort_idx] = sort(diag(S), 'descend');
V = V(:,sort_idx);
H_tissue = H * V(:,1:threshold) * V(:,1:threshold)';
% H = reshape(H - H_tissue, width, height, batch_size);
H = reshape(H_tissue, width, height, batch_size);
end