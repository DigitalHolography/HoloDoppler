function zernike_values = evaluate_zernikes(n, m, numX, numY)
x = linspace(-1, 1, numX);
y = linspace(-1, 1, numY);
[X, Y] = meshgrid(x, y);
[theta, r] = cart2pol(X, Y);
indices = r <= sqrt(2); % [-1; 1] square excircle
y = zernfun(n, m, r(indices), theta(indices), 'norm');

% evaluate base functions
zernike_values = zeros(numX, numY, numel(n), 'single');

for k = 1:numel(n) % k= 1,2,3
    tmp = zeros(numX, numY, 'single');
    tmp(indices) = y(:, k);
    zernike_values(:, :, k) = tmp;
end
end