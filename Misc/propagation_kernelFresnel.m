function kernel = propagation_kernelFresnel(numX, numY, z, lambda, x_step, y_step, use_double_precision)

numX = double(numX);
numY = double(numY);

x(1:numX) = (((1:numX) - 1) - round(numX / 2)) * x_step; %Valeurs de l'axe x
y(1:numY) = (((1:numY) - 1) - round(numY / 2)) * y_step; %Valeurs de l'axe y

[X, Y] = meshgrid(y, x); %Grille de calcul

kernel = exp(1i * pi / (lambda * z) * (X .^ 2 + Y .^ 2));

if ~use_double_precision
    kernel = single(kernel);
end

end
