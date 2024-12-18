function H = svd_filter(H, f1, fs, tresh, stride_param)

% SVD filtering
%
% H: an frame batch already propagated to the distance of reconstruction
% f1: frequency
% fs: sampling frequency[iwidth, iheight, batch_size] = size(H); % 'i' for initial


[iwidth, iheight, batch_size] = size(H); % 'i' for initial

Hi = reshape(H, iwidth*iheight, batch_size);

if nargin < 4
    % third parameter does not exist, so default it to something
    tresh = round(f1 * batch_size / fs)*2 + 1;
end
if nargin < 4
    % tstride_param doesnt exist so default to 1 (full H)
    stride_param = 1;
end


xrange = unique(round(1:stride_param:iwidth));
yrange = unique(round(1:stride_param:iheight));
H = H(xrange,yrange,:); % sub sample H for faster computations
%disp(size(H))

[width, height, ~] = size(H);
H = reshape(H, width*height, batch_size);



% SVD of spatio-temporal features
cov = H'*H;
[V,S] = eig(cov);

[~, sort_idx] = sort(diag(S), 'descend');
V = V(:,sort_idx);
H_tissue = Hi * V(:,1:tresh) * V(:,1:tresh)';
H = reshape(Hi - H_tissue, iwidth, iheight, batch_size);
H = reshape(H, iwidth, iheight, batch_size);


end