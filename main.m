% Meta script - Corrects aberrations from .raw video file
% Available methods:
%   1 - Numerical Shack-Hartmann simulation
%   2 - Entropy optimization

% load parameters from config file
config;

% get interferogram filename
if cine_file
    [data_filename, data_path] = uigetfile('.cine');
else
    [data_filename, data_path] = uigetfile('.raw');
end

%% Construct InterferogramStream object
fullpath = fullfile(data_path, data_filename);
acquisition = DopplerAcquisition(Nx, Ny, fs, z, lambda, delta_x, delta_y, x_step, y_step);

if cine_file
    interferogram_stream = CineReader(fullpath);
    acquisition.Nx = interferogram_stream.frame_width;
    acquisition.Ny = interferogram_stream.frame_height;
    fs = interferogram_stream.frame_rate / 1000; % in kHz
else
    interferogram_stream = InterferogramStream(fullpath, endianness,acquisition, ...
                                           j_win, j_step);
    interferogram_stream.acquisition.Nx = Nx_before_crop;
    interferogram_stream.acquisition.Ny = Ny_before_crop;
end
             
%% Select which method to use                                
switch method
    case 1
        shack_hartmann = ShackHartmann(n_pup, n_mode, interp_factor);
    case 2
        entropy_opt = EntropyOptimization(f1, f2, n, m, min_constraint, ...
                                          max_constraint, initial_guess, ...
                                          mask_radiuses);
    case 3
        % do nothing
    otherwise
        error('Method does not exist. Use 1 for Shack Hartmann or 2 for entropy optimization')
end

%% Construct objects common to all methods
% wave propagation kernel
kernel = propagation_kernel(Nx, Ny, z, lambda, x_step, y_step, use_double_precision);

%% video i/o
data_fullpath = fullfile(data_path, data_filename);
data_file_info = dir(data_fullpath);
num_images = data_file_info.bytes / (2*Nx*Ny);

% setup output directory
[~, name] = fileparts(data_filename);
output_dir = sprintf('%s_jwin=%d_jstep=%d', name, j_win, j_step);
mkdir(output_dir);

% setup video writers
video_wr_aberrated = VideoWriter(fullfile(output_dir, 'aberrated.avi'));
video_wr_phase_corrector = VideoWriter(fullfile(output_dir, 'phase_corrector.avi'));
video_wr_corrected = VideoWriter(fullfile(output_dir, 'corrected.avi'));

video_wr_aberrated.FrameRate = 25;
video_wr_aberrated.Quality = 100;
video_wr_phase_corrector.FrameRate = 25;
video_wr_phase_corrector.Quality = 100;
video_wr_corrected.FrameRate = 25;
video_wr_corrected.Quality = 100;

open(video_wr_aberrated);
open(video_wr_phase_corrector);
open(video_wr_corrected);

%% Main loop
if cine_file
    num_batches = floor((interferogram_stream.num_frames - j_win) / j_step);
else
    num_batches = interferogram_stream.num_frame_batches();
end

% frame_batch = interferogram_stream.read_frame_batch(j_win, 1);
% frame_batch_2 = interferogram_stream.read_frame_batch(j_win, 3);
% FH = fftshift(fft2(frame_batch)); % reciprocal space of the 2 first dimensions of FH
% FH = FH .* kernel;
% if enable_hardware_acceleration
%     FH = gpuArray(FH);
% end

for batch_idx = 1:num_batches-1
    disp(batch_idx);
    if cine_file
        frame_batch = interferogram_stream.read_frame_batch(j_win, batch_idx * j_step);
    else
        frame_batch = interferogram_stream.read_batch(batch_idx);
    end

%     if mod(batch_idx - 1, 2) == 1 && batch_idx ~= 2 && batch_idx ~= num_batches - 1
%         %% load next batch
%         frame_batch = frame_batch_2;
%         frame_batch_2 = interferogram_stream.read_frame_batch(j_win, batch_idx + 2);
%     end

    if crop
       x_offset = floor((Nx_before_crop - Nx) / 2);
       y_offset = floor((Ny_before_crop - Ny) / 2);
       frame_batch = frame_batch(x_offset:x_offset+Nx, y_offset:y_offset+Ny, :);
    end
    
%     switch mod(batch_idx - 1, 3)
%         case 0
%             FH = gpuArray(fftshift(fft2(frame_batch)) .* kernel);
%         case 1
%             FH(:,:,1:j_win/2) = FH(:,:,j_win/2+1:end);
%             FH(:,:,j_win/2+1:end) = gpuArray(fftshift(fft2(frame_batch_2(:,:,1:j_win/2))) .* kernel);
%         case 2
%             FH = gpuArray(fftshift(fft2(frame_batch_2)) .* kernel);
%     end
    
    %% interferograms pre-treatment
    FH = fftshift(fft2(frame_batch)); % reciprocal space of the 2 first dimensions of FH
    FH = FH .* kernel;
    if enable_hardware_acceleration
        FH = gpuArray(FH);
    end
    
    %% compute aberrated hologram
    hologram_aberrated = reconstruct_hologram(FH, f1, f2, acquisition, gaussian_width, enable_hardware_acceleration);
    
    % add 8 defocus
%     [p, ze] = zernike_phase([16; 0; 0], Nx, Ny);
%     FH = FH .* exp(1i.*compute_phase_correction([16; 0; 0],ze)); 
    % TODO fonction pour plot des images avec plusieurs aberrations
    % differentes
    
    %% perform aberration compensation with selected method
    switch method
        case 1
            % Shack Hartmann
            % construct calibration matrix
            M_aso = shack_hartmann.construct_M_aso(acquisition, gaussian_width, enable_hardware_acceleration);            
            
            % rename shift_array
            shifts = shack_hartmann.compute_images_shifts(FH, false, acquisition, f1, f2, gaussian_width, enable_hardware_acceleration);
            Y = cat(1, real(shifts), imag(shifts));
            M_aso_concat = cat(1,real(M_aso),imag(M_aso));
            X = M_aso_concat \ Y;
            
            [phase, zernikes] = zernike_phase(X, Nx, Ny);
            figure(1)
            imagesc(phase);
            colorbar
            
            % plot shifts in 2D
            plot_shifts(shifts, n_pup, Nx, Ny);

        case 2
            % Entropy optimization
            X = entropy_opt.optimize(FH, f1, f2, acquisition, gaussian_width, 0.4, enable_hardware_acceleration);
            display(batch_idx, 'batch_idx');
            display(X, 'X');
    end
    
%     %% apply correction
%     zernikes = evaluate_zernikes(n, m, Nx, Ny);
%     phase_correction = compute_phase_correction(X/10, zernikes);
%     hologram_corrected = reconstruct_hologram(FH, f1, f2, acquisition, gaussian_width, enable_hardware_acceleration, phase_correction);
%     
%     figure(2)
%     imshow(mat2gray(hologram_corrected));
%     figure(3)
%     imshow(mat2gray(hologram_aberrated));
    
    
    %% write video files
    writeVideo(video_wr_aberrated, mat2gray(hologram_aberrated));
%     writeVideo(video_wr_phase_corrector, mat2gray(phase_correction));
%     writeVideo(video_wr_corrected, mat2gray(hologram_corrected));
end

close(video_wr_aberrated);
close(video_wr_phase_corrector);
close(video_wr_corrected);

