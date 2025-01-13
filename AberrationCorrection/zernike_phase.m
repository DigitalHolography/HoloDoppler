function [phi, zern] = zernike_phase(A, numX, numY)
% Computes the phase phi in a plane.
% INPUTS :
%   ai - Zernike coeff
%   numX, numY: grid size
% OUTPUTS :
%   phi - phase

x = linspace(-1, 1, numX);
y = linspace(-1, 1, numY);
[X, Y] = meshgrid(x, y);
[theta, r] = cart2pol(X, Y);
% idx = r<=sqrt(2);
idx = r <= 1;
% Calcul de la phase aberree
phi = 0;
zern = zeros(numX, numY, numel(A), 'single');

zz = zernfun2(A, r(idx), theta(idx)); %,'norm');

for k = 1:numel(A)
    tmp = zeros(numX, numY, 'single');
    tmp(idx) = zz(:, k);
    zern(:, :, k) = tmp;
    phi = phi + A(k) .* squeeze(zern(:, :, k));
end

end
