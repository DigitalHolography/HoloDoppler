function [FH] = subaperture_PCA (FH, SubAp_PCA, acquisition)

ac = acquisition;
batch_size = size(FH,3);
% shifts is a 1D vector
% it maps the 2D SubApils grid by iterating column first
% example of ordering for a 4x4 SubApil grid
% 1  2  3  4
% 5  6  7  8
% 9  10 11 12
% 13 14 15 16
%

ac.Nx = double(ac.Nx);
n_subAp_x = 16;
n_subAp_y = 16;
subAp_Nx = floor(ac.Nx/n_subAp_x); % assume : image is square
subAp_Ny = floor(ac.Nx/n_subAp_x); % assume : image is square


FH_4D = ones(subAp_Nx, subAp_Ny, batch_size, n_subAp_x * n_subAp_y)+1i*ones(subAp_Nx, subAp_Ny, batch_size, n_subAp_x * n_subAp_y);

for id_y = 1 : n_subAp_y
    for id_x = 1 : n_subAp_x  
         FH_4D(:,:,:,id_x+(id_y-1)*n_subAp_x) = FH((id_y-1)*subAp_Nx+1 : id_y*subAp_Nx, (id_x-1)*subAp_Nx+1 : id_x*subAp_Nx, :);
    end
end 

FH_2D = reshape(FH_4D, subAp_Nx * subAp_Ny * batch_size, n_subAp_x * n_subAp_y);

cov = FH_2D' * FH_2D;

[V,S] = eig(cov);
[~, sort_idx] = sort(diag(S), 'descend');
V = V(:,sort_idx);

%singular value selection
% %FIXME ATTN 2f1
% threshold = round(f1 * batch_size / ac.fs)*2 + 1;

%PCA (reciprocal space)
% FH_2D = FH_2D * V(:,3:end);
%SVD (+ return to direct space)
FH_2D = FH_2D * V(:,SubAp_PCA.min:SubAp_PCA.max) * V(:,SubAp_PCA.min:SubAp_PCA.max)';

FH_4D = reshape(FH_2D,subAp_Nx, subAp_Ny, batch_size, n_subAp_x * n_subAp_y);

for id_y = 1 : n_subAp_y
    for id_x = 1 : n_subAp_x  
         FH((id_y-1)*subAp_Nx+1 : id_y*subAp_Nx, (id_x-1)*subAp_Nx+1 : id_x*subAp_Nx, :) = FH_4D(:,:,:,id_x+(id_y-1)*n_subAp_x);
    end
end 

end
