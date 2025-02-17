function H = svd_filter(H, thresh, f1, fs, stride_param)

% SVD filtering
%
% H: an frame batch already propagated to the distance of reconstruction
% threshold : number of firsts components of the svd decomposition removed
% f1 fs : thresh frequency and sampling frequency for default behavior


[iwidth, iheight, batch_size] = size(H); % 'i' for initial

Hi = reshape(H, iwidth*iheight, batch_size);

if ~ thresh
    % thresh parameter does not exist, so default it to something
    thresh = ceil(f1 * batch_size / fs *2 );
end
thresh = max(min(thresh,batch_size),1);
if nargin < 5 || isempty(stride_param)
    % stride_param doesnt exist so default to 1 (full H)
    stride_param = 1;
end


xrange = unique(round(1:stride_param:iwidth));
yrange = unique(round(1:stride_param:iheight));
H = H(xrange,yrange,:); % sub sample H for faster computations

[width, height, ~] = size(H);
H = reshape(H, width*height, batch_size);



% SVD of spatio-temporal features
cov = H'*H;
[V,S] = eig(cov);

[~, sort_idx] = sort(diag(S), 'descend');
V = V(:,sort_idx);
H_tissue = Hi * V(:,1:thresh) * V(:,1:thresh)';
H = reshape(Hi - H_tissue, iwidth, iheight, batch_size);
H = reshape(H, iwidth, iheight, batch_size);


end