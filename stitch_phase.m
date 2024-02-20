function phase = stitch_phase(shifts, phase_zernike, Nx, Ny, shack_hartmann)

SubAp_Nx = floor(Nx/shack_hartmann.n_SubAp);
SubAp_Ny = floor(Ny/shack_hartmann.n_SubAp);

%% Padding when n_subAp_positions > image_to_subap_size_ratio
stride = floor((Nx-SubAp_Nx)/(shack_hartmann.n_SubAp_inter-1));

if stride > SubAp_Nx
    range_x = stride * (shack_hartmann.n_SubAp_inter-1) + SubAp_Nx;
    range_y = stride * (shack_hartmann.n_SubAp_inter-1) + SubAp_Ny;
else
    range_x = stride * (shack_hartmann.n_SubAp_inter);
    range_y = stride * (shack_hartmann.n_SubAp_inter);
end
% pad_x = floor(SubAp_Nx/2) - floor(stride/2);
% pad_y = floor(SubAp_Nx/2) - floor(stride/2);
pad_x = floor((Nx - range_x)/2);
pad_y = floor((Ny - range_y)/2);
phase = zeros(Nx, Ny, size(shifts, 3));

shifts = double(shifts);

if ~(isempty(phase_zernike))
    shifts = shifts .* Nx .* 3.1427;
end

shifts = reshape(shifts, shack_hartmann.n_SubAp_inter, shack_hartmann.n_SubAp_inter, []);

[X, Y] = meshgrid(1 : shack_hartmann.n_SubAp_inter);
step = (shack_hartmann.n_SubAp_inter-1) / range_x;
[Xq ,Yq] = meshgrid(1 : step : shack_hartmann.n_SubAp_inter - step);
half_Nx = floor(Nx/2);

for i = 1 : size(shifts, 3)

    Ay = -imag(shifts(:,:,i));
    Ax = -real(shifts(:,:,i));

    Ax = interp2(X, Y, Ax, Xq, Yq);
    Ay = interp2(X, Y, Ay, Xq, Yq);
    dx = 2/range_x;
    dy = 2/range_y;
    A = intgrad2(Ax, Ay, dx, dy, 0);

    if  ~(isempty(phase_zernike))
        A = A - (A(half_Nx, half_Nx) - phase_zernike(half_Nx, half_Nx));
    else
        A = A - mean(A, "all");
    end
    A = permute(A, [2 1]);
    phase(pad_x + 1 : pad_x + range_x, pad_y + 1 : pad_y + range_y,i) = A;

end

% Ay = imag(shifts(:,:,i));
% Ax = real(shifts(:,:,i));


% figure(2)
% q = quiver(X,Y,Ax,Ay);
% q.Alignment = 'center';
% % imagesc(angle(exp(1i.*phase(:,:,1))))
% q.Color = 'white';
% set(gca,'Color','k')
% axis square
% axis off
% colormap gray
% colormap gray

% figure(1)
% imagesc(A)
% % surf(X, Y, A)
% axis square
% axis off

mask = construct_mask(0, round(Nx/2), Nx, Ny);

if ~isempty(phase_zernike)
    figure(9)
    subplot(2,1,1)
    imagesc(angle(exp(1i.*phase_zernike)))
    title('Projected on Zernike')
    axis square
    axis off
    colormap gray

    subplot(2,1,2)
    imagesc(angle(exp(1i.*phase)).*mask)
    title('Gradient integration')
    axis square
    axis off
    colormap gray
end
end
