function mask = make_ring_mask(Nx, Ny, id_x, id_y, radius1, radius2)
    mask = zeros(Nx, Ny);
    
    center_x = floor(Nx/2);
    center_y = floor(Ny/2);

    for y = center_y - radius1:center_y + radius1
        for x = center_x - radius1:center_x + radius1
            vec_norm = norm([x - center_x, y - center_y]);
            if (x > 0 && y > 0 && x <= Nx && y <= Ny && vec_norm < radius1 && vec_norm >= radius2)
                mask(x, y) = 1;
            end
        end
    end

%     imagesc(mask);

mask = circshift(mask, id_x - center_x, 1);
mask = circshift(mask, id_y - center_y, 2);

end