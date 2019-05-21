function [mask] = construct_mask(r1, r2, nx, ny)
% constructs a mask to filter spatial frequencies of an image
%
% nx, ny: sizes of the filter
%
% r1: radius of the low frequencies rejector
%
% r2: radius of the high frequencies rejector
x = 1:nx;
y = 1:ny;
[X, Y] = meshgrid(x, y);
mask = ones(nx, ny);
mask(((X - nx / 2).^2 + (Y - ny / 2).^2) <= r1^2) = 0;
mask(((X - nx / 2).^2 + (Y - ny / 2).^2) >= r2^2) = 0;
end