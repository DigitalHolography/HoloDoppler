function [Q] = RenderQuadrant(FHin, Params)
[numX, numY, ~] = size(FHin);
[X, Y] = meshgrid(linspace(-1, 1, numX), linspace(-1, 1, numY));
ang = mod(atan2(Y, X) + pi, 2 * pi);

for i = 1:4
    mask = ((i) * pi / 2 > ang) & (ang >= (i - 1) * pi / 2);
    FH = FHin .* mask; % the whole point of quadrant is to reconstruct only some parts of the image

    switch Params.spatial_transformation
        case "angular spectrum"
            H = ifft2(FH);
        case "Fresnel"
            H = fftshift(fftshift(fft2(FH), 1), 2); %.*PhaseFactor;
        case "None"
            H = single(Frames);
    end

    svd_filter(H, Params.svd_threshold, Params.time_range(1), Params.fs, Params.svd_stride);

    switch Params.time_transform
        case 'PCA'
            SH = short_time_PCA(H);
        case 'FFT'
            SH = fft(H, [], 3);
    end

    SH = flip(permute(SH, [2 1 3]), 2); % x<->-y transpose due to the lens imaging

    if Params.flip_y
        SH = flip(SH, 1);
    end

    if Params.flip_x
        SH = flip(SH, 2);
    end

    Q.(sprintf("Q%d_m0", i)) = moment0(SH, Params.time_range(1), Params.time_range(2), Params.fs, size(FH, 3), Params.flatfield_gw);
    Q.(sprintf("Q%d_m1", i)) = moment1(SH, Params.time_range(1), Params.time_range(2), Params.fs, size(FH, 3), Params.flatfield_gw);
end

%Q.numQuadrants=4;
end
