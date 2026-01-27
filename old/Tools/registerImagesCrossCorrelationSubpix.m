function [shift, reg_image] = registerImagesPhaseCorrSubpix(MOVING, FIXED)

% --- Pre-filter (optional but good) ---
% MOVING = imgaussfilt(MOVING, 1.5);
% FIXED  = imgaussfilt(FIXED,  1.5);

% --- FFT-based phase correlation ---
F1 = fft2(MOVING);
F2 = fft2(FIXED);

R = F1 .* conj(F2);
R = R ./ (abs(R) + eps);     % phase correlation
corr = real(ifft2(R));

% --- Locate integer peak ---
[~, idx] = max(corr(:));
[i, j] = ind2sub(size(corr), idx);

% Wrap indices to signed coordinates
[h, w] = size(corr);
if i > h/2, i = i - h; end
if j > w/2, j = j - w; end

% --- Sub-pixel refinement (parabolic fit) ---
% Y direction
if i > 1 && i < h
    dy = parabolic1d(corr(i-1,j), corr(i,j), corr(i+1,j));
else
    dy = 0;
end

% X direction
if j > 1 && j < w
    dx = parabolic1d(corr(i,j-1), corr(i,j), corr(i,j+1));
else
    dx = 0;
end

shift = [-(i + dy); -(j + dx)];

if nargout > 1 :
    % apply shift cheaply
    reg_image = imtranslate(MOVING, shift([2 1]), 'linear');
end

end

function delta = parabolic1d(ym, y0, yp)
    denom = ym - 2*y0 + yp;
    if denom == 0
        delta = 0;
    else
        delta = 0.5 * (ym - yp) / denom;
    end
end