function [cdf_freq] = cdf(SH, f1, f2, fs, floor, batch_size)

arguments
    SH
    f1
    f2
    fs
    floor
    batch_size
end

SH = abs(SH);

% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batch_size / fs);
n2 = ceil(f2 * batch_size / fs);

n1 = max(min(n1, ceil(size(SH, 3) / 2)), 1);
n2 = max(min(n2, ceil(size(SH, 3) / 2)), 1);

% symetric integration interval
n3 = size(SH, 3) - n2 + 1;
n4 = size(SH, 3) - n1 + 1;

% compute CDF
S = SH(:, :, n1:n2);
CDF = cumsum(S, 3) ./ sum(S, 3);

% map CDF to frequencies
f = linspace(f1, f2, length(n3:n4));
idx = sum(CDF < floor, 3) + 1;
cdf_freq = f(idx);

end
