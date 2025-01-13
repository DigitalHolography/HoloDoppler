function [M] = mat_mask(M_init,rem_subAp)
% mat_mask(M_init,rem_subAp) puts 0 value to all 4 corners of a vectorized matrix.
% input:    M_init, matrix or vector to mask. size(M_init) =
% (n_SubAp,n_mode) or (n_SubAp,1)    
%           rem_subAp : vector of size (n_removed,1) of number of
%           subApertures to remove
% output:   M_init with a mask

if rem_subAp == 0
    [numX2,numY2] = size(M_init);
    numX=sqrt(numX2);
    idx = 1:numX2;
    condition = mod(idx,numX)~=0 & mod(idx,numX)~=1 & idx>numX & idx<=numX2-numX;
    condition = repmat(condition.',1,numY2);
    M = M_init(condition);
    M=reshape(M,[size(M,1)/size(condition,2) size(condition,2)]);
else
    M=M_init;
    M(rem_subAp,:)=[];
end
    


%Other versions

% [numX_2,~] = size(M);
% numX=sqrt(numX_2);
% 
% for i = 1:numX_2
%     idx_row=floor((i-1)/numX);
%     idx_col=mod(i-1,numX);
%     idx_corner=[0:n_diag_corner-1 numX-n_diag_corner:numX-1];
%     if ~isempty(find(idx_corner==idx_row,1)) && ~isempty(find(idx_corner==idx_col,1))
%         M(numX_2-i+1,:)=[];
%     end
% end


% [numX,~] = size(M_init);
% M_masked = M_init;
% M_masked(1,:) = 0;
% M_masked(sqrt(numX),:) = 0;
% M_masked(numX-sqrt(numX)+1,:) = 0;
% M_masked(numX,:) = 0;

end

