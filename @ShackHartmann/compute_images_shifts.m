function [shifts] = compute_images_shifts(obj, FH, calibration, acquisition, f1, f2, gaussian_width, use_gpu)
% performs shack-hartman simulation
ac = acquisition;

shifts = zeros(obj.n_pup, obj.n_pup);

moment_chunks = zeros(ac.Nx,ac.Ny);
for pup_x = 1:obj.n_pup
    for pup_y = 1:obj.n_pup
        FH_chunk = FH((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup), :);

        if calibration
            % if M_aso was not found in cache, construct its shifts
            % instead of runing the simulation
            FH_chunk = FH((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup), :);
            FH_chunk = abs(ifft2(FH_chunk)).^2;
            moment_chunks((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup)) = FH_chunk;
        else
            moment_chunk = reconstruct_hologram(FH_chunk, f1, f2, acquisition, gaussian_width, use_gpu);
            moment_chunk = moment_chunk ./ mean2(moment_chunk);
            moment_chunks((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup)) = moment_chunk;
        end
    end
end

moment_chunks = fftshift(moment_chunks);
moment_chunks = reshape(moment_chunks, floor(ac.Nx/obj.n_pup), floor(ac.Ny/obj.n_pup), obj.n_pup^2);

for pup_x = 1:obj.n_pup
    for pup_y = 1:obj.n_pup
        FFT_ref = fft2(moment_chunks(:,:,1));

        V = moment_chunks(:, :, 1 + (pup_x - 1) + obj.n_pup * (pup_y - 1));
        [output, ~] = dftregistration(FFT_ref,fft2(V),obj.interp_factor);
        dx = -output(4);
        dy = -output(3);
        shifts(pup_x, pup_y) = dx + 1i * dy;
    end
end
end