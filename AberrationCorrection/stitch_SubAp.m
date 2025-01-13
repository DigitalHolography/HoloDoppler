function stitched_FH = stitch_SubAp(FH)
n_SubAp = sqrt(size(FH, 1));
numY = size(FH, 2);
numX = size(FH, 3);
stitched_FH = ones(n_SubAp*numY, n_SubAp*numX);

for idx = 1 : n_SubAp
    for idy = 1 : n_SubAp
        idx_range = (idx - 1) * numX + 1 : idx * numX;
        idy_range = (idy - 1) * numY + 1 : idy * numY;
        stitched_FH(idy_range, idx_range) = FH((idy - 1) * n_SubAp + idx, :, :);
    end
end
end