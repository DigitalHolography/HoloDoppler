function SH = short_time_PCA(H, f1, fs)
    % SVD filtering
    %
    % H: an frame batch already propagated to the distance of reconstruction
    % f1: frequency
    % fs: sampling frequency
    [width, height, batch_size] = size(H);
    H = reshape(H, width*height, batch_size);
    
%     threshold = round(f1 * batch_size / fs)*2 + 1;
    rang = floor(batch_size/1);
    
    % SVD of spatio-temporal features
    cov = H'*H;
    [V,S] = eig(cov);
    [~, sort_idx] = sort(diag(S), 'descend');
    V = V(:,sort_idx);
    SH = cell(1,1);
    tmp = H * V(:,4:rang) * V(:,4:rang)';
    SH{1,1} = reshape(tmp, width, height,[]);
%     for i = 2:4
%         %tmp = H * V(:,(i-1)*rang+1:i*rang) * V(:,(i-1)*rang+1:i*rang)';
%         tmp = H * V(:,4:batch_size) * V(:,4:batch_size)';
%         SH{1,i} = reshape(tmp, width, height, []);
%     end

    SH_output = zeros(width, height, batch_size, 1);
% 
%     for i = 1:4
%        SH_output(:,:,:,i) = SH{i};
%     end

SH_output(:,:,:,1) = SH{1};
    SH = SH_output;



%     H_tissue = H * V(:,1:threshold) * V(:,1:threshold)';
%     tmp_SH = zeros(width*2, height*2, batch_size);
%     tmp_SH(1:width,1:height,:) = SH{1};
%     tmp_SH(width+1:width*2,1:height,:) = SH{2};
%     tmp_SH(1:width,height+1:height*2,:) = SH{3};
%     tmp_SH(width+1:width*2,height+1:height*2,:) = SH{4};
%     SH = tmp_SH;
%     SH = reshape(SH, width*2, height*2, batch_size);
end