function kernel = propagation_kernel(numX, numY, z, lambda, x_step, y_step, use_double_precision)
% Wave propagation kernel 2FFT
u_step = 1.0 / (numX * x_step);
v_step = 1.0 / (numY * y_step);
u = ((1:numX) - 1 - round(numX / 2)) * u_step;
v = ((1:numY) - 1 - round(numY / 2)) * v_step;
[U, V] = meshgrid(v, u);

kernel = exp(2 * 1i * pi * z / lambda * sqrt(1 - lambda^2 * (U).^2 - lambda^2 * (V).^2));
if ~use_double_precision
    kernel = single(kernel);
end
end