function images_dark_field = mean_of_H_dark_field(H_dark_field, n1, n2)
    
images_dark_field = zeros(size(H_dark_field,1),size(H_dark_field,2), 1, size(H_dark_field,4));

    for i = 1 : size(H_dark_field, 4)

        H_temp = H_dark_field(:,:,:,i);
        SH_temp = fft(H_temp, [], 3);
        M0_temp = (sum(abs(SH_temp(:,:,n1:n2)),3));
        images_dark_field(:,:,:,i) = M0_temp;
%         figure(i)
%         imagesc(M0_temp);
%         colormap gray;
%         axis square;

    end
  
%     images_dark_field = reshape(images_dark_field, size(H_dark_field,1), size(H_dark_field,2), 1, size(H_dark_field,4));
    register_video_from_reference(images_dark_field, images_dark_field(:,:,:,1));

    mean_image = squeeze(mean(images_dark_field,4));
    figure(11)
    imagesc(mean_image);
    colormap gray;
    axis square;


end