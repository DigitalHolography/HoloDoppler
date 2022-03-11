function FH = local_spatial_PCA(FH, nu1, nu2)
% spatial filtering in sub-cube of FH to reveal smaller structures

H = fft2(FH);
% H = FH;

num_cube_x = 8;
num_cube_y = 8;
Nx_cube = floor(size(H, 1)/num_cube_x);
Ny_cube = floor(size(H, 2)/num_cube_y);
H_filtered = 1i*zeros(size(H), 'double');

cube = 1i*zeros(Nx_cube, Ny_cube, size(FH, 3), num_cube_x, num_cube_y);

for id_y = 1 : num_cube_y
    for id_x = 1 : num_cube_x
        % cut out the cube of interest
        range_x = (id_x - 1) * Nx_cube + 1: id_x * Nx_cube;
        range_y = (id_y - 1) * Ny_cube + 1: id_y * Ny_cube;
        cube(:,:,:,id_x, id_y) = H(range_x, range_y, :);
    end
end

for id_y = 4 : 6
    for id_x = 4 : 6
        %filter with spatial PCA
        minicube = squeeze(cube(:,:,:, id_x, id_y));
        minicube = reshape(minicube, Nx_cube * Ny_cube, size(H,3));
        COV = minicube*minicube'; % dimensions inversed (final dim = xy)
        [V, S]           = eig(COV);
        [~, sortIdx]     = sort(diag(S),'descend');
        V                = V(:,sortIdx);
        minicube = (minicube'*V(:, nu1:nu2) * V(:, nu1:nu2)')';
        minicube = reshape(minicube, Nx_cube, Ny_cube, size(H, 3));
        %reassign to the FH
        cube(:,:,:, id_x, id_y) = minicube;
    end
end

for id_y = 4 : 6
    for id_x = 4 : 6
        range_x = (id_x - 1) * Nx_cube + 1: id_x * Nx_cube;
        range_y = (id_y - 1) * Ny_cube + 1: id_y * Ny_cube;
        H_filtered(range_x, range_y, :) = cube(:,:,:, id_x, id_y);
    end
end

FH = ifft2(H_filtered);
end