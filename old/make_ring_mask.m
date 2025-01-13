function mask = make_ring_mask(numX, numY, r1, r2)
mask = zeros(numX, numY);
center_x = floor(numX/2);
center_y = floor(numY/2);

for y = center_y - r1:center_y + r1
    for x = center_x - r1:center_x + r1
        vec_norm = norm([x - center_x, y - center_y]);
        if (x > 0 && y > 0 && x <= numX && y <= numY && vec_norm <= r1 && vec_norm >= r2)
            mask(x, y) = 1;
        end
    end
end
end