function plot_shifts(shifts, n_pup, Nx, Ny)
x = zeros(n_pup^2,1);
y = zeros(n_pup^2,1);
x_cdg = zeros(n_pup^2,1);
y_cdg = zeros(n_pup^2,1);
for pup_x = 1:n_pup
    for pup_y = 1:n_pup
        center_x = (floor(Nx/n_pup) * (2 * pup_x - 1) + 1) / 2;
        center_y = (floor(Ny/n_pup) * (2 * pup_y - 1) + 1) / 2;
        x_cdg(1 + (pup_y - 1) + n_pup * (pup_x - 1)) = center_x;
        y_cdg(1 + (pup_y - 1) + n_pup * (pup_x - 1)) = center_y;
        x(1 + (pup_y - 1) + n_pup * (pup_x - 1)) = floor(center_x - real(shifts(1 + (pup_y - 1) + n_pup * (pup_x - 1))));
        y(1 + (pup_y - 1) + n_pup * (pup_x - 1)) = floor(center_y - imag(shifts(1 + (pup_y - 1) + n_pup * (pup_x - 1))));
    end
end

figure()
plot(x,y,'r*')
hold on
plot(x_cdg, y_cdg, 'b+')
hold off
end