function [img_color] = color_energy_ratio(SH, f1, f2, fi1, fi2, fs, batch_size, gw)

arguments
    SH
    f1
    f2
    fi1
    fi2
    fs
    batch_size
    gw
end

[Ny, Nx, ~] = size(SH);
mask = diskMask(Nx, Ny, 1);

img_M0 = moment0(SH, f1, f2, fs, batch_size, gw);
img_M0(~mask) = NaN;
img_M0 = rescale(img_M0);
[img_energy_ratio] = 1 ./ energy_ratio(SH, f1, f2, fi1, fi2, fs, batch_size);

ER_ff = img_energy_ratio ./ imgaussfilt(img_energy_ratio, gw);
img_energy_ratio_centered = log(ER_ff);
img_color = labDuoImage(img_M0, img_energy_ratio_centered);

mask_3D = [~mask ~mask ~mask];
img_color(mask_3D) = 0;
img_color(img_color<0) = 0;
img_color(img_color>1) = 1;
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
a = 128 .* image_2 * rx;
b = 128 .* image_2 * ry;

Lab(:, :, 1) = L;
Lab(:, :, 2) = a;
Lab(:, :, 3) = b;
RGB = lab2rgb(Lab);
end
