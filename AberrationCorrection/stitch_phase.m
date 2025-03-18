function phase = stitch_phase(shifts, phase_zernike, Nx, Ny, shack_hartmann)

SubAp_Nx = floor(Nx / shack_hartmann.n_SubAp);
SubAp_Ny = floor(Ny / shack_hartmann.n_SubAp);

%% Padding when n_subAp_positions > image_to_subap_size_ratio
stride = floor((Nx - SubAp_Nx) / (shack_hartmann.n_SubAp_inter - 1));

if stride > SubAp_Nx
    range_x = stride * (shack_hartmann.n_SubAp_inter - 1) + SubAp_Nx;
    range_y = stride * (shack_hartmann.n_SubAp_inter - 1) + SubAp_Ny;
else
    range_x = stride * (shack_hartmann.n_SubAp_inter);
    range_y = stride * (shack_hartmann.n_SubAp_inter);
end

% pad_x = floor(SubAp_Nx/2) - floor(stride/2);
% pad_y = floor(SubAp_Nx/2) - floor(stride/2);
pad_x = floor((Nx - range_x) / 2);
pad_y = floor((Ny - range_y) / 2);
phase = zeros(Nx, Ny, size(shifts, 3));

shifts = double(shifts);

if ~(isempty(phase_zernike))
    %     shifts = shifts .* Nx .* 3.1427;
    shifts = shifts .* (Nx / shack_hartmann.n_SubAp);
end

% shifts = shifts .* 3;
% shifts = reshape(shifts, shack_hartmann.n_SubAp_inter, shack_hartmann.n_SubAp_inter, []);

% a = DopplerAcquisition(Nx, Ny, 0,0,0,0,0,0,0,0,0);
% [~, defocus] = zernike_phase(9, Nx, Ny);
% defocus_phase_pos = exp(1i .* (defocus .* 40));
% [shifts, ~, ~, ~] = shack_hartmann.compute_images_shifts(defocus_phase_pos, 1, 2, 3, true, false, a);
% cf = linspace(-25, 25, 50);
% sh = zeros(50, 1);
[~, tilt] = zernike_phase(2, Nx, Ny);
cf = linspace(-60, 60, 50);
sh = zeros(50, 1);
half_SubAp_Nx = floor(SubAp_Nx / 2);
% half_SubAp_Nx = floor(Nx /2) - 1;
half_Nx = floor(Nx / 2);

for i = 1:50
    calibration_factor = cf(i);
    tilt_phase_pos = exp(1i .* (tilt));
    tilt_phase_pos = tilt_phase_pos(half_Nx - half_SubAp_Nx:half_Nx + half_SubAp_Nx, half_Nx - half_SubAp_Nx:half_Nx + half_SubAp_Nx);
    tilt_phase_pos = tilt_phase_pos .^ (calibration_factor);
    spot_pos = abs(fftshift(fftshift(ifft2(tilt_phase_pos), 1), 2)) .^ 2;
    %     tilt_phase_neg = exp(1i .* (-tilt));
    %     tilt_phase_neg = tilt_phase_neg(half_Nx - half_SubAp_Nx : half_Nx + half_SubAp_Nx, half_Nx - half_SubAp_Nx : half_Nx + half_SubAp_Nx);
    %     tilt_phase_neg = tilt_phase_neg.^(calibration_factor);
    %     spot_neg = abs(fftshift(fftshift(ifft2(tilt_phase_neg),1),2)).^2;
    %     c = normxcorr2(spot_pos,spot_neg);
    c = spot_pos;
    [xpeak_aux, ypeak_aux] = find(spot_pos == max(spot_pos(:)));
    ypeak = ypeak_aux + 0.5 * (c(xpeak_aux, ypeak_aux - 1) - c(xpeak_aux, ypeak_aux + 1)) / (c(xpeak_aux, ypeak_aux - 1) + c(xpeak_aux, ypeak_aux + 1) - 2 .* c(xpeak_aux, ypeak_aux));
    yoffSet = ceil(size(spot_pos, 2) / 2) - ypeak;
    sh(i) = yoffSet;
end

% new_x_shifts = interp1(sh, cf', real(shifts));
% new_y_shifts = interp1(sh, cf', imag(shifts));
% shifts = new_x_shifts + 1i.*new_y_shifts;

% Eqn = 'a*sin(b*x + c)+d*x + e';
f = fit((sh), cf', 'poly1');

% figure(5)
% plot((sh), cf, 'LineWidth', 2, 'Color', 'k')
% hold on
% p2 = plot(f, 'k--');
% p2.LineWidth = 2;fontsize(gca,12,"points") ;
% xlabel('Shift [pixel]','FontSize',14) ;
% ylabel('Calibration factor [rad]','FontSize',14) ;
% pbaspect([1.618 1 1]) ;
% set(gca, 'LineWidth', 2);
% hold off

% figure(5)
% imagesc(angle(exp(1i.*phase_zernike)))
% axis square
% axis off
% colormap gray
% print('-f5','-depsc', 'C:\Users\Bronxville\Pictures\Aberration_correction_no_projection\measured_phase.eps') ;

fit_coef = f.p1;
% disp(fit_coef* (Nx/shack_hartmann.n_SubAp))
% disp(fit_coef)
% % %
shifts = shifts .* fit_coef;

shifts = reshape(shifts, shack_hartmann.n_SubAp_inter, shack_hartmann.n_SubAp_inter, []);

[X, Y] = meshgrid(1:shack_hartmann.n_SubAp_inter);
step = (shack_hartmann.n_SubAp_inter - 1) / range_x;
[Xq, Yq] = meshgrid(1:step:shack_hartmann.n_SubAp_inter - step);
half_Nx = floor(Nx / 2);

for i = 1:size(shifts, 3)

    Ay = -imag(shifts(:, :, i));
    Ax = -real(shifts(:, :, i));

    Ax = interp2(X, Y, Ax, Xq, Yq);
    Ay = interp2(X, Y, Ay, Xq, Yq);
    dx = 2 / range_x;
    dy = 2 / range_y;
    A = intgrad2(Ax, Ay, dx, dy, 0);

    if ~(isempty(phase_zernike))
        A = A - (A(half_Nx, half_Nx) - phase_zernike(half_Nx, half_Nx));
    else
        A = A - mean(A, "all");
    end

    A = permute(A, [2 1]);
    phase(pad_x + 1:pad_x + range_x, pad_y + 1:pad_y + range_y, i) = A;

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

mask = construct_mask(0, round(Nx / 2), Nx, Ny);

if ~isempty(phase_zernike)
    figure(9)
    subplot(2, 1, 1)
    imagesc(angle(exp(1i .* phase_zernike)))
    title('Projected on Zernike')
    axis square
    axis off
    colormap gray

    subplot(2, 1, 2)
    imagesc(angle(exp(1i .* phase)) .* mask)
    title('Gradient integration')
    axis square
    axis off
    colormap gray
end

%
% imwrite(mat2gray(angle(exp(1i.*phase_zernike))), 'C:\Users\Rakushka\Desktop\phase_function_original_zernike_central_subap.png');
% imwrite(mat2gray(angle(exp(1i.*phase))), 'C:\Users\Rakushka\Desktop\phase_function_original_integration_central_subap.png');

end
