function [cube_filtered] = SubAp_filtering(cube, n_SubAp, reciprocal, temporal, eigen_list, n1, n2, gw)
Nz = size(cube, 3);
Nx = size(cube, 2);
Ny = size(cube, 1);

subNx = floor(double(Nx)/n_SubAp);
subNy = floor(double(Ny)/n_SubAp);


cube_filtered = cube;   
cube_chunks_list = zeros(floor(double(Ny)/n_SubAp),floor(double(Nx)/n_SubAp),Nz, n_SubAp^2);

for SubAp_idy = 1 : n_SubAp
    for SubAp_idx = 1 : n_SubAp
        ind = sub2ind([n_SubAp, n_SubAp],SubAp_idx,SubAp_idy);
        idx_range = (SubAp_idx-1)*floor(Nx/n_SubAp)+1:SubAp_idx*floor(Nx/n_SubAp);
        idy_range = (SubAp_idy-1)*floor(Ny/n_SubAp)+1:SubAp_idy*floor(Ny/n_SubAp);
        cube_chunk = cube(idy_range,idx_range,:);
        if reciprocal
            cube_chunk = ifft2(cube_chunk);
        end
        cube_chunks_list(:,:,:,ind) = cube_chunk;
    end
end

figure(600)
for i = 1 : n_SubAp^2
    chunk = reshape(cube_chunks_list(:,:,:, i), subNy, subNx, Nz);
    if reciprocal
        chunk = ifft2(chunk);
    end
    if temporal
        chunk = fft(chunk, [], 3);
    end
    chunk = abs(chunk).^2;
    img = moment0(chunk, n1, n2, size(chunk, 3), size(chunk, 3), gw);
    subplot(n_SubAp,n_SubAp,i)
    imagesc(img)
    colormap gray
    axis square
    axis off
end

A = reshape(cube_chunks_list, subNx*subNy*Nz, n_SubAp^2);
[A, T, V] = my_svd_filter(A, eigen_list);
cube_chunks_list = reshape(A, subNx, subNy, Nz,  n_SubAp^2);

figure(601)
for i = 1 : n_SubAp^2
    chunk = reshape(T(:, i), subNy, subNx, Nz);
    if reciprocal
        chunk = ifft2(chunk);
    end
    if temporal
        chunk = fft(chunk, [], 3);
    end
    chunk = abs(chunk).^2;
    img = moment0(chunk, n1, n2, size(chunk, 3), size(chunk, 3), gw);
    subplot(n_SubAp,n_SubAp,i)
    imagesc(img)
    colormap gray
    axis square
    axis off
end

%% Stitch cube back
for SubAp_idy = 1 : n_SubAp
    for SubAp_idx = 1 : n_SubAp
        ind = sub2ind([n_SubAp, n_SubAp],SubAp_idx,SubAp_idy);
        idx_range = (SubAp_idx-1)*subNx+1:SubAp_idx*subNx;
        idy_range = (SubAp_idy-1)*subNy+1:SubAp_idy*subNy;
        cube_chunk = cube_chunks_list(:,:,:,ind);
        if reciprocal
            cube_chunk = fft2(cube_chunk);
        end
        cube_filtered(idy_range,idx_range, :) = cube_chunk;
    end
end

end