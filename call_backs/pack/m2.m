function M2 = m2(SH, f1, f2, fs, batch_size, gw)
    % m2 -> moment 2

%% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batch_size / fs);
n2 = ceil(f2 * batch_size / fs);

% symetric integration interval
n3 = size(SH, 3) - n2 + 1;
n4 = size(SH, 3) - n1 + 1;

f_range = (n1:n2) .* (fs / batch_size);
f_range_sym = (-n2:-n1) .* (fs / batch_size);

SH(:,:,n1:n2) = SH(:,:,n1:n2) .* reshape(f_range, 1, 1, numel(f_range)).^2;
SH(:,:,n3:n4) = SH(:,:,n3:n4) .* reshape(f_range_sym, 1, 1, numel(f_range_sym)).^2;

moment = squeeze(sum(abs(SH(:, :, n1:n2)), 3)) + ...
    squeeze(sum(abs(SH(:, :, n3:n4)), 3));

if gw ~= 0
moment = ff(moment, gw);
end

M2 = (moment);
end