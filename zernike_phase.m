function [ phi , zern ] = zernike_phase(A, Nx, Ny)
% Computes the phase phi in a plane.
% INPUTS : 
%   ai - Zernike coeff
%   Nx, Ny: grid size
% OUTPUTS : 
%   phi - phase

x = linspace(-1,1,Nx);
y = linspace(-1,1,Ny);
[X,Y] = meshgrid(x,y);
[theta,r] = cart2pol(X,Y);
% idx = r<=sqrt(2);
% TODO prendre sqrt(2) au lieu de 1
idx = r<=1;
% Calcul de la phase aberree
phi = 0;
zern = zeros(Nx,Ny,numel(A));

zz = zernfun2(1:size(A),r(idx),theta(idx),'norm');

for k = 1:numel(A)
    tmp = zeros(Nx, Ny);
    tmp(idx) = zz(:, k);
    zern(:, :, k) = tmp;
    phi = phi+A(k).*squeeze(zern(:,:,k));
end

end

