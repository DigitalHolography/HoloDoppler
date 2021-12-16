function kernel = propagation_kernelFresnel(Nx, Ny, z, lambda, x_step, y_step, use_double_precision)
% % Wave propagation kernel 2FFT
% u_step = 1.0 / (Nx * x_step);
% v_step = 1.0 / (Ny * y_step);
% u = ((1:Nx) - 1 - round(Nx / 2)) * u_step;
% v = ((1:Ny) - 1 - round(Ny / 2)) * v_step;
% [U, V] = meshgrid(v, u);
% kernel = exp(2 * 1i * pi * z / lambda * sqrt(1 - lambda^2 * (U).^2 - lambda^2 * (V).^2));

x(1:Nx)=(((1:Nx)-1)-round(Nx/2))*x_step; %Valeurs de l'axe x
y(1:Ny)=(((1:Ny)-1)-round(Ny/2))*y_step; %Valeurs de l'axe y
[X,Y]=meshgrid(x,y); %Grille de calcul
kernel = exp(1i*pi/(lambda*z)*(X.^2+Y.^2));

if ~use_double_precision
    kernel = single(kernel);
end

end