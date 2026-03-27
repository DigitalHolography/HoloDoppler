function [RGB] = new_color_image(SH, f1, f2, fi1, fi2, fs, batchSize)

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

L = spectral_negentropy(SH, f1, f2, fs, batchSize);
ab = energy_ratio(SH, f1, f2, fi1, fi2, fs, batchSize);

L(~mask) = NaN;
L = rescale(L, 0, 1);
L(~mask) = 0;

ab = ab ./ imgaussfilt(ab, 35);
ab(~mask) = NaN;
ab = ab - mean(ab, 'all', 'omitnan');
ab(~mask) = 0;

RGB = labDuoImage(L, ab, 45);
RGB(RGB>1) = 1;
RGB(RGB<0) = 0;

end

function [RGB] = labDuoImage(image_1, image_2, h)

arguments
    image_1,
    image_2,
    h = 45
end

h = mod(h, 360);

if abs(h) <= 45 || abs(h - 180) <= 45
    rx = sign(cosd(h));
    ry = sign(sind(h)) .* (1 / (cosd(h) * cosd(h)) - 1);
else
    ry = sign(sind(h));
    rx = sign(cosd(h)) .* (1 / (sind(h) * sind(h)) - 1);
end

image_1 = image_1 ./ max(abs(max(image_1, [], "all")), abs(min(image_1, [], "all")));
image_2 = image_2 ./ max(abs(max(image_2, [], "all")), abs(min(image_2, [], "all")));

L = 100 .* image_1;
a = 127.5 .* image_2 * rx - 0.5;
b = 127.5 .* image_2 * ry - 0.5;

Lab(:, :, 1) = L;
Lab(:, :, 2) = a;
Lab(:, :, 3) = b;
RGB = lab2rgb(Lab);
end
