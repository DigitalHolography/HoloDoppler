function [objective_fn] = objective_segmented(batch, zernike_eval, kernel, f1, f2, fs, mask, delta_x, delta_y, gaussian_width, max_gpu_batch_size)
if size(batch, 3) < max_gpu_batch_size
    objective_fn = objective(batch, zernike_eval, kernel, f1, f2, fs, mask, delta_x, delta_y, gaussian_width, true);
    return;
end

%% complex valued hologram
FH = fftshift(fft2(batch));
FH = FH .* kernel;

    function [J] = objective_segmented_impl(FH, coefs, zernike_eval, f1, f2, fs, mask, delta_x, delta_y, gaussian_width, max_gpu_batch_size)
        j_win = size(FH, 3);
        n1 = round(f1 * j_win / fs);
        n2 = round(f2 * j_win / fs);
        
        %% move small data to gpu
        mask = gpuArray(mask);
        zernike_eval = gpuArray(zernike_eval);
        phase_correction = compute_phase_correction(coefs, zernike_eval);
        
        num_segments = floor(j_win / max_gpu_batch_size);
        moments = zeros(size(FH, 1), size(FH, 2), num_segments);
        
        for i = 1:num_segments
            % move segment to gpu
            if i ~= num_segments
                FH_segment = gpuArray(FH(:, :, (i - 1) * max_gpu_batch_size + 1:i * max_gpu_batch_size));
            else
                FH_segment = gpuArray(FH(:, :, (i - 1) * max_gpu_batch_size + 1:end));
            end
            
            FH_segment = FH_segment .* exp(-1i * phase_correction);
            H = ifft2(FH_segment);
            clear FH_segment;
            
            SH = fft(H, [], 3);
            clear H;
            SH = abs(SH).^2;
            SH = permute(SH, [2 1 3]);
            SH = circshift(SH, [delta_x, delta_y, 0]);
            
            if (i - 1) * max_gpu_batch_size + 1 < n1
                n1_local =  n1 - (i - 1) * max_gpu_batch_size - 1; 
            else
                n1_local = 1;
            end
            if i * max_gpu_batch_size > n2
                n2_local = max_gpu_batch_size - (i * max_gpu_batch_size - n2);
            else
                n2_local = max_gpu_batch_size;
            end
            
            if n2_local < 1
                break;
            end
            
            if i ~= num_segments
                moment = sum(abs(SH(:, :, n1_local:max_gpu_batch_size)), 3);
            else
                moment = sum(abs(SH(:, :, 1:n2_local)), 3);
            end
            clear SH;
            moments(:, :, i) = gather(moment);
            clear moment;
        end
        
        % send back moments tu gpu for second pass
        moments = gpuArray(moments);
        moment = squeeze(sum(moments, 3));
        clear moments;
        moment = moment ./ imgaussfilt(moment, gaussian_width);
        moment = mat2gray(abs(ifft2(fft2(moment) .* fftshift(mask))));
        
        J = gather(entropy(moment(50:450, 50:450)) / norm(stdfilt(moment(50:450, 50:450)).^2));
    end

objective_fn = @(coefs)objective_segmented_impl(FH, coefs, zernike_eval, f1, f2, fs, mask, delta_x, delta_y, gaussian_width, max_gpu_batch_size);
end