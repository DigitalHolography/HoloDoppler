function [img_energy_ratio] = color_energy_ratio(SH, f1, f2, fi1, fi2, fs, batchSize)

arguments
    SH
    f1
    f2
    fi1
    fi2
    fs
    batchSize
end

[Ny, Nx, ~] = size(SH);
mask = diskMask(Nx, Ny, 1); % DISK
[img_energy_ratio] = energy_ratio(SH, f1, f2, fi1, fi2, fs, batchSize);
img_energy_ratio(~mask) = NaN;
img_energy_ratio = rescale(img_energy_ratio, 0, 1);
img_energy_ratio(~mask) = 0;

end
