function kernel = propagation_kernelAngularSpectrum(numX, numY, z, lambda, x_step, y_step, use_double_precision)

u_step = 1.0 / (numX * x_step);
v_step = 1.0 / (numY * y_step);
u = ((1:numX) - 1 - round(numX / 2)) * u_step;
v = ((1:numY) - 1 - round(numY / 2)) * v_step;
a = 1;

[U, V] = meshgrid(a * v, a * u);

kernel = exp(2 * 1i * pi * z / lambda * sqrt(1 - lambda ^ 2 * (U) .^ 2 - lambda ^ 2 * (V) .^ 2));

if ~use_double_precision
    kernel = single(kernel);
end

% imagesc(real(kernel));
% axis image;
% 1;
end
