function [shifts] = compute_images_shifts(obj, FH, calibration, acquisition, f1, f2, gaussian_width, use_gpu)
%  FH
% calibration: flag to compute shifts from a 2d array, e.g. FH(x,y) = exp(1i*phi(x,y))
% acquisition
% f1, f2
% gaussian_width
% use_gpu

% performs shack-hartman simulation
ac = acquisition;

% shifts is a 1D vector
% it maps the 2D pupils grid by iterating column first
% example of ordering for a 4x4 pupil grid
% 1  5  9 13
% 2  6 10 14
% 3  7 11 15
% 4  8 12 16
shifts = zeros(obj.n_pup^2, 1);

moment_chunks = zeros(ac.Nx,ac.Ny);
for pup_x = 1:obj.n_pup
    for pup_y = 1:obj.n_pup
        FH_chunk = FH((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup), :);

        if calibration
            % if M_aso was not found in cache, construct its shifts
            % instead of runing the simulation
            
            % propagate wave
            H_chunk = abs(fftshift(fft2(FH_chunk))).^2;
            moment_chunks((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup)) = H_chunk;
        else
%             FH_chunk = fftshift(fft2(FH_chunk));
            moment_chunk = reconstruct_hologram_no_shifts(FH_chunk, f1, f2, acquisition, gaussian_width, use_gpu);
            moment_chunks((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup)) = moment_chunk;
        end
    end
end

% moment_chunks = fftshift(moment_chunks);
stacked_moment_chunks = zeros(floor(ac.Nx/obj.n_pup), floor(ac.Ny/obj.n_pup), obj.n_pup^2);
for pup_x = 1:obj.n_pup
    for pup_y = 1:obj.n_pup
        stacked_moment_chunks(:,:,1 + (pup_x - 1) + obj.n_pup * (pup_y - 1)) = ...
            moment_chunks((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), ...
            (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup));
    end
end
moment_chunks = stacked_moment_chunks;

% reference pupil
% we take one of the four in the center as a reference
% we then compute shifts of all images to the reference images
ref_pup = floor(obj.n_pup/2) * (obj.n_pup - 1);
% ref_pup = 1;

for pup_x = 1:obj.n_pup
    for pup_y = 1:obj.n_pup
        FFT_ref = fft2(moment_chunks(:,:,ref_pup));

        V = moment_chunks(:, :, 1 + (pup_y - 1) + obj.n_pup * (pup_x - 1));
        [output, ~] = dftregistration(FFT_ref,fft2(V),obj.interp_factor);
        dx = -output(4);
        dy = -output(3);
        shifts(1 + (pup_y - 1) + obj.n_pup * (pup_x - 1)) = dx + 1i * dy;
        
%           c = normxcorr2(moment_chunks(:,:,ref_pup), moment_chunks(:,:,1 + (pup_x - 1) + obj.n_pup * (pup_y - 1)));
%           [xpeak, ypeak] = find(c==max(c(:)));
%           yoffSet = ypeak-size(moment_chunks(:,:,ref_pup), 1);
%           xoffSet = xpeak-size(moment_chunks(:,:,1 + (pup_x - 1) + obj.n_pup * (pup_y - 1)), 2);
%           shifts(1 + (pup_x - 1) + obj.n_pup * (pup_y - 1)) = xoffSet(end) + 1i * yoffSet(end);
    end
end
end
