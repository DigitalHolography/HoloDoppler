function J = objective2(FH, coefs, zernike_eval, f1, f2, mask, acquisition, gaussian_width, use_gpu)  
    % appeler cost function
    phase_correction = compute_phase_correction(coefs, zernike_eval);

    %% compute corrected hologram
    moment = reconstruct_hologram(FH, f1, f2, acquisition, gaussian_width, use_gpu, phase_correction);
    moment = mat2gray(abs(ifft2(fft2(moment) .* fftshift(mask))));

%     J = gather(sum(sum(moment.^0.75)));
    J = gather(entropy(moment) / norm(stdfilt(moment).^2));
%     J = gather(norm(stdfilt(moment(50:450, 50:450)).^2));
%     J = norm(imgradient(gather(moment)));
%     J = gather(entropy(moment));
%     J = -gather((max(moment(:)) - min(moment(:)) / (max(moment(:)) + min(moment(:))))); % contrast
end