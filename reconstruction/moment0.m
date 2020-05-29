function [M0, sqrt_M0] = moment0(SH, f1, f2, fs, batch_size, gw)
%% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batch_size / fs);
n2 = ceil(f2 * batch_size / fs);

% symetric integration interval
n3 = size(SH, 3) - n2 + 1;
n4 = size(SH, 3) - n1 + 1;

moment = squeeze(sum(abs(SH(:, :, n1:n2)), 3)) + squeeze(sum(abs(SH(:, :, n3:n4)), 3));
ms = sum(sum(moment,1),2);
sqrt_moment = sqrt(moment);

% apply flat field correction
moment = moment ./ imgaussfilt(moment, gw);
sqrt_moment = sqrt_moment ./ imgaussfilt(sqrt_moment, gw);
ms2 = sum(sum(moment,1),2);
moment = (ms / ms2) * moment;

M0 = gather(moment);
sqrt_M0 = gather(sqrt_moment);
end

