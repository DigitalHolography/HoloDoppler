function stitched_FH = stitch_SubAp(FH)
n_SubAp = sqrt(size(FH, 1));
Ny = size(FH, 2);
Nx = size(FH, 3);
stitched_FH = ones(n_SubAp * Ny, n_SubAp * Nx);

for idx = 1:n_SubAp

    for idy = 1:n_SubAp
        idxRange = (idx - 1) * Nx + 1:idx * Nx;
        idyRange = (idy - 1) * Ny + 1:idy * Ny;
        stitched_FH(idyRange, idxRange) = FH((idy - 1) * n_SubAp + idx, :, :);
    end

end

end
