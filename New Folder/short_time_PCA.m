function H_PCA = short_time_PCA(H)
    % PCA
    
    [width, height, batch_size] = size(H);
    H = reshape(H, width*height, batch_size);
    % SVD of spatio-temporal features
    cov = H'*H;
    [V,S] = eig(cov);
    [~, sort_idx] = sort(diag(S), 'descend');
    V = V(:,sort_idx);
%     figure
%     plot(log(diag(S)), '.')
%     title('Eigenvalues distribution')
%     threshold = round(f1 * batch_size / fs)*2 + 1;
    % selection of eigenvalues
%     X = ones(size(V));
%     X(:, x) = 0;
%     V = V.*X;
    %projection of H
    H_PCA = H * V;
    H_PCA = reshape(H_PCA,width,height,batch_size);
end