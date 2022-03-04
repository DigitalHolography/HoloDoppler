function mask = apodize_image(Nx, Ny, alpha)
%     mask = zeros(Nx, Ny);
%     size_cropped_image = SubAp_end - SubAp_init + 1;
    gauss_x = gausswin(Nx, alpha);
    gauss_y = gausswin(Ny, alpha);
    mask = ones(Nx, Ny) .* gauss_x .* gauss_y';
%     mask(SubAp_init:SubAp_end,SubAp_init:SubAp_end) = mask_gauss;
end