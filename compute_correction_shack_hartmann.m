function correction = compute_correction_shack_hartmann(istream, cache, kernel, gw, complex_mask,...
                                         progress_bar, use_gpu, use_multithread,...
                                         p, registration_shifts, num_subapertures,...
                                         calibration_factor, subaperture_margin,...
                                         corrmap_margin, excluded_subapertures,...
                                         power_filter_corrector, sigma_filter_corrector,...
                                         varargin)
% Compute an optimal aberration correction given zernike
% indices.
%
% istream: either a valid CineReader or a RawReader
% cache: gui parameters
% kernel: reconstruction kernel
% gw: size of gaussian filter
% batch_size: number of frames in a batch
% batch_stride: number of frames to skip between each batches
% complex_mask: apply a fake aberration complex mask (Nx*Ny complex matrix)
%               ignored if empty
% progress_bar: gui progress bar to display computation progress
% use_gpu: uses GPU for hologram reconstructions
% use_multithread: enables parfor loops
% p: 1D array containing the indices of the zernikes to use for
%                   the optimization (1D indices from 0 onwards)
%
% [...]: shack hartmann parameters
% varargin = { previous_p, previous_coefs }
%
% previous_(p|coefs): optional, arrays containing informations about 
% previously computed corrections for preprocessing before computing the current correction.
%    p: 1D arrays containing indices of zernikes used for
%          previous correction
%    coefs: a 1D array containing coefs of the matching
%          zernikes for previous correction

% Prevent using the GPU in a parfor loop
% (that would be a terrible idea)
if use_multithread && use_gpu
    use_multithread = false;
end

nin = nargin; % local alias because nargin can't be used in parfor loops

% proxy variables to avoid
% broadcasting the entire gui to worker
% threads during parfor loop
Nx = istream.get_frame_width();
Ny = istream.get_frame_height();
j_win = cache.batch_size;
j_step = cache.batch_stride;
f1 = cache.registration_f1;
f2 = cache.registration_f2;
acquisition = DopplerAcquisition(Nx,Ny,cache.Fs/1000,cache.z,cache.wavelength,cache.DX,cache.DY,cache.pix_width,cache.pix_height);

% modify j_win and j_step if a batch_size_factor is provieded
% by user
if cache.batch_size_factor_flag
    batch_size_factor = cache.batch_size_factor;
    aberration_j_win = j_win * batch_size_factor;
    aberration_j_step = aberration_j_win; % j_step == j_win is constrained in gui
else
    batch_size_factor = 1;
    aberration_j_win = j_win;
    aberration_j_step = j_step;
end

% reset progress bar
num_batches = floor((istream.num_frames - aberration_j_win) / aberration_j_step);

phase_coefs = zeros(numel(p), num_batches);

if use_gpu || ~use_multithread
    parfor_arg = 0;
else
    parfor_arg = Inf;
end

initial_guess = zeros(1, numel(p));
if parfor_arg == Inf
    %% PARALLEL LOOP
    parfor batch_idx = 1:num_batches-1
        % load interferogram batch
        FH = istream.read_frame_batch(aberration_j_win, batch_idx * aberration_j_step);

        % load registration_shifts
        local_shifts = registration_shifts(:, batch_size_factor*(batch_idx-1) + 1:batch_size_factor*batch_idx);

        % compute FH
        FH = fftshift(fft2(FH)) .* kernel;
        if ~isempty(complex_mask)
            FH = FH .* complex_mask;
        end

        FH = register_FH(FH, local_shifts, j_win, batch_size_factor);

        if nin == 20 % change this value if function arguments are added or removed
            % if this parameter exist, then so does 'previous_p'
            previous_p = varargin{1};
            previous_coefs = varargin{2};

            [~, previous_zernikes] = zernike_phase(previous_p, Nx, Ny);
            previous_phase = 0;
            for i = 1:numel(previous_p)
                previous_phase = previous_phase + previous_coefs(i) * previous_zernikes(:,:,i);
            end

            % apply pervious correction
            FH = FH .* exp(-1i * previous_phase);
        end

        % FH is now registered and pre-processed, we now proceed to aberation
        % computation
        shack_hartmann = ShackHartmann(num_subapertures, p, calibration_factor, subaperture_margin, corrmap_margin, power_filter_corrector, sigma_filter_corrector);
        [M_aso, stiched_moments_M_aso] = shack_hartmann.construct_M_aso(f1, f2, gw, acquisition);
        
        if use_gpu
            FH = gpuArray(FH);
        end
        
        [shifts, stiched_moments_subap, stiched_corr_subapp] = shack_hartmann.compute_images_shifts(FH, f1, f2, gw, false, true, acquisition);
        
        % remove corners
        M_aso = mat_mask(M_aso, excluded_subapertures);
        shifts = mat_mask(shifts, excluded_subapertures);
        
        % separate x shifts from y shifts
        Y = cat(1, real(shifts), imag(shifts));
        M_aso_concat = cat(1,real(M_aso),imag(M_aso));
        
        % solve linear system
        coefs = M_aso_concat \ Y;   
        
        coefs = coefs * calibration_factor;
        
        phase_coefs(:, batch_idx) = coefs;

        % increment progress bar
        send(progress_bar, 0);
    end
else
    %% SEQUENTIAL LOOP
    %  This code is a duplicate from the loop above except it is sequencial.
    %  We can't just use a conditional parfor here because matlab wouldn't
    %  allow us to update the initial guess in the sequencial case.
    %  Please don't modify both loops if a modification is done. Otherwise
    %  the code could become a mess quickly
    for batch_idx = 1:num_batches-1
        % load interferogram batch
        FH = istream.read_frame_batch(aberration_j_win, batch_idx * aberration_j_step);

        % load registration_shifts
        local_shifts = registration_shifts(:, batch_size_factor*(batch_idx-1) + 1:batch_size_factor*batch_idx);

        % compute FH
        FH = fftshift(fft2(FH)) .* kernel;
        if ~isempty(complex_mask)
            FH = FH .* complex_mask;
        end

        FH = register_FH(FH, local_shifts, j_win, batch_size_factor);

        if nin == 20 % change this value if function arguments are added or removed
            % if this parameter exist, then so does 'previous_p'
            previous_p = varargin{1};
            previous_coefs = varargin{2};

            [~, previous_zernikes] = zernike_phase(previous_p, Nx, Ny);
            previous_phase = 0;
            for i = 1:numel(previous_p)
                previous_phase = previous_phase + previous_coefs(i) * previous_zernikes(:,:,i);
            end

            % apply pervious correction
            FH = FH .* exp(-1i * previous_phase);
        end

        % FH is now registered and pre-processed, we now proceed to aberation
        % computation
        shack_hartmann = ShackHartmann(num_subapertures, p, calibration_factor, subaperture_margin, corrmap_margin, power_filter_corrector, sigma_filter_corrector);
        [M_aso, stiched_moments_M_aso] = shack_hartmann.construct_M_aso(f1, f2, gw, acquisition);
        
        if use_gpu
            FH = gpuArray(FH);
        end
        
        [shifts, stiched_moments_subap, stiched_corr_subapp] = shack_hartmann.compute_images_shifts(FH, f1, f2, gw, false, true, acquisition);
        
        % remove corners
        M_aso = mat_mask(M_aso, excluded_subapertures);
        shifts = mat_mask(shifts, excluded_subapertures);
        
        % separate x shifts from y shifts
        Y = cat(1, real(shifts), imag(shifts));
        M_aso_concat = cat(1,real(M_aso),imag(M_aso));
        
        % solve linear system
        coefs = M_aso_concat \ Y;
        
        coefs = coefs * calibration_factor;
        
        phase_coefs(:, batch_idx) = coefs;

        % increment progress bar
        send(progress_bar, 0);
    end
end

correction = phase_coefs;
end