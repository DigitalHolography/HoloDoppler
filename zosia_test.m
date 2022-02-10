function zosia_test(image)


    F_img = fftshift(fftshift(fft2(image), 1),2);
    
    n_subAp_x = 4;
    n_subAp_y = 4;
    subAp_Nx = floor(size(image, 1) / n_subAp_x);
    subAp_Ny = floor(size(image, 2) / n_subAp_y);

    gauss = ones(subAp_Nx, subAp_Ny);
%     gauss(4:124, 4:124) = 1;
    gauss = gauss .* hann(subAp_Nx);
    gauss = gauss .* hann(subAp_Ny)';

    gauss = fft2(gauss);
%     t = linspace(-64*pi,64*pi,subAp_Nx);
%     gauss = gauss .*(sinc(t));
%     gauss = gauss .*(sinc(t))';
% 
%     gauss2 = ones(subAp_Nx, subAp_Ny);
%     gauss3 = ones(subAp_Nx, subAp_Ny);
%     x = linspace(-1,1,subAp_Nx);
%     y = linspace(-1,1,subAp_Ny);
%     gauss2 = gauss2 .* x;
% %     gauss3 = gauss3.* y';
% 
%     gauss = gauss .* exp(1i * gauss2 * 202) .* exp(1i * gauss3 * 202);

    F_img3D = zeros(subAp_Nx, subAp_Ny, n_subAp_x * n_subAp_y);
    subAp_M0 = zeros(subAp_Nx, subAp_Ny, n_subAp_x * n_subAp_y);
    stiched_image = zeros(size(image, 1), size(image, 2));

    for id_y = 1 : n_subAp_y
        for id_x = 1 : n_subAp_x
            F_img3D(:,:,id_x+(id_y-1)*n_subAp_x) = conv2(F_img((id_y-1)*subAp_Nx+1 : id_y*subAp_Nx, (id_x-1)*subAp_Nx+1 : id_x*subAp_Nx), gauss, 'same');
%             F_img3D(:,:,id_x+(id_y-1)*n_subAp_x) = F_img((id_y-1)*subAp_Nx+1 : id_y*subAp_Nx, (id_x-1)*subAp_Nx+1 : id_x*subAp_Nx);
            subAp_M0(:, :, id_x+(id_y-1)*n_subAp_x) = ifft2(gauss);
            stiched_image((id_y-1)*subAp_Nx+1 : id_y*subAp_Nx, (id_x-1)*subAp_Nx+1 : id_x*subAp_Nx) = subAp_M0(:, :, id_x+(id_y-1)*n_subAp_x);
        end
    end

    imagesc(abs(stiched_image).^2);
    axis square;
end