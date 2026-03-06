function [energy_ratio] = energy_ratio(SH, f1, f2, fi, fs, batch_size)

arguments
    SH
    f1
    f2
    fi
    fs
    batch_size
end

SH = abs(SH);

% integration interval
% convert frequencies to indices
n1 = ceil(f1 * batch_size / fs);
n2 = ceil(f2 * batch_size / fs);
ni = ceil(fi * batch_size / fs);

n1 = max(min(n1, ceil(size(SH, 3) / 2)), 1);
n2 = max(min(n2, ceil(size(SH, 3) / 2)), 1);
ni = max(min(ni, ceil(size(SH, 3) / 2)), 1);

% symetric integration interval
n3 = size(SH, 3) - n2 + 1;
n4 = size(SH, 3) - n1 + 1;
nj = size(SH, 3) - ni + 1;

% Further
outerMask = ~diskMask(Ny, Nx, 1.2);
SH_mask = SH .* outerMask;
outerReference = sum(SH_mask, [1 2]) / nnz(outerMask);
SH_norm = SH ./ outerReference;

% Energies
HF_energy = squeeze(sum(SH_norm(:, :, n1:ni), 3)) + ...
    squeeze(sum(SH_norm(:, :, nj:n4), 3));
LF_energy = squeeze(sum(SH_norm(:, :, ni:n2), 3)) + ...
    squeeze(sum(SH_norm(:, :, n3:nj), 3));
% total_energy = squeeze(sum(SH_norm(:, :, n1:n2), 3)) + ...
%     squeeze(sum(SH_norm(:, :, n3:n4), 3));

% energy ratio
high_low_ratio = HF_energy ./ LF_energy;
% low_total_ratio = LF_energy ./ total_energy;
% high_total_ratio = HF_energy ./ total_energy;

energy_ratio = gather(high_low_ratio);

end
