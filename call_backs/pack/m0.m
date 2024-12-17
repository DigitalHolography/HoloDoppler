function M0 = m0(SH, f1, f2, fs, batch_size, gw)
    % m0 -> moment 0

%% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batch_size / fs);
n2 = ceil(f2 * batch_size / fs);

% symetric integration interval
n3 = size(SH, 3) - n2 + 1;
n4 = size(SH, 3) - n1 + 1;

moment = squeeze(sum(SH(:, :, n1:n2), 3)) + squeeze(sum(SH(:, :, n3:n4), 3));

if gw ~= 0
moment = ff(moment, gw);
end 


M0 = (moment);
end