function [energy_ratio] = energy_ratio(SH, f1, f2, fi1, fi2, fs, batch_size)

arguments
    SH
    f1
    f2
    fi1
    fi2
    fs
    batch_size
end

SH = abs(SH);

% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batch_size / fs);
n2 = ceil(f2 * batch_size / fs);
ni1 = ceil(fi1 * batch_size / fs);
ni2 = ceil(fi2 * batch_size / fs);

n1 = max(min(n1, ceil(size(SH, 3) / 2)), 1);
n2 = max(min(n2, ceil(size(SH, 3) / 2)), 1);
ni1 = max(min(ni1, ceil(size(SH, 3) / 2)), 1);
ni2 = max(min(ni2, ceil(size(SH, 3) / 2)), 1);

% symetric integration interval
n3 = size(SH, 3) - n2 + 1;
n4 = size(SH, 3) - n1 + 1;
nj1 = size(SH, 3) - ni1 + 1;
nj2 = size(SH, 3) - ni2 + 1;

% Energies
LF_psd_avg = squeeze(mean(SH(:, :, n1:ni1), 3)) + ...
    squeeze(mean(SH(:, :, nj1:n4), 3));
HF_psd_avg = squeeze(mean(SH(:, :, ni2:n2), 3)) + ...
    squeeze(mean(SH(:, :, n3:nj2), 3));

% energy ratio
high_low_ratio = HF_psd_avg ./ LF_psd_avg ;

energy_ratio = gather(high_low_ratio);

end
