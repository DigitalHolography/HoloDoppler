function [cdf_freq] = cdf(SH, f1, f2, fs, floor, batchSize)

arguments
    SH
    f1
    f2
    fs
    floor
    batchSize
end

SH = abs(SH);

% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batchSize / fs);
n2 = ceil(f2 * batchSize / fs);

n1 = max(min(n1, ceil(size(SH, 3) / 2)), 1); % -f2
n2 = max(min(n2, ceil(size(SH, 3) / 2)), 1); % -f1

% symetric integration interval
n3 = size(SH, 3) - n2 + 1; % f1
n4 = size(SH, 3) - n1 + 1; % f2

% compute CDF
SH_shifted = fftshift(SH, 3);
S = SH_shifted(:, :, n3:n4);
CDF = cumsum(S, 3) ./ sum(S, 3);

% map CDF to frequencies
f = linspace(f1, f2, length(n3:n4));
idx = sum(CDF < floor, 3) + 1;
cdf_freq = f(idx);

end
