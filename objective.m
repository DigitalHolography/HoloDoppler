function [objective_fn] = objective(batch, zernike_eval, kernel, f1, f2, fs, mask, delta_x, delta_y, gaussian_width, use_gpu)  
    %% complex valued hologram
    FH = fftshift(fft2(batch));
    FH = FH .* kernel;
    
    % move data to gpu if available
    if use_gpu
        FH = gpuArray(FH);
        mask = gpuArray(mask);
        zernike_eval = gpuArray(zernike_eval);
    end
    
    % appeler cost function
    function [J] = objective_impl(FH, coefs, zernike_eval, f1, f2, fs, mask, delta_x, delta_y, gaussian_width)
        j_win = size(FH, 3);
        phase_correction = compute_phase_correction(coefs, zernike_eval);
        
        %% compute corrected hologram
        FH = FH .* exp(-1i * phase_correction);
        H = ifft2(FH);
        clear FH;
        
        %% compute corrected squared magnitude
        SH = fft(H, [], 3);
        clear H;
        SH = abs(SH).^2;
        SH = permute(SH, [2 1 3]);
        SH = circshift(SH, [delta_x, delta_y, 0]);
        
        %% compute corrected moment
        % convert frequency bounds to indices bounds
        n1 = round(f1 * j_win / fs);
        n2 = round(f2 * j_win / fs);
        moment = squeeze(sum(abs(SH(:, :, n1:n2)), 3));
        moment = moment ./ imgaussfilt(moment, gaussian_width);
        moment = mat2gray(abs(ifft2(fft2(moment) .* fftshift(mask))));
        
%         J = gather(sum(sum(moment.^0.75)));
        J = gather(entropy(moment) / norm(stdfilt(moment).^2));
%         J = gather(norm(stdfilt(moment(50:450, 50:450)).^2));
%         J = -norm(imgradient(gather(moment(50:450, 50:450))));
%         J = gather(entropy(moment));
    end
    objective_fn = @(coefs)objective_impl(FH, coefs, zernike_eval, f1, f2, fs, mask, delta_x, delta_y, gaussian_width);
end