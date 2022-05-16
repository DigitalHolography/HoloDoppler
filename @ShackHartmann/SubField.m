function SubFH = SubField(obj, FH)
%     num_SubFH_x = floor((size(FH, 1) - obj.subimage_size) / obj.subimage_stride) + 1;
%     num_SubFH_y = floor((size(FH, 2) - obj.subimage_size) / obj.subimage_stride) + 1;
%     SubFH = cell(num_SubFH_y, num_SubFH_x);
%     H = ifft2(FH);
%     H = fftshift(fftshift(H, 1), 2);
% %     figure;
% %     imshow(mat2gray(squeeze(mean(abs(H(:,:,10:40)), 3))));
% 
%     for y = 1:num_SubFH_y
%         for x = 1:num_SubFH_x
%             SubH = H(((y - 1) * obj.subimage_stride) + 1:((y - 1) * obj.subimage_stride) + obj.subimage_size, ((x - 1) * obj.subimage_stride) + 1:((x - 1) * obj.subimage_stride) + obj.subimage_size, :);
%             SubH = fft2(SubH);
%             SubH = fftshift(fftshift(SubH, 1), 2);
% 
%             SubFH{y, x} = SubH;
%         end
%     end
%     aSubFH = abs(SubFH{y, x});
%     aSubFH = aSubFH / sum(aSubFH, 'all') *10000;
%     imagesc(mat2gray(log(aSubFH)));
%     number_512 = sum(aSubFH(384-67 : 384+67, 384-67 : 384+67, :), "all")
    SubFH = {FH};
end