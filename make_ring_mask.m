function mask = make_ring_mask(Nx, Ny, id_x, id_y, radius1, radius2)

mask = zeros(Nx, Ny);


for y = id_y - radius1:id_y + radius1
    for x = id_x - radius1:id_x + radius1
        vec_norm = norm([x - id_x, y - id_y]);
        %             if (discretize(x, [0,size(image, 1)]) && discretize(y, [0,size(image, 2)]))
        if (x > 0 && y > 0 && x <= Nx && y <= Ny && vec_norm < radius1 && vec_norm >= radius2)
            mask(x, y) = 1;
        end
    end
end

imagesc(mask);
end