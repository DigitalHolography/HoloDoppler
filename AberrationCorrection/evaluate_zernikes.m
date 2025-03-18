function zernike_values = evaluate_zernikes(n, m, Nx, Ny)
x = linspace(-1, 1, Nx);
y = linspace(-1, 1, Ny);
[X, Y] = meshgrid(x, y);
[theta, r] = cart2pol(X, Y);
indices = r <= sqrt(2); % [-1; 1] square excircle
y = zernfun(n, m, r(indices), theta(indices), 'norm');

% evaluate base functions
zernike_values = zeros(Nx, Ny, numel(n), 'single');

for k = 1:numel(n) % k= 1,2,3
    tmp = zeros(Nx, Ny, 'single');
    tmp(indices) = y(:, k);
    zernike_values(:, :, k) = tmp;
end

end
