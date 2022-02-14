function filter = gauss2D(dim, alpha)
    gauss = gausswin(dim, 1 / alpha);
    filter = ones(dim, dim) .* gauss .* gauss';
end