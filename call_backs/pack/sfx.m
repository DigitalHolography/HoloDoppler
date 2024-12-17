
function H = sfx(H, threshold, nb_sub_ap)
    % SVD filtering by sub parts of the image
    %
    % H: an frame batch already propagated to the distance of reconstruction
    % f1: frequency
    % fs: sampling frequency
    % NbSubAp : number N of subapertures to divide SVD filtering over NxN zones
    
    
    [width, height, batch_size] = size(H);
    Lx = linspace(1,width,nb_sub_ap+1);
    Ly = linspace(1,height,nb_sub_ap+1);

    for ii=1:nb_sub_ap
        for kk=1:nb_sub_ap
            H1 = reshape(H(round(Lx(ii)):round(Lx(ii+1)-1),round(Ly(kk)):round(Ly(kk+1)-1),:), (round(Lx(ii+1))-round(Lx(ii)))*(round(Ly(kk+1))-round(Ly(kk))), batch_size);

            % SVD of spatio-temporal features
            cov = H1'*H1;
            [V,S] = eig(cov);
            [~, sort_idx] = sort(diag(S), 'descend');
            V = V(:,sort_idx);
            H_tissue = H1 * V(:,1:threshold) * V(:,1:threshold)';
            H1 = reshape(H1 - H_tissue, (round(Lx(ii+1))-round(Lx(ii))), (round(Ly(kk+1))-round(Ly(kk))), batch_size);
            H(round(Lx(ii)):round(Lx(ii+1)-1),round(Ly(kk)):round(Ly(kk+1)-1),:) = reshape(H1, (round(Lx(ii+1))-round(Lx(ii))), (round(Ly(kk+1))-round(Ly(kk))), batch_size);
        end
    end
    
    end