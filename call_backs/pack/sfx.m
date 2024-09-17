
function H = sfx(H, threshold)
    % SVD filtering by sub parts of the image
    %
    % H: an frame batch already propagated to the distance of reconstruction
    % f1: frequency
    % fs: sampling frequency
    % NbSubAp : number N of subapertures to divide SVD filtering over NxN zones
    
    
    [width, height, batch_size] = size(H);
    Lx = linspace(1,width,NbSubAp+1);
    Ly = linspace(1,height,NbSubAp+1);

    for ii=1:NbSubAp
        for kk=1:NbSubAp
            H1 = H(round(Lx(ii)):round(Lx(ii+1)-1),round(Ly(kk)):round(Ly(kk+1)-1),:);
            H1 = reshape(H1, (round(Lx(ii+1))-round(Lx(ii)))*(round(Ly(kk+1))-round(Ly(kk))), batch_size);

            % SVD of spatio-temporal features
            cov = H1'*H1;
            [V,S] = eig(cov);
            [~, sort_idx] = sort(diag(S), 'descend');
            V = V(:,sort_idx);
            H_tissue = H1 * V(:,1:tresh) * V(:,1:tresh)';
            H1 = reshape(H1 - H_tissue, (round(Lx(ii+1))-round(Lx(ii))), (round(Ly(kk+1))-round(Ly(kk))), batch_size);
            H(round(Lx(ii)):round(Lx(ii+1)-1),round(Ly(kk)):round(Ly(kk+1)-1),:) = reshape(H1, (round(Lx(ii+1))-round(Lx(ii))), (round(Ly(kk+1))-round(Ly(kk))), batch_size);
        end
    end
    
    end