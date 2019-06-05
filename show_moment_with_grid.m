function show_moment_with_grid(img, Nx, Ny, n_pup)
val = max(max(img));
for i = 1:floor(Nx/n_pup):Nx
    img(i,:) = val;
end
for j = 1:floor(Ny/n_pup):Ny
    img(:,j) = val;
end

imshow(mat2gray(img));
end