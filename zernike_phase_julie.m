function [ phi , zern ] = zernike_phase_julie(A, Nx, Ny)
% Computes a phase plane phi from Zernike coefficients.
%   To suppress offset+1 first Zernike modes
% INPUTS : 
%   A- Zernike coeffs
%   Nx, Ny: grid size
%   TODO add offset and radius
% OUTPUTS : 
%   phi - phase
%   zern - individual polynoms on the grid

x = linspace(-1,1,Nx);
y = linspace(-1,1,Ny);
[X,Y] = meshgrid(x,y);
[theta,r] = cart2pol(X,Y);
%  idx = r<=sqrt(2);
% TODO do not sqrt(2) instead of 1
idx = r<=1;
% Calcul de la phase aberree
phi = 0;
zern = zeros(Nx,Ny,numel(A));
offset = 2; %To suppress offset+1 first Zernike modes

zz = zernfun2(1+offset:size(A)+offset,r(idx),theta(idx));%,'norm');

for k = 1:numel(A)
    tmp = zeros(Nx, Ny);
    tmp(idx) = zz(:, k);
    zern(:, :, k) = tmp;
    phi = phi+A(k).*squeeze(zern(:,:,k));
end

end

