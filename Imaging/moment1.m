function M1 = moment1(SH, f1, f2, fs, batch_size, gw)
SH = abs(SH);

%% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batch_size / fs);
n2 = ceil(f2 * batch_size / fs);

n1 = max(min(n1, size(SH, 3)), 1);
n2 = max(min(n2, size(SH, 3)), 1);

% symetric integration interval
n3 = size(SH, 3) - n2 + 1;
n4 = size(SH, 3) - n1 + 1;

f_range = (n1:n2) .* (fs / batch_size);
f_range_sym = (-n2:-n1) .* (fs / batch_size);

SH(:, :, n1:n2) = SH(:, :, n1:n2) .* reshape(f_range, 1, 1, numel(f_range));
SH(:, :, n3:n4) = SH(:, :, n3:n4) .* reshape(f_range_sym, 1, 1, numel(f_range_sym));

% moment = gather(squeeze(sum(abs(SH(:, :, n1:n2)), 3))) + gather(squeeze(sum(abs(SH(:, :, n3:n4)), 3)));
moment = gather(squeeze(sum(SH(:, :, n1:n2), 3))) + gather(squeeze(sum(SH(:, :, n3:n4), 3)));

% M1 =  flat_field_correction(moment, gw);
% if gw ~= 0
% moment = moment ./ imgaussfilt(moment, gw);
% end
%
M1 = moment;
end
