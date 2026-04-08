function [RGB] = color_energy_ratio(SH, f1, f2, fi1, fi2, fs, batchSize, gw)

[Ny, Nx, ~] = size(SH);
mask = diskMask(Nx, Ny, 1); % DISK

[I] = energy_ratio(SH, f1, f2, fi1, fi2, fs, batchSize);
I = I ./ imgaussfilt(I, gw);
I(~mask) = NaN;
I = rescale(I, 0, 1);

cmap = cmapLAB(256, [0 0 0], 0, [1 0 0], 1/2, [1 1 0], 3/4, [1 1 1], 1);

RGB = setcmap(I, ones(Ny, Nx), cmap);
RGB(RGB < 0) = 0;
RGB(RGB > 1) = 1;

mask3D = repmat(mask, [1 1 3]);
RGB(~mask3D) = 0;

end

function [outIm] = setcmap(Im, mask, cmap)
% Im: grayscale image with values between 0 and 1
% mask: binary mask to apply to the output image
% cmap: colormap to apply to the grayscale image

% Number of levels in the colormap
num_levels = size(cmap, 1);

Im = rescale(Im);

% Normalize the grayscale image to the range [1, num_levels]
% This avoids the need for the linspace and min operations
Im_normalized = round(Im * (num_levels - 1)) + 1;

% Ensure that the indices are within the valid range
Im_normalized = max(1, min(Im_normalized, num_levels));

% Map the normalized grayscale data to the colormap
mappedIm = cmap(Im_normalized, :);

% Reshape the mapped image to the original image size
mappedIm = reshape(mappedIm, [size(Im, 1), size(Im, 2), 3]);

% Apply the mask to the output image
outIm = mappedIm .* mask;
end

function [cmap] = cmapLAB(n, color_n, pos_n)

arguments
    n = 256
end

arguments (Repeating)
    color_n
    pos_n
end

pos_n{1} = 0;
pos_n{end} = 1;

numArgs = size(color_n, 2);

L = zeros(n, 1);
a = zeros(n, 1);
b = zeros(n, 1);

for i = 1:numArgs - 1

    n1 = round(n * pos_n{i} + 1);
    n2 = round(n * pos_n{i + 1});

    color1 = color_n{i};
    color2 = color_n{i + 1};

    lab1 = rgb2lab(color1);
    lab2 = rgb2lab(color2);

    dL = lab2(1) - lab1(1);
    da = lab2(2) - lab1(2);
    db = lab2(3) - lab1(3);

    x = linspace(0, 1, n2 - n1 + 1);

    L(n1:n2) = lab1(1) + dL * x;
    a(n1:n2) = lab1(2) + da * x;
    b(n1:n2) = lab1(3) + db * x;

end

cmap = zeros(n, 3);

for idx = 1:n
    cmap(idx, :) = lab2rgb([L(idx) a(idx) b(idx)]);
end

cmap(cmap > 1) = 1;
cmap(cmap < 0) = 0;
cmap(isnan(cmap)) = 0;

end
