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

% % TESTS
% figure, hold on
%
% maskArteryChoroid = logical(imread("C:\Users\Michael\Documents\Masks for test\maskArteryChoroid.png"));
% maskVeinChoroid = logical(imread("C:\Users\Michael\Documents\Masks for test\maskVeinChoroid.png"));
% maskBackground = logical(imread("C:\Users\Michael\Documents\Masks for test\maskBackground.png"));
%
% S = SH_shifted .* maskArteryChoroid;
% S = S(:, :, n3:n4);
% CDF = cumsum(S, 3) ./ nnz(maskArteryChoroid); % CDF / NNZ
% meanCDF = squeeze(mean(CDF, [1 2], 'omitnan'));
% plot(f, meanCDF - meanCDF(end))
%
% S = SH_shifted .* maskVeinChoroid;
% S = S(:, :, n3:n4);
% CDF = cumsum(S, 3) ./ nnz(maskVeinChoroid); % CDF / NNZ
% meanCDF = squeeze(mean(CDF, [1 2], 'omitnan'));
% plot(f, meanCDF - meanCDF(end))
%
% S = SH_shifted .* maskBackground;
% S = S(:, :, n3:n4);
% CDF = cumsum(S, 3) ./ nnz(maskBackground); % CDF / NNZ
% meanCDF = squeeze(mean(CDF, [1 2], 'omitnan'));
% plot(f, meanCDF - meanCDF(end))
%
% legend({'Arterial Choroid', 'Venous Choroid', 'Background'}, ...
%     'Location', 'northwest')
% box on, set(gca, 'LineWidth', 2)
% axis([f1, f2, 0, 1])
%
% figure, hold on
%
% S = SH_shifted .* maskArteryChoroid;
% S = S(:, :, n3:n4);
% plot(f, squeeze(sum(S, [1 2]) / nnz(maskArteryChoroid)))
%
% S = SH_shifted .* maskVeinChoroid;
% S = S(:, :, n3:n4);
% plot(f, squeeze(sum(S, [1 2]) / nnz(maskVeinChoroid)))
%
% S = SH_shifted .* maskBackground;
% S = S(:, :, n3:n4);
% plot(f, squeeze(sum(S, [1 2]) / nnz(maskBackground)))
%
% legend({'Arterial Choroid', 'Venous Choroid', 'Background'})
% box on, set(gca, 'LineWidth', 2)
%
% axis padded
% axP = axis;
% axis([f1, f2, axP(3), axP(4)])

end
