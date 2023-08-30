function phase = stitch_phase(shifts_inter,calibration_factor)
% calculate calibration factor
% [~,phi] = zernike_phase(2, 512, 512);
% phi = phi.*calibration_factor;
% transmittance = (exp(1i*phi));
% source = abs(fftshift(fftshift(ifft2(transmittance),1),2)).^2;
% [~, loc] = max(source, [], 'all');
% [a, b] = ind2sub([512 512], loc);
% b = b-258;

% A1 = real(shifts_inter);
% A2 = imag(shifts_inter);
% 
A1 = interp2(real(shifts_inter), 3);
A2 = interp2(imag(shifts_inter), 3);
% A1 = imresize(real(shifts_inter), [512 512]);
% A2 = imresize(imag(shifts_inter), [512 512]);
A = intgrad2(A1, A2, 1, 1, 0);
A = imresize(A, [512 512]);

% A = A.*calibration_factor;
A = A - mean(A, "all");

% figure(1)
% imagesc(A)
% axis square
% axis off

phase = exp(-1i .* A);
end
