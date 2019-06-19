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

% reference pupil
% we take one of the four in the center as a reference
% we then compute shifts of all images to the reference images
ref_pup = floor(obj.n_pup/2) * (obj.n_pup - 1);
% ref_pup = 1;

moment_chunks = zeros(ac.Nx,ac.Ny);

% 4D correlation array
chunk_cors = zeros(2*floor(ac.Nx/obj.n_pup) - 1, 2*floor(ac.Ny/obj.n_pup) - 1, obj.n_pup^2, size(FH,3));
if calibration
    for pup_x = 1:obj.n_pup
        for pup_y = 1:obj.n_pup
            FH_chunk = FH((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup), :);
            
            % if M_aso was not found in cache, construct its shifts
            % instead of runing the simulation

            % propagate wave
            H_chunk = abs(fftshift(fft2(FH_chunk))).^2;
            moment_chunks((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup)) = H_chunk;
        end
    end
else
    mid_pup = floor(obj.n_pup/2);
    FH_ref_chunk = FH((mid_pup-1)*floor(ac.Nx/obj.n_pup) + 1:mid_pup*floor(ac.Nx/obj.n_pup), (mid_pup-1)*floor(ac.Ny/obj.n_pup) + 1:mid_pup*floor(ac.Ny/obj.n_pup), :);
    H_ref_chunk = ifft2(FH_ref_chunk);
    SH_ref_chunk = fft(H_ref_chunk,[],3);
    hologram_ref_chunk = abs(SH_ref_chunk).^2;
    
    for pup_x = 1:obj.n_pup
        for pup_y = 1:obj.n_pup
            FH_chunk = FH((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup), :);
            H_chunk = ifft2(FH_chunk);
            SH_chunk = fft(H_chunk,[],3);
            hologram_chunk = abs(SH_chunk).^2; % stack of holograms
            
            % 3D array
            c = zeros(2*size(hologram_chunk, 1) - 1, 2*size(hologram_chunk, 2) - 1, size(hologram_chunk, 3));
            for kk = 1:size(c,3)
                c(:,:,kk) = normxcorr2(hologram_chunk(:,:,kk), hologram_ref_chunk(:,:,kk));
            end
            
            % assign 3D array into 3D view of 4D array
            chunk_cors(:,:,1 + (pup_y - 1) + obj.n_pup * (pup_x - 1), :) = c;
              
%             FH_chunk = fftshift(fft2(FH_chunk));
%             moment_chunk = reconstruct_hologram_no_shifts(FH_chunk, f1, f2, acquisition, gaussian_width, use_gpu);
%             moment_chunks((pup_x-1)*floor(ac.Nx/obj.n_pup) + 1:pup_x*floor(ac.Nx/obj.n_pup), (pup_y-1)*floor(ac.Ny/obj.n_pup) + 1:pup_y*floor(ac.Ny/obj.n_pup)) = moment_chunk;

        end
    end
    
    % here chunk_cors is constructed
    % sum all correlations
    
    % 3D array
%     cors = sum(chunk_cors, 4);
    cors = abs(fft(chunk_cors,4)).^2;
    % then find shifts
    for pup_x = 1:obj.n_pup
        for pup_y = 1:obj.n_pup
            c = cors(:,:,1 + (pup_x - 1) + obj.n_pup * (pup_y - 1));
            [xpeak, ypeak] = find(c==max(c(:)));
            yoffSet = ypeak - size(cors(:,:,ref_pup), 1)/2;
            xoffSet = xpeak - size(cors(:,:,1 + (pup_x - 1) + obj.n_pup * (pup_y - 1)), 2)/2;
            shifts(1 + (pup_x - 1) + obj.n_pup * (pup_y - 1)) = xoffSet + 1i * yoffSet;
        end
    end
    return
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
