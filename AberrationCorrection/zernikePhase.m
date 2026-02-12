function [phi, zern] = zernikePhase(A, Nx, Ny, Radius)
% zernikePhase - Computes the phase and Zernike polynomials over a grid.
%
% Inputs:
%   A - Array of Zernike coefficients.
%   Nx - Number of grid points in the x-direction.
%   Ny - Number of grid points in the y-direction.
%
% Outputs:
%   phi - The computed phase in the plane.
%   zern - A 3D array of size (Nx, Ny, numel(A)) containing the evaluated Zernike polynomials.

if nargin < 4
    Radius = 1;
end

% Create a grid of normalized coordinates in the range [-1, 1]
x = linspace(-1, 1, Nx);
y = linspace(-1, 1, Ny);
[X, Y] = meshgrid(y, x);

% Convert Cartesian coordinates to polar coordinates
[theta, r] = cart2pol(X, Y);

% Create a mask for points inside the unit circle (r <= 1)
insideUnitCircle = r <= Radius;

% Initialize the phase and Zernike polynomials array
phi = 0; % Phase
zern = zeros(Nx, Ny, numel(A), 'single'); % Zernike polynomials

% Evaluate Zernike polynomials for points inside the unit circle

% Compute the phase and Zernike polynomials
for k = 1:numel(A)
    tmp = zeros(Nx, Ny, 'single');
    tmp(insideUnitCircle) = zernfun2(A(k), r(insideUnitCircle), theta(insideUnitCircle));
    zern(:, :, k) = tmp;
    phi = phi + A(k) .* squeeze(zern(:, :, k));
end

end
