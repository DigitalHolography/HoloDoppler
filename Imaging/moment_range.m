function [n1, n2, n3, n4, f_range, f_range_sym] = moment_range(SH, f1, f2, fs, batch_size)
%MOMENT_RANGE Simply get you the n1 n2 n3 n4 index range to filter a
%hyperspectral cube resulting from a Fourier transform on the last
%dimension optionally gives you the frequency ranges
%% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batch_size / fs);
n2 = ceil(f2 * batch_size / fs);

n1 = max(min(n1, ceil(size(SH, 3) / 2)), 1);
n2 = max(min(n2, ceil(size(SH, 3) / 2)), 1);

% symetric integration interval
n3 = size(SH, 3) - n2 + 1;
n4 = size(SH, 3) - n1 + 1;

f_range = (n1:n2) .* (fs / batch_size);
f_range_sym = (-n2:-n1) .* (fs / batch_size);
end
