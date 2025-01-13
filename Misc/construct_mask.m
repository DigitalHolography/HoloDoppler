function [mask] = construct_mask(r1, r2, numX, numY)
% constructs a mask to filter spatial frequencies of an image
%
% numX, numY: sizes of the filter
%
% r1: radius of the low frequencies rejector
%
% r2: radius of the high frequencies rejector
x = 1:numX;
y = 1:numY;
[X, Y] = meshgrid(x, y);
mask = ones(numX, numY);
mask(((X - numX / 2) .^ 2 + (Y - numY / 2) .^ 2) <= r1 ^ 2) = 0;
mask(((X - numX / 2) .^ 2 + (Y - numY / 2) .^ 2) >= r2 ^ 2) = 0;
end
