function SH = long_time_PCA(SH_video)
% slices are the ranges of pseudo frequencies chosen in PCA short time
    [width, height, num_batches, slices] = size(SH_video);
    SH_video = reshape(SH_video, width*height*slices, num_batches);

    cov = SH_video'*SH_video;
    [V,S] = eig(cov);
    [~, sort_idx] = sort(diag(S), 'descend');
    V = V(:,sort_idx);

    range = floor(num_batches/1);

    SH = cell(1,1);
% do we also  need to skip first pseudo-frequencies?
    tmp = SH_video * V(:,4:range) * V(:,4:range)';
    SH{1,1} = reshape(tmp, width, height, slices, []);
%     for i = 2:4
%         tmp = SH_video * V(:,(i-1)*range+1:i*range) * V(:,(i-1)*range+1:i*range)';
%         SH{1,i} = reshape(tmp, width, height, slices, []);
%     end
end