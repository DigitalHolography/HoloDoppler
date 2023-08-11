function parallaxFiltering(moment_chunks_array, num_SubAp)

moment_chunks_array = permute(moment_chunks_array, [2 1]);

figure(1)
imagesc(moment_chunks_array)
colormap gray
axis square

Nx = size(moment_chunks_array, 1);
Ny = size(moment_chunks_array, 2);

SubAp_images = zeros(floor(Ny/num_SubAp), floor(Nx/num_SubAp), num_SubAp^2);

for SubAp_idy = 1 : num_SubAp
    for SubAp_idx = 1 : num_SubAp
        %% Construction of subapertures
        ind = sub2ind([num_SubAp, num_SubAp],SubAp_idx,SubAp_idy);
        % get the current index range and reference index ranges
        idx_range = (SubAp_idx-1)*floor(Nx/num_SubAp)+1:SubAp_idx*floor(Nx/num_SubAp);
        idy_range = (SubAp_idy-1)*floor(Ny/num_SubAp)+1:SubAp_idy*floor(Ny/num_SubAp);
        % get the current image chunk
        SubAp_images(:,:,ind) = moment_chunks_array(idy_range,idx_range,:);
    end
end

SubAp_images = reshape(SubAp_images, floor(Ny/num_SubAp)*floor(Nx/num_SubAp), num_SubAp^2);
H_images = SubAp_images;
% features
COV              = H_images*H_images';
[V, S]           = eig(COV);
[~, sortIdx]     = sort(diag(S),'descend');
V                = V(:,sortIdx);



for i = 1 : num_SubAp^2
image_1 = reshape(V(:, i), floor(Ny/num_SubAp), floor(Nx/num_SubAp));
figure
imagesc(image_1)
end
1;
% H_chunk_Tissue   = H_chunk*V(:, 1:threshold) * V(:, 1:threshold)';image_1 = reshape(V(:, 1), floor(Ny/num_SubAp), floor(Nx/num_SubAp));
% H_chunk   = reshape(H_chunk - H_chunk_Tissue, [sz1,sz2, sz3]);

end