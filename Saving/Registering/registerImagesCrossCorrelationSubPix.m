function [reg_image, shift] = registerImagesCrossCorrelationSubPix(MOVING, FIXED)

MOVING = imgaussfilt(MOVING, 1.5);
FIXED = imgaussfilt(FIXED, 1.5);

Fm = fft2(MOVING);
Ff = fft2(FIXED);

R = Fm .* conj(Ff);
R = R ./ max(abs(R), eps);

corr = real(ifft2(R));
corr = fftshift(corr);

[~, idx] = max(corr(:));
[py, px] = ind2sub(size(corr), idx);

if py > 1 && py < size(corr, 1) && px > 1 && px < size(corr, 2)
    dy = (corr(py + 1, px) - corr(py - 1, px)) / ...
        (2 * (2 * corr(py, px) - corr(py + 1, px) - corr(py - 1, px)));
    dx = (corr(py, px + 1) - corr(py, px - 1)) / ...
        (2 * (2 * corr(py, px) - corr(py, px + 1) - corr(py, px - 1)));
else
    dy = 0;
    dx = 0;
end

cy = ceil(size(corr, 1) / 2);
cx = ceil(size(corr, 2) / 2);

shift_y = (py - cy) + dy;
shift_x = (px - cx) + dx;

shift = [shift_x; shift_y];

if ~any(isnan(MOVING))
    reg_image = imtranslate(MOVING, [-shift_x, -shift_y], 'linear', 'FillValues', 0);
else
    reg_image = MOVING;
end

end
