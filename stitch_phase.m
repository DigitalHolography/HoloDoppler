function phase = stitch_phase(shifts, phase_zernike, ac, shack_hartmann)

magic_number = 710;

SubAp_Nx = floor(ac.Nx/shack_hartmann.n_SubAp);
SubAp_Ny = floor(ac.Ny/shack_hartmann.n_SubAp);



shifts = shifts .* (ac.Nx/shack_hartmann.n_SubAp);
disp(shifts)
shifts = reshape(shifts, shack_hartmann.n_SubAp_inter, shack_hartmann.n_SubAp_inter);
% shifts = (shifts');

%normalize shifts
stride = floor((ac.Nx-SubAp_Nx)/(shack_hartmann.n_SubAp_inter-1));
% padding = floor((SubAp_Nx/stride - 1)/2);
% padding = floor(SubAp_Nx/2) - floor(stride/2);


%% calculate calibration factor
% % [~, tilt] = zernike_phase(2, SubAp_Nx, SubAp_Ny);
% [~, defocus] = zernike_phase(2, stride, stride);
% calibration_factor = shack_hartmann.calibration_factor;
% shifts = floor(shifts .* calibration_factor);
% defocus_phase = exp(1i .* (defocus .* 1));
% spot = (fftshift(fftshift(ifft2(defocus_phase),1),2));
% 
% for idx = 1 : size(shifts, 1)
%     for idy = 1 : size(shifts, 2)
%         tmp = circshift(circshift(spot, real(shifts(idx, idy)), 2), imag(shifts(idx, idy)), 1);
%         phaselet = fft2(fftshift(fftshift(tmp,1),2));
%         range_x = padding + (idx - 1)*stride + 1 : padding + idx*stride; 
%         range_y = padding + (idy - 1)*stride + 1 : padding + idy*stride; 
%         phase(range_x, range_y) = phaselet;
%     end
% end
% 
% figure(1)
% imagesc(angle(phase))

% OLD CODE
[~, tilt] = zernike_phase(5, ac.Nx, ac.Ny);

cf = linspace(0.01, 60, 50);
sh = zeros(50, 1);

for i = 1 : 50
% %     disp(i);
% %     [~, tilt] = zernike_phase(2, 100 + 10*i, 100 + 10*i);
    calibration_factor = cf(i);
% %     s = cf(i);
    tilt_tmp = tilt;
    tilt_phase_pos = exp(1i .* (tilt_tmp .* calibration_factor));
%     spot_pos = abs(fftshift(fftshift(ifft2(tilt_phase_pos),1),2)).^2;
% %     FH_tmp = FH.*spot_pos;
    [phase_shifts,~,~] = shack_hartmann.compute_images_shifts(tilt_phase_pos, 6, 33, 35, true, true, ac);
%     tilt_phase_neg = exp(1i .* (-tilt_tmp .* calibration_factor));
%     spot_neg = abs(fftshift(fftshift(ifft2(tilt_phase_neg),1),2)).^2;
%     c = normxcorr2(spot_pos,spot_neg);
%     [xpeak_aux, ypeak_aux] = find(c==max(c(:)));
%     xpeak = xpeak_aux+0.5*(c(xpeak_aux-1,ypeak_aux)-c(xpeak_aux+1,ypeak_aux))/(c(xpeak_aux-1,ypeak_aux)+c(xpeak_aux+1,ypeak_aux)-2.*c(xpeak_aux,ypeak_aux));
%     ypeak = ypeak_aux+0.5*(c(xpeak_aux,ypeak_aux-1)-c(xpeak_aux,ypeak_aux+1))/(c(xpeak_aux,ypeak_aux-1)+c(xpeak_aux,ypeak_aux+1)-2.*c(xpeak_aux,ypeak_aux));
%     xoffSet = ceil(size(c, 1)/2) - xpeak;
%     yoffSet = ceil(size(c, 2)/2) - ypeak;
%     shift_tilt = (xoffSet + 1i * yoffSet)/2;
%     shifts = shifts/(abs(yoffSet/2)/0.0131);
    sh(i) = real(phase_shifts(ceil(shack_hartmann.n_SubAp_inter/2)));
%     sh(i) = yoffSet;
end
% % 
f = fit(abs(sh), cf', 'poly1');
figure(5)
plot(abs(sh), cf)
hold on
plot(f)
hold off

disp(f.p1);
fit_coef = f.p1;

shifts = shifts.*fit_coef;

% gradient_calibration_factor = shack_hartmann.calibration_factor/(floor(shack_hartmann.n_SubAp_inter/2)*abs(imag(shift_tilt)));
% shift_tilt = shift_tilt * gradient_calibration_factor;

% shifts_tilt = ones(size(shifts)) .* shift_tilt;
% Ay = -real(shifts_tilt);
% Ax = -imag(shifts_tilt);
% 
% % A1 = interp2(real(shifts_inter), 3);
% % A2 = interp2(imag(shifts_inter), 3);
% % A1 = imresize(real(shifts_inter), [512 512]);
% % A2 = imresize(imag(shifts_inter), [512 512]);
% A = intgrad2(Ax, Ay, 1, 1, 0);
% A = A - mean(A, "all");
% 
% %% calibrate shifts
% shifts = shifts .* gradient_calibration_factor;
% % shifts_inter = shifts_inter./calibration_factor;

Ay = imag(shifts);
Ax = real(shifts);

[X, Y] = meshgrid(1 : size(Ax));
step = (size(Ax)-1) / 512;
[Xq ,Yq] = meshgrid(1 : step : size(Ax) - step);
Ax = interp2(X, Y, Ax, Xq, Yq);
Ay = interp2(X, Y, Ay, Xq, Yq);
% A1 = imresize(real(shifts_inter), [512 512]);
% A2 = imresize(imag(shifts_inter), [512 512]);
% dx = SubAp_Nx;
% dy = SubAp_Ny;
dx = 1/ac.Nx;
dy = 1/ac.Ny;
A = intgrad2(Ax, Ay, dx, dy, 0);
A = A - mean(A, "all");

[Fx, Fy] = gradient(A);


% A_temp = zeros(size(A,1)+2*padding, size(A,2)+2*padding);
% A_temp(padding+1:end-padding, padding+1:end-padding) = A;
% A = permute(A, [2 1]); 

% [X, Y] = meshgrid(1 : size(A_temp));
% step = (size(A_temp)-1) / 512;
% [Xq ,Yq] = meshgrid(1 : step : size(A_temp) - step);
% A_interp = interp2(X, Y, A, Xq, Yq);
% 
% A = A_interp;

% A = A - mean(A, "all");
disp(max(A,[], 'all') - min(A,[], 'all'))
A = A .* shack_hartmann.n_SubAp;

figure(1)
imagesc(A)
% surf(X, Y, A)
axis square
axis off

phase = exp(-1i .* A);

[phase_shifts,~,~] = shack_hartmann.compute_images_shifts(phase, 1, 1, 1, true, true, ac);

phase_shifts  = reshape(phase_shifts, [shack_hartmann.n_SubAp_inter shack_hartmann.n_SubAp_inter]);


if ~isempty(phase_zernike)
    figure(9)
    subplot(2,1,1)
    imagesc(angle(exp(1i.*phase_zernike)))
    title('Projected on Zernike')
    axis square
    axis off

    subplot(2,1,2)
    imagesc(angle(phase))
    title('Measured')
    axis square
    axis off

    figure(10)
    subplot(2,2,1);
    imagesc(real(shifts))
    title('Real shifts')
    % clim([-0.06, 0.06])
    axis square
    axis off

    subplot(2,2,2);
    imagesc(imag(shifts))
    title('Imag shifts')
    % clim([-0.06, 0.06])
    axis square
    axis off

    subplot(2,2,3);
    imagesc(real(phase_shifts))
    title('Real phase shifts')
    % clim([-0.06, 0.06])
    axis square
    axis off

    subplot(2,2,4);
    imagesc(imag(phase_shifts))
    title('Imag phase shifts')
    % clim([-0.06, 0.06])
    axis square
    axis off
end
By = -imag(shifts);
Bx = -real(shifts);

[X, Y] = meshgrid(1 : size(Bx));
step = (size(Bx)-1) / 512;
[Xq ,Yq] = meshgrid(1 : step : size(Bx) - step);
Bx = interp2(X, Y, Bx, Xq, Yq);
By = interp2(X, Y, By, Xq, Yq);
% A1 = imresize(real(shifts_inter), [512 512]);
% A2 = imresize(imag(shifts_inter), [512 512]);
B = intgrad2(Bx, By, 1, 1, 0);

figure(2)
imagesc(B)
axis square
axis off

end
