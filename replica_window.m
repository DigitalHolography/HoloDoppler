function w = replica_window(Nx, Ny, x0, y0)
% x0: number of pixels to skip horizontally on each side of the window
% y0: number of pixels to skip horizontally on each side of the window

x_window_size = Nx - 2*x0;
y_window_size = Ny - 2*y0;

factor = 0.8;

x = [zeros(x0,1)' ones(x_window_size,1)' zeros(x0,1)'];
y = [zeros(y0,1)' ones(y_window_size,1)' zeros(y0,1)'];

w = meshgrid(x, y);

% middle bands
w(1:x0,y0+1:end-y0) = ((1:x0) ./ x0)' * ones(y_window_size,1)';
w(1:x0,y0+1:end-y0) = exp(1i * w(1:x0,y0+1:end-y0) * x0 * factor);

w(x0 + x_window_size + 1:end,y0+1:end-y0) = ((x0:-1:1) ./ x0)' * ones(y_window_size,1)';
w(x0 + x_window_size + 1:end,y0+1:end-y0) = exp(1i * w(x0 + x_window_size + 1:end,y0+1:end-y0) * x0 * factor);

w(x0+1:end-x0,1:y0) = ones(x_window_size,1) * ((1:y0) ./ y0);
w(x0+1:end-x0,1:y0) = exp(1i * w(x0+1:end-x0,1:y0) * y0 * factor);

w(x0+1:end-x0,y0 + y_window_size + 1:end) = ones(x_window_size,1) * ((y0:-1:1) ./ y0);
w(x0+1:end-x0,y0 + y_window_size + 1:end) = exp(1i * w(x0+1:end-x0,y0 + y_window_size + 1:end) * y0 * factor);

% corners now
w(1:x0,end-y0+1:end) = (((1:x0) ./ x0)' * ones(y0,1)' + (ones(x0,1) * (y0:-1:1) ./ y0)) ./ 2;
w(1:x0,end-y0+1:end) = exp(1i * sqrt(w(1:x0,end-y0+1:end)) * (x0 + y0) * factor);

w(x0 + x_window_size + 1:end,end-y0+1:end) = (((x0:-1:1) ./ x0)' * ones(y0,1)' + (ones(x0,1) * (y0:-1:1) ./ y0)) ./ 2;
w(x0 + x_window_size + 1:end,end-y0+1:end) = exp(1i * w(x0 + x_window_size + 1:end,end-y0+1:end) * (x0 + y0) * factor);

% symetric
% TODO: fix. it will crash if x0 != y0
w(x0 + x_window_size + 1:end,1:y0) = w(1:x0,end-y0+1:end)';
w(1:x0,1:y0) = w(x0 + x_window_size + 1:end,end-y0+1:end)';
end