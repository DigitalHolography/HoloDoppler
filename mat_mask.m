function [M] = mat_mask(M_init,rem_subAp)
% mat_mask(M_init,rem_subAp) puts 0 value to all 4 corners of a vectorized matrix.
% input:    M_init, matrix or vector to mask. size(M_init) =
% (n_SubAp,n_mode) or (n_SubAp,1)    
%           rem_subAp : vector of size (n_removed,1) of number of
%           subApertures to remove
% output:   M_init with a mask

if rem_subAp == 0
    [Nx_2,Ny] = size(M_init);
    Nx=sqrt(Nx_2);
    idx = 1:Nx_2;
    condition = mod(idx,Nx)~=0 & mod(idx,Nx)~=1 & idx>Nx & idx<=Nx_2-Nx;
    condition = repmat(condition.',1,Ny);
    M = M_init(condition);
    M=reshape(M,[size(M,1)/size(condition,2) size(condition,2)]);
    
else
    M=M_init;
    M(rem_subAp,:)=[];
end
    


%Other versions

% [Nx_2,~] = size(M);
% Nx=sqrt(Nx_2);
% 
% for i = 1:Nx_2
%     idx_row=floor((i-1)/Nx);
%     idx_col=mod(i-1,Nx);
%     idx_corner=[0:n_diag_corner-1 Nx-n_diag_corner:Nx-1];
%     if ~isempty(find(idx_corner==idx_row,1)) && ~isempty(find(idx_corner==idx_col,1))
%         M(Nx_2-i+1,:)=[];
%     end
% end


% [Nx,~] = size(M_init);
% M_masked = M_init;
% M_masked(1,:) = 0;
% M_masked(sqrt(Nx),:) = 0;
% M_masked(Nx-sqrt(Nx)+1,:) = 0;
% M_masked(Nx,:) = 0;

end

