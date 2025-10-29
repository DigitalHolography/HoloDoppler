function zernike_values = evaluate_zernikes(n, m, Nx, Ny)
% evaluate_zernikes - Evaluates Zernike polynomials over a grid.
%
% Inputs:
%   n - Array of radial orders for Zernike polynomials.
%   m - Array of azimuthal orders for Zernike polynomials.
%   Nx - Number of grid points in the x-direction.
%   Ny - Number of grid points in the y-direction.
%
% Output:
%   zernike_values - A 3D array of size (Nx, Ny, numel(n)) containing
%                    the evaluated Zernike polynomials.

% Create a grid of normalized coordinates in the range [-1, 1]
x = linspace(-1, 1, Nx);
y = linspace(-1, 1, Ny);
[X, Y] = meshgrid(x, y);

% Convert Cartesian coordinates to polar coordinates
[theta, r] = cart2pol(X, Y);

% Create a mask for points inside the unit circle (r <= 1)
insideUnitCircle = r <= 1;

% Evaluate Zernike polynomials for points inside the unit circle
zernikeEvals = zernfun(n, m, r(insideUnitCircle), theta(insideUnitCircle), 'norm');

% Initialize the output array
zernike_values = zeros(Nx, Ny, numel(n), 'single');

% Populate the output array with Zernike polynomial values
for k = 1:numel(n)
    tmp = zeros(Nx, Ny, 'single');
    tmp(insideUnitCircle) = zernikeEvals(:, k);
    zernike_values(:, :, k) = tmp;
end

end
