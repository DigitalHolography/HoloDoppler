function [kernel,phase_factor] = propagation_kernelFresnel(Nx, Ny, z, lambda, x_step, y_step, use_double_precision)
Nx = double(Nx);
Ny = double(Ny);
x(1:Nx)=(((1:Nx)-1)-round(Nx/2))*x_step; %Valeurs de l'axe x
y(1:Ny)=(((1:Ny)-1)-round(Ny/2))*y_step; %Valeurs de l'axe y
[X,Y]=meshgrid(x,y); %Grille de calcul

kernel = exp(1i*pi/(lambda*z)*(X.^2+Y.^2));
phase_factor = 1i/lambda*exp(-2i*pi*z/lambda)*exp(-1i*pi*((X*lambda*z/(x_step^2*Nx)).^2+(Y*lambda*z/(y_step^2*Ny)).^2)/(lambda*z));

if ~use_double_precision
    kernel = single(kernel);
end
end