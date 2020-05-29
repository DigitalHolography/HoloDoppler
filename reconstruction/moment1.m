function M1 = moment1(SH, f1, f2, fs, batch_size, gw)
%% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batch_size / fs);
n2 = ceil(f2 * batch_size / fs);

% symetric integration interval
n3 = size(SH, 3) - n2 + 1;
n4 = size(SH, 3) - n1 + 1;

f_range = (n1:n2) .* (fs / batch_size);
f_range_sym = (-n2:-n1) .* (fs / batch_size);
SH(:,:,n1:n2) = SH(:,:,n1:n2) .* reshape(f_range, 1, 1, numel(f_range));
SH(:,:,n3:n4) = SH(:,:,n3:n4) .* reshape(f_range_sym, 1, 1, numel(f_range_sym));
moment1 = gather(squeeze(sum(abs(SH(:, :, n1:n2)), 3))) + gather(squeeze(sum(abs(SH(:, :, n3:n4)), 3)));
ms = sum(sum(moment1,1),2);
moment1 = moment1 ./ imgaussfilt(moment1, gw);
ms2 = sum(sum(moment1,1),2);
moment1 = (ms/ms2) * moment1;

M1 = moment1;
end