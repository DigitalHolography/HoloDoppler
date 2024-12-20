function Rendervideo(app)
% main program loop
% Select a file and call other functions
% to perform a full computation and create
% output videos.

if strcmp(app.outputvideoDropDown.Value, 'dark field') && (app.z_reconstruction == app.z_iris)
    app.Switch.Value = 'z_retina';
    app.ZSwitchValueChanged();
end

if ~app.file_loaded
    return
end

% start clock to monitor
% computation duration

tic;

ToolBox = ToolBoxClass(app);
[path, path_png, path_txt, ~, ~, path_log, path_mat] = getPaths(obj);

% save all gui parameters to a struct.
% The current computation will fetch every parameter
% from the cache and not from the gui.
% The purpose of this is to prevent gui interactions
% to mess up the parameters while a computation is ongoing.
set_up = app.setUpDropDown.Value;

app.cache = GuiCache(app);
num_workers = app.cache.nb_cpu_cores;

aberration_correction = AberrationCorrection();
image_registration = ImageRegistration();

% select parallelism policy
switch app.cache.parallelism
    case 'CPU multithread'
        %                     parfor_arg = app.numCPUCores(0.2);
        % parfor_arg = Inf;
        parfor_arg = num_workers;
        use_multithread = true;
        use_gpu = false;
    case 'GPU parallelization'
        parfor_arg = 3;
        use_multithread = false;
        reset(gpuDevice(1)); % clear memory
        use_gpu = check_GPU_for_render(app, parfor_arg);
    case 'CPU singlethread'
        parfor_arg = 0;
        use_multithread = false;
        use_gpu = false;
    case 'CPU/GPU rendering/optim'
        % TODO
        % parfor_arg = app.numCPUCores(0.2);
        % parfor_arg = Inf;
        parfor_arg = num_workers;
        use_multithread = true;
        reset(gpuDevice(1));
        use_gpu = check_GPU_for_render(app);

end

if use_gpu
    disp("Using GPU.")
else
    disp("Not using GPU.")
end

istream = app.interferogram_stream;

batchSize = app.cache.batch_size;
batchSizeRef = app.refbatchsizeEditField.Value;
batchStride = app.cache.batch_stride;

time_transform = app.cache.time_transform;
blur = app.cache.blur;

numX = app.Nx;
numY = app.Ny;
numFrames = istream.num_frames;
numBatches = floor((numFrames - batchSize) / batchStride);

fs = app.fs;
wavelength = app.cache.wavelength;
isSvd = app.SVDCheckBox.Value;
output_video = app.cache.output_videos;
rephasing = app.cache.rephasing;
isLowMemory = app.cache.low_memory;
spatialTransformation = app.cache.spatialTransformation;
temporalFilter = app.cache.temporal_filter;
SubAp_PCA.Value = app.SubAp_PCA.Value;
SubAp_PCA.min = app.SubAp_PCA.min;
SubAp_PCA.max = app.SubAp_PCA.max;
isTemporal = app.temporalCheckBox.Value;
phi1 = app.phi1EditField.Value;
phi2 = app.phi2EditField.Value;
isSpatial = app.spatialCheckBox.Value;
nu1 = app.nu1EditField.Value;
nu2 = app.nu2EditField.Value;
volume_size = floor(batchSize / 2);
isSVDx = app.SVDxCheckBox.Value;
SVDx_SubAp_num = app.SVDx_SubApEditField.Value;
isSVDThreshold = app.SVDThresholdCheckBox.Value;
SVDThreshold = app.SVDThresholdEditField.Value;
SVDStride = app.SVDStrideEditField.Value;
num_F = app.numFreqEditField.Value;

if ~isempty(app.image_registration)
    local_image_registration = cat(1, app.image_registration.translation_x, app.image_registration.translation_y);

    if size(local_image_registration, 2) == floor((numFrames - batchSize) / batchStride) % if registration from previous folder results
        disp('found last registration that will be used.')
    end

else
    local_image_registration = [];
end

% FIXME : add new elements to cache

if rephasing
    rephasing_data = app.rephasing_data;
else
    rephasing_data = [];
end

switch spatialTransformation
    case 'angular spectrum'
        kernel = app.kernelAngularSpectrum; % propagation kernel initialization
    case 'Fresnel'
        kernel = app.kernelFresnel; % propagation kernel initialization
end

acquisition = DopplerAcquisition(numX, numY, fs / 1000, app.cache.z, app.cache.z_retina, app.cache.z_iris, app.cache.wavelength, app.cache.DX, app.cache.DY, app.cache.pix_width, app.cache.pix_height);

isLowFrequency = app.cache.low_frequency;
color_f1 = app.cache.color_f1;
color_f2 = app.cache.color_f2;
color_f3 = app.cache.color_f3;
xystride = app.cache.xystride;
num_unit_cells_x = app.cache.num_unit_cells_x;
r1 = app.cache.r1;
imageTypeList = ImageTypeList();

if isLowMemory
    output_filename = sprintf('%s_M0_tmp.%s', ToolBox.HD_name, 'raw');
    fd_M0 = fopen(sprintf('%s\\%s', path, output_filename), 'w');
else

    switch output_video
        case 'power_Doppler'
            imageTypeList.select('power_Doppler');
            video_M0 = zeros(numX, numY, 1, numBatches, 'single');

        case 'moments'
            imageTypeList.select('power_Doppler', 'moment_0', 'moment_1', 'moment_2');
            video_M0 = zeros(numX, numY, 1, numBatches, 'single');
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;

        case 'all_videos'
            app.time_transform.type = 'FFT';
            imageTypeList.select('power_Doppler', 'power_1_Doppler', 'power_2_Doppler', 'color_Doppler', 'directional_Doppler', 'M0sM1r', 'velocity_estimate', 'spectrogram', 'moment_0', 'moment_1', 'moment_2')

            video_M0 = zeros(numX, numY, 1, numBatches, 'single');
            video_M1 = video_M0;
            video_M2 = video_M0;
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;
            video_M1_over_M0 = video_M0;
            video_M2_over_M0 = video_M0;
            video_M_freq_low = video_M0;
            video_M_freq_high = video_M0;
            video_M0_pos = video_M0;
            video_M0_neg = video_M0;
            video_M0sM1r = video_M0;

            video_velocity = zeros(numX, numY, 3, numBatches, 'single');

            video_directional = zeros(numX, numY, 3, numBatches, 'single');
            video_fmean = video_directional;

            % video_mask = video_M0;
            % psf_through_time = video_M0;
            % spectrogram_array = zeros(j_win, numBatches, 'single');

            %FIX ME binx biny bint binw à paramétriser et
            %mettre dans le .mat + config
            bin_x = 4;
            bin_y = 4;
            bin_t = 1;
            bin_w = 16;
            % SH_time = zeros(numX, numY, 1, j_win, 1, 'single');
            %FIX ME prévoir les cas ou ça tombe pas entier
            SH_time = zeros(numX / bin_x, numY / bin_y, 1, batchSize / bin_w, ceil(numBatches / bin_t), 'single');
            % SH_time = zeros(256, 256, 1, 32, ceil(numBatches/bin_t), 'single');
            % tmp_SH = zeros(numX, numY, 1, j_win,ceil(numBatches/bin_t), 'single');
            % idx_tab_SH_time = 1:ceil(numBatches/bin_t);
            % idx_tab_SH_time = repmat(idx_tab_SH_time,2,1);
            % idx_tab_SH_time = reshape(idx_tab_SH_time,[],1);s

        case 'dark_field'
            imageTypeList.select('dark_field_image');
            H_dark_field_stack = 1i * ones(numX, numY, batchSize, numBatches, 'single');
            video_M0_dark_field = zeros(numX, numY, 1, numBatches, 'single');

        case 'choroid'
            imageTypeList.select('power_Doppler', 'moment_0', 'moment_1', 'moment_2', 'choroid');
            video_M0 = zeros(numX, numY, 1, numBatches, 'single');
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;
            images_choroid =  zeros(numX, numY, 1, numBatches, num_F, 'single');
            video_M_freq_low = video_M0;
            video_M_freq_high = video_M0;


    end %switch local_output_video

end

% parfor waitbar
% we have to use a DataQueue
% since there are no synchronization
% primitives in matlab (mutex)
D = parallel.pool.DataQueue;
h = waitbar(0, '');
afterEach(D, @update_waitbar);
N = double(numBatches - 1);
p = 1;

%% first pass - compute shifts for video registration
registration_pass = app.cache.registration_via_phase;

if registration_pass
    current_batchIdx = 1 + floor(app.positioninfileSlider.Value / (batchSize + batchStride));
    shifts = compute_temporal_registration(istream, app.cache, batchSize, batchStride, current_batchIdx, blur, ...
        kernel, [], D, use_multithread);
    % tilts zernikes used for translating an image
    zernikes = evaluate_zernikes([1 1], [1 -1], numX, numY);
else
    % declare unused variables to make matlab parfor
    % loop parser happy - stupid matlab
    shifts = zeros(3, numBatches, 'single');
    zernikes = zeros(numX, numY, 2, 'single');
end

enable_iterative_optimization = app.IterativeoptimizationCheckBox.Value;
enable_shack_hartmann = app.ShackHartmannCheckBox.Value;
zernike_projection = app.ZernikeProjectionCheckBox.Value;

correction_coefs = [];
correction_zernikes = [];
previous_zernike_indices = [];

if enable_shack_hartmann
    % aberration computation pass
    %
    % Implementation - Shack Hartmann simulation

    % shack hartmann params
    zernike_ranks = app.cache.shack_hartmann_zernike_ranks;
    image_subapertures_size_ratio = app.cache.image_subapertures_size_ratio;
    num_subapertures_positions = app.cache.num_subapertures_positions;
    subaperture_margin = app.cache.subaperture_margin;
    ref_image = app.cache.shack_hartmann_ref_image;

    calibration_factor = 20;
    corrmap_margin = 0.4;

    power_filter_corrector = 1;
    sigma_filter_corrector = 1;

    shack_hartmann = ShackHartmann(image_subapertures_size_ratio, num_subapertures_positions, [], calibration_factor, subaperture_margin, corrmap_margin, power_filter_corrector, sigma_filter_corrector, ref_image);

    % select subapertures to exclude, depending on the number
    % of subaperture used. This is chosen experimentally, the
    % value of the number of subapertures is constrained in the
    % GUI so the following switch should always branch to a
    % valid choice of excluded_subapertures
    %                 switch num_subapertures
    %                     case 4
    %                         excluded_subapertures = [1; 4; 13; 16];
    %                     case 5
    %                         excluded_subapertures = [1; 5; 21; 25];
    %                     case 6
    %                         excluded_subapertures = [1; 2; 5; 6; 7; 12; 25; 30; 31; 32; 35; 36];
    %                     case 7
    %                         excluded_subapertures = [1; 2; 6; 7; 8; 14; 36; 42; 43; 44; 48; 49];
    %                     case 8
    %                         excluded_subapertures = [1; 2; 7; 8; 9; 16; 49; 56; 57; 58; 63; 64];
    %                     otherwise
    %                         error('Unreachable code was reached. Check value of num_subapertures');
    %                 end
    excluded_subapertures = shack_hartmann.excluded_subapertures();

    % perform iterative aberration computation with shack-hartmann
    for r = 2:zernike_ranks
        send(D, 3); % reset progress bar

        % r-th zernike line has r+1 zernikes in it
        cur_num_zernikes = r + 1;

        % compute indices of the zernikes of current rank
        current_zernike_indices = (cur_num_zernikes * (cur_num_zernikes - 1) / 2):(cur_num_zernikes * (cur_num_zernikes - 1) / 2 + cur_num_zernikes - 1);

        % apply previous aberration correction
        [current_correction_coefs, stiched_moments_video, shifts_vector, stitched_correlation_video] = compute_correction_shack_hartmann(istream, app.cache, kernel, rephasing_data, app.blur, [], D, use_gpu, use_multithread, current_zernike_indices, ...
            shifts, image_subapertures_size_ratio, num_subapertures_positions, calibration_factor, subaperture_margin, corrmap_margin, power_filter_corrector, sigma_filter_corrector, excluded_subapertures, previous_zernike_indices, correction_coefs);
        [~, current_correction_zernikes] = zernike_phase(current_zernike_indices, numX, numY);

        correction_coefs = [correction_coefs; current_correction_coefs];
        correction_zernikes = cat(3, correction_zernikes, current_correction_zernikes);
        previous_zernike_indices = [previous_zernike_indices, current_zernike_indices];
    end

    measured_phase = stitch_phase(shifts_vector, [], numX, numY, shack_hartmann);
    % save correction coefs and indices for future export
    aberration_correction.shack_hartmann_zernike_indices = previous_zernike_indices;
    aberration_correction.shack_hartmann_zernike_coefs = correction_coefs;
end

if enable_iterative_optimization
    % aberration computation pass
    %
    % Implementation - Entropy optimization
    %
    % here we generate a set of zernike coefficients
    % that represent the aberation present on the
    % reconstructed images

    % compute coefficients for high order zernikes
    % we make a different optimization pass for each
    % additional zernike rank

    % reset correction indices and coefs arrays that ay have
    % been set by the shack hartmann pass
    zernike_indices = [];
    correction_coefs = [];

    zernike_ranks = app.optimizationzernikeranksEditField.Value;

    for r = 2:zernike_ranks
        send(D, 4); % reset progress bar
        num_zernikes = r + 1; % map to zernfun zernike ordering

        % construct high order zernike indices
        current_zernike_indices = (num_zernikes * (num_zernikes - 1) / 2):(num_zernikes * (num_zernikes - 1) / 2 + num_zernikes - 1);

        % compute correction
        current_cor = compute_correction(istream, app.cache, kernel, rephasing_data, app.blur, [], D, use_gpu, use_multithread, current_zernike_indices, app.cache.zernikes_tol, app.cache.mask_num_iter, ...
            app.cache.max_constraint, shifts, previous_zernike_indices, correction_coefs);
        [~, current_correction_zernikes] = zernike_phase(current_zernike_indices, numX, numY);

        % append coefs to correction coefs array
        correction_coefs = [correction_coefs; current_cor];
        correction_zernikes = cat(3, correction_zernikes, current_correction_zernikes);
        previous_zernike_indices = [previous_zernike_indices current_zernike_indices];
        zernike_indices = [zernike_indices current_zernike_indices];
    end

    % save correction coefs and indices for future export
    aberration_correction.iterative_opt_zernike_indices = zernike_indices;
    aberration_correction.iterative_opt_zernike_coefs = correction_coefs;
end

if ~enable_shack_hartmann && ~enable_iterative_optimization % no aberration compensation at all
    % define dummy unused variables with good size
    % to make matlab parfor parser happy - stupid matlab
    measured_phase = zeros(numX, numY, numBatches, 'single');
    correction_coefs = zeros(3, numFrames, 'single');
    correction_zernikes = zeros(numX, numY, 3, 'single');
end

[rephasing_zernikes, shack_zernikes, iterative_zernikes] = aberration_correction.generate_zernikes(numX, numY);

%% Final pass
% Here we apply all transformations computed in previous passes
% and construct the videos

% There are two ways of doing this, the first one is a 'low
% memory' mode in which the reconstructed data is cached on a
% file on the disk to avoid allocating massive video buffers.
% This is useful when the batch stride is so small that the
% whole video buffer would overflow memory.
%
% The second one is a more straightforward mode in which whole
% video buffers are allocated and stored in RAM. This is the
% default and most simple mode

% FIXME : wrap most routines into functions to factorize the "if
% local_low_memory" statement

poolobj = gcp('nocreate'); % check if a pool already exist

if isempty(poolobj)
    poolobj = parpool(parfor_arg); % create a new pool
elseif poolobj.NumWorkers ~= parfor_arg
    delete(poolobj); %close the current pool to create a new one with correct num of workers
    poolobj = parpool(parfor_arg);
end

if isLowMemory
    reg_frame_batch = istream.read_frame_batch(app.refbatchsizeEditField.Value, floor(app.positioninfileSlider.Value));
    reg_FH = fftshift(fft2(reg_frame_batch)) .* app.kernelAngularSpectrum;
    reg_FH = rephase_FH(reg_FH, rephasing_data, app.refbatchsizeEditField.Value, floor(app.positioninfileSlider.Value));
    acquisition = DopplerAcquisition(numX, numY, app.Fs / 1000, app.cache.z, app.cache.z_retina, app.cache.z_iris, app.cache.wavelength, app.cache.DX, app.cache.DY, app.pix_width, app.pix_height);
    reg_hologram = reconstruct_hologram(reg_FH, acquisition, app.blur, use_gpu, app.SVDCheckBox.Value,app.SVDThresholdCheckBox.Value, SVDThresholdEditField.Value, app.SVDxCheckBox.Value,  app.SVDx_SubApEditField.Value, [], app.cache.time_transform, spatialTransformation);

    block_size = 1024; % TODO: this should stay hardcoded but to a higher value
    block_M0 = zeros(numX, numY, 1, block_size);
    send(D, -2); % display 'video construction' on progress bar

    for batchIdx = 1:block_size:numBatches
        last_iter = min(batchIdx - 1 + block_size, numBatches) - batchIdx + 1;
        fprintf("Parfor loop: %u workers\n", parfor_arg)
        tParfor = tic;

        parfor (innerIdx = 1:last_iter, parfor_arg)
            frame_batch = istream.read_frame_batch(batchSize, (batchIdx - 1 + innerIdx - 1) * batchStride);
            FH_par = compute_FH_from_frame_batch(frame_batch, kernel, spatialTransformation, use_gpu);

            if rephasing
                FH_par = rephase_FH(FH_par, rephasing_data, batchSize, (batchIdx - 1 + innerIdx - 1) * batchStride);
            end

            % add tilted phase for FH registration
            if registration_pass
                FH_par = register_FH(FH_par, shifts(:, batchIdx:(batchIdx + 1) - 1), batchSize, 1);
            end

            if enable_iterative_optimization || enable_shack_hartmann

                if zernike_projection
                    phase = aberration_correction.compute_total_phase(batchIdx, rephasing_zernikes, shack_zernikes, iterative_zernikes);
                    correction = exp(-1i * phase);
                else
                    %                             phase = aberration_correction.compute_total_phase(batchIdx,rephasing_zernikes,[],iterative_zernikes);
                    phase = measured_phase(:, :, batchIdx);
                    correction = exp(-1i * phase);
                end

                % apply correction
                FH_par = FH_par .* correction;
            end

            if strcmp(set_up, 'Doppler')
                [M0, ~, ~] = reconstruct_hologram(FH_par, acquisition, blur, false, isSvd, isSVDx, SVDx_SubAp_num, [], time_transform, spatialTransformation);
                % save frame to block buffer
                block_M0(:, :, :, innerIdx) = gather(M0);
                send(D, 0);
            end

            send(D, 0);
        end

        tEndParfor = toc(tParfor);
        fprintf("Parfor loop took %f s\n", tEndParfor)

        if app.cache.registration

            if size(local_image_registration, 2) == numBatches % if registration from previous folder results
                block_M0 = register_video_from_shifts(block_M0(:, :, :, 1:last_iter), local_image_registration(1:2, :));
                shifts(:, batchIdx:batchIdx + last_iter - 1) = local_image_registration(1:2, batchIdx:batchIdx + last_iter - 1);
            else
                [block_M0, block_shifts] = register_video_from_reference(block_M0(:, :, :, 1:last_iter), reg_hologram);
                shifts(:, batchIdx:batchIdx + last_iter - 1) = block_shifts;
            end

        end

        % write block to file
        fwrite(fd_M0, block_M0(:), 'single');
    end

    fclose(fd_M0);

    if app.cache.registration
        % save shifts for export
        image_registration.translation_x = shifts(1, :);
        image_registration.translation_y = shifts(2, :);
    end

    exportRaw = app.saverawvideosCheckBox.Value;
    generate_video_low_memory(sprintf('%s\\%s', path, output_filename), numX, numY, 1, numBatches, path, 'M0', 0.0005, app.cache.temporal_filter, isLowFrequency, exportRaw);
else % ~local_low_memory
    send(D, -2); % display 'video construction' on progress bar
    fprintf("Parfor loop: %u workers\n", parfor_arg)
    tParfor = tic;

    parfor batchIdx = 1:numBatches

        % for batchIdx = 1:num_batches
        frame_batch = istream.read_frame_batch(batchSize, (batchIdx - 1) * batchStride);
        use_gpu_par = use_gpu;
        FH_par = compute_FH_from_frame_batch(frame_batch, kernel, spatialTransformation, use_gpu);
        local_image_type_list_par = imageTypeList;

        if rephasing
            FH_par = rephase_FH(FH_par, rephasing_data, batchSize, (batchIdx - 1) * batchStride);
        end

        % add tilted phase for FH registration
        if registration_pass
            FH_par = register_FH(FH_par, shifts(:, batchIdx:(batchIdx + 1) - 1), batchSize, 1);
        end

        if enable_iterative_optimization || enable_shack_hartmann

            if zernike_projection
                phase = aberration_correction.compute_total_phase(batchIdx, rephasing_zernikes, shack_zernikes, iterative_zernikes);
                correction = exp(-1i * phase);
            else
                %                             phase = aberration_correction.compute_total_phase(batchIdx,rephasing_zernikes,[],iterative_zernikes);
                phase = measured_phase(:, :, batchIdx);
                correction = exp(-1i * phase);
            end

            % apply correction
            FH_par = FH_par .* correction;
        end

        if strcmp(set_up, 'Doppler')
            local_image_type_list_par.construct_image(FH_par, wavelength, acquisition, blur, use_gpu, isSvd, isSVDThreshold,SVDStride, isSVDx, SVDThreshold, SVDx_SubAp_num, [], color_f1, color_f2, color_f3, ...
                0, spatialTransformation, time_transform, SubAp_PCA, xystride, num_unit_cells_x, r1, ...
                isTemporal, phi1, phi2, isSpatial, nu1, nu2, num_F);

            switch output_video
                case 'all_videos'
                    %                         [M0, sqrt_M0, M1, M2, M_freq_low, M_freq_high, M0_pos, M0_neg, M1sM0r, velocity] = reconstruct_hologram_extra(FH_par, local_wavelength, local_f1, local_f2, acquisition, local_blur, false, local_svd, [],...
                    %                             local_color_f1, local_color_f2, local_color_f3);

                    tmp_video_M0 = gather(local_image_type_list_par.power_Doppler.image);
                    video_M0(:, :, :, batchIdx) = tmp_video_M0;
                    video_M1(:, :, :, batchIdx) = gather(local_image_type_list_par.power_1_Doppler.image);
                    video_M2(:, :, :, batchIdx) = gather(local_image_type_list_par.power_2_Doppler.image);
                    video_moment0(:, :, :, batchIdx) = gather(local_image_type_list_par.moment_0.image);
                    video_moment1(:, :, :, batchIdx) = gather(local_image_type_list_par.moment_1.image);
                    video_moment2(:, :, :, batchIdx) = gather(local_image_type_list_par.moment_2.image);
                    video_M1_over_M0(:, :, :, batchIdx) = gather(local_image_type_list_par.power_1_Doppler.image) ./ gather(local_image_type_list_par.power_Doppler.image);
                    video_M2_over_M0(:, :, :, batchIdx) = gather(local_image_type_list_par.power_2_Doppler.image) ./ gather(local_image_type_list_par.power_Doppler.parameters.M0_sqrt);
                    video_M_freq_low(:, :, :, batchIdx) = gather(local_image_type_list_par.color_Doppler.parameters.freq_low);
                    video_M_freq_high(:, :, :, batchIdx) = gather(local_image_type_list_par.color_Doppler.parameters.freq_high);
                    tmp_video_M0_pos = gather(local_image_type_list_par.directional_Doppler.parameters.M0_pos);
                    video_M0_pos(:, :, :, batchIdx) = tmp_video_M0_pos;
                    tmp_video_M0_neg = gather(local_image_type_list_par.directional_Doppler.parameters.M0_neg);
                    video_M0_neg(:, :, :, batchIdx) = tmp_video_M0_neg;
                    tmp_video_M0sM1r = gather(local_image_type_list_par.M0sM1r.image);
                    video_M0sM1r(:, :, :, batchIdx) = tmp_video_M0sM1r;
                    video_velocity(:, :, :, batchIdx) = gather(local_image_type_list_par.velocity_estimate.image);
                    video_directional(:, :, :, batchIdx) = construct_directional_video(tmp_video_M0_pos, tmp_video_M0_neg, temporalFilter);
                    video_fmean(:, :, :, batchIdx) = construct_fmean_video(tmp_video_M0sM1r, tmp_video_M0, temporalFilter);

                    % video_mask(:,:,:,batchIdx) = gather(local_images_par.spectrogram.image);
                    % spectrogram_array(:,batchIdx) = gather(local_images_par.spectrogram.parameters.vector);

                    bin_t = 1;

                    if (batchIdx / bin_t) == round(batchIdx / bin_t)
                        %tmp_SH(:,:,:,:,batchIdx) = gather(local_images_par.spectrogram.parameters.SH);
                        % FIXME : Binning propre x,y,w,t
                        %SH_time(:,:,:,:,batchIdx) = tmp_SH(1:size(SH_time,1),1:size(SH_time,2),1,1:size(SH_time,4),batchIdx);
                        SH_time(:, :, :, :, batchIdx) = gather(local_image_type_list_par.spectrogram.parameters.SH);
                    end

                    % FIXME : modify entire reconstruct hologram
                    % extras to acquire additional videos
                case 'dark_field'
                    H_dark_field_stack(:, :, :, batchIdx) = gather(local_image_type_list_par.dark_field_image.parameters.H);
                    video_M0_dark_field(:, :, :, batchIdx) = gather(local_image_type_list_par.dark_field_image.image);
                case 'power_Doppler'
                    tmp_video_M0 = gather(local_image_type_list_par.power_Doppler.image);
                    video_M0(:, :, :, batchIdx) = tmp_video_M0;
                case 'moments'
                    tmp_video_M0 = gather(local_image_type_list_par.power_Doppler.image);
                    video_M0(:, :, :, batchIdx) = tmp_video_M0;
                    video_moment0(:, :, :, batchIdx) = gather(local_image_type_list_par.moment_0.image);
                    video_moment1(:, :, :, batchIdx) = gather(local_image_type_list_par.moment_1.image);
                    video_moment2(:, :, :, batchIdx) = gather(local_image_type_list_par.moment_2.image);
                case 'choroid'
                    tmp_video_M0 = gather(local_image_type_list_par.power_Doppler.image);
                    video_M0(:, :, :, batchIdx) = tmp_video_M0;
                    video_moment0(:, :, :, batchIdx) = gather(local_image_type_list_par.moment_0.image);
                    video_moment1(:, :, :, batchIdx) = gather(local_image_type_list_par.moment_1.image);
                    video_moment2(:, :, :, batchIdx) = gather(local_image_type_list_par.moment_2.image);
                    images_choroid(:, :, :, batchIdx, :) = gather(local_image_type_list_par.choroid.parameters.intervals);
                    tmp = images_choroid(:, :, :, batchIdx, :);
                    video_M_freq_low(:, :, :, batchIdx) = tmp(:,:,:,1);
                    video_M_freq_high(:, :, :, batchIdx) = tmp(:,:,:,end);

            end

        end

        send(D, 0);
    end



    tEndParfor = toc(tParfor);
    fprintf("Parfor loop took %f s\n", tEndParfor)

    if strcmp(output_video, 'all_videos') || strcmp(output_video, 'choroid')
        % generate color video
        if isLowFrequency
            video_color = construct_colored_video(video_M_freq_high, video_M_freq_low);
        else
            video_color = construct_colored_video(video_M_freq_low, video_M_freq_high);
        end

        % generate directional video

    end


    if app.cache.registration
        % post reconstruction image registration.
        % This registration is performed on the final video,
        % it does not use tilts zernikes to perform the
        % registration.
        tRegistration = tic;
        fprintf("Registration...\n")

        % If iterative registration import last registration before
        % calculating the next one

        if size(local_image_registration, 2) == numBatches && app.cache.iterative_registration % si iterative registration est activée et une registration précédente a été trouvée
            disp('Importing last registration.')
            video_M0 = register_video_from_shifts(video_M0, local_image_registration(1:2, :));
        end

        % construct treshold M0
        Nx = size(video_M0, 1);
        Ny = size(video_M0, 2);

        if app.cache.registration_disc
            [X, Y] = meshgrid(linspace(-Nx / 2, Nx / 2, Nx), linspace(-Ny / 2, Ny / 2, Ny));
            disc_ratio = app.cache.registration_disc_ratio;
            disc = X .^ 2 + Y .^ 2 < (disc_ratio * min(Nx, Ny) / 2) ^ 2;
        else
            disc = ones([Nx, Ny]);
        end

        disc = disc'; % TODO: Understand
        video_M0_reg = video_M0 .* disc - disc .* sum(video_M0 .* disc, [1, 2]) / nnz(disc); % minus the mean in the disc of each frame
        video_M0_reg = video_M0_reg ./ (max(abs(video_M0_reg), [], [1, 2])); % rescaling each frame but keeps mean at zero

        % % construct reference image
        ref_batchIdx = min(floor((app.cache.position_in_file) / batchStride) + 1, size(video_M0, 4));

        reg_frame_batch = istream.read_frame_batch(app.cache.ref_batch_size, floor(ref_batchIdx * batchStride));

        switch app.cache.spatialTransformation
            case 'angular spectrum'
                reg_FH = fftshift(fft2(reg_frame_batch)) .* kernel;
            case 'Fresnel'
                reg_FH = (reg_frame_batch) .* kernel;
        end

        reg_FH = rephase_FH(reg_FH, rephasing_data, app.cache.ref_batch_size, floor(ref_batchIdx * batchStride));
        acquisition = DopplerAcquisition(numX, numY, app.Fs / 1000, app.cache.z, app.cache.z_retina, app.cache.z_iris, app.cache.wavelength, app.cache.DX, app.cache.DY, app.pix_width, app.pix_height);
        reg_hologram = reconstruct_hologram(reg_FH, acquisition, app.blur, use_gpu, app.SVDCheckBox.Value,isSVDThreshold, SVDThreshold, app.SVDxCheckBox.Value, app.SVDx_SubApEditField.Value, [], app.time_transform, spatialTransformation);

        reg_hologram = reg_hologram .* disc - disc .* sum(reg_hologram .* disc, [1, 2]) / nnz(disc); % minus the mean
        reg_hologram = reg_hologram ./ (max(abs(reg_hologram), [], [1, 2])); % rescaling but keeps mean at zero

        switch app.cache.spatialTransformation
            case 'Fresnel'
                reg_hologram = flip(flip(reg_hologram, 1), 2);
        end

        if app.showrefCheckBox.Value
            frame_ = video_M0_reg(:, :, 1, ref_batchIdx);

            figure(7)
            montage({mat2gray(frame_) mat2gray(reg_hologram)})
            title('Current frame vs calculated reference for registration')
            % plot the mean of M0 columns for registration
            plot_columns_reg(video_M0_reg, reg_hologram, path);
        end

        switch output_video
            case 'moments'

                if size(local_image_registration, 2) == numBatches && ~app.cache.iterative_registration % if registration from previous folder results
                    disp('rendering from old registration')
                    video_M0 = register_video_from_shifts(video_M0, local_image_registration(1:2, :));
                    shifts(1:2, :) = local_image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end

                video_moment0 = register_video_from_shifts(video_moment0, shifts);
                video_moment1 = register_video_from_shifts(video_moment1, shifts);
                video_moment2 = register_video_from_shifts(video_moment2, shifts);
            case 'choroid'

                if size(local_image_registration, 2) == numBatches && ~app.cache.iterative_registration % if registration from previous folder results
                    disp('rendering from old registration')
                    video_M0 = register_video_from_shifts(video_M0, local_image_registration(1:2, :));
                    shifts(1:2, :) = local_image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end

                video_moment0 = register_video_from_shifts(video_moment0, shifts);
                video_moment1 = register_video_from_shifts(video_moment1, shifts);
                video_moment2 = register_video_from_shifts(video_moment2, shifts);
                video_color = register_video_from_shifts(video_color, shifts);


            case 'power_Doppler'

                if size(local_image_registration, 2) == numBatches && ~app.cache.iterative_registration % if registration from previous folder results
                    video_M0 = register_video_from_shifts(video_M0, local_image_registration(1:2, :));
                    shifts(1:2, :) = local_image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end

            case 'all_videos'

                if size(local_image_registration, 2) == numBatches && ~app.cache.iterative_registration % if registration from previous folder results
                    video_M0 = register_video_from_shifts(video_M0, local_image_registration(1:2, :));
                    shifts(1:2, :) = local_image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end

                video_M1 = register_video_from_shifts(video_M1, shifts);
                video_M2 = register_video_from_shifts(video_M2, shifts);
                video_moment0 = register_video_from_shifts(video_moment0, shifts);
                video_moment1 = register_video_from_shifts(video_moment1, shifts);
                video_moment2 = register_video_from_shifts(video_moment2, shifts);
                video_M1_over_M0 = register_video_from_shifts(video_M1_over_M0, shifts);
                video_M2_over_M0 = register_video_from_shifts(video_M2_over_M0, shifts);
                video_color = register_video_from_shifts(video_color, shifts);
                video_M_freq_high = register_video_from_shifts(video_M_freq_high, shifts);
                video_M_freq_low = register_video_from_shifts(video_M_freq_low, shifts);
                video_M0_pos = register_video_from_shifts(video_M0_pos, shifts);
                video_M0_neg = register_video_from_shifts(video_M0_neg, shifts);
                video_M0sM1r = register_video_from_shifts(video_M0sM1r, shifts);
                video_velocity = register_video_from_shifts(video_velocity, shifts);
                video_directional = register_video_from_shifts(video_directional, shifts);
                video_fmean = register_video_from_shifts(video_fmean, shifts);
            case 'dark_field'

                if size(local_image_registration, 2) == numBatches % if registration from previous folder results
                    video_M0_dark_field = register_video_from_shifts(video_M0_dark_field, local_image_registration(1:2, :));
                    shifts(1:2, :) = local_image_registration(1:2, :);
                else
                    [video_M0_dark_field, shifts] = register_video_from_reference(video_M0_dark_field, video_M0_dark_field(:, :, :, ref_batchIdx));
                end

        end

        % save shifts for export
        image_registration.translation_x = shifts(1, :);
        image_registration.translation_y = shifts(2, :);
        image_registration.translation_z = shifts(3, :);

        tEndRegistration = toc(tRegistration);
        fprintf("Registration took %f s\n", tEndRegistration)
    end

    %% long time processing

    exportRaw = app.saverawvideosCheckBox.Value;

    fprintf("Video generation...\n")
    tVideoGen = tic;
    % FIXME add 'or' statement
    % add colors to M0_registration
    video_M0_reg = cat(3, rescale(video_M0_reg), repmat(rescale(reg_hologram), [1, 1, 1, size(video_M0, 4)]), rescale(video_M0(:, :, 1, :))); % new in red, ref in green, old in blue

    switch output_video
        case 'power_Doppler'
            generate_video(video_M0, path, 'M0', app.cache.temporal_filter, isLowFrequency, 0, 1, Contrast=true);
            generate_video(video_M0_reg, path, 'M0_registration', app.cache.temporal_filter, isLowFrequency, 0, 1, Contrast=true);
        case 'moments'
            generate_video(video_M0, path, 'M0', app.cache.temporal_filter, isLowFrequency, 0, 1, Contrast=true);
            generate_video(video_M0_reg, path, 'M0_registration', app.cache.temporal_filter, isLowFrequency, 0, 1, Contrast=true);
            generate_video(video_moment0, path, 'moment0', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);
            generate_video(video_moment1, path, 'moment1', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);
            generate_video(video_moment2, path, 'moment2', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);

        case 'all_videos'
            generate_video(video_M0, path, 'M0', 0.0005, app.cache.temporal_filter, isLowFrequency, 0, 1);
            generate_video(video_M0_reg, path, 'M0_registration', app.cache.temporal_filter, isLowFrequency, 0, 1, Contrast=true);

            generate_video(video_moment0, path, 'moment0', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);
            generate_video(video_moment1, path, 'moment1', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);
            generate_video(video_moment2, path, 'moment2', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);

            generate_video(video_M1_over_M0, path, 'NormalizedDopplerAVG', app.cache.temporal_filter, isLowFrequency, 0, 1, Contrast=true);
            generate_video(video_M2_over_M0, path, 'NormalizedDopplerRMS', app.cache.temporal_filter, isLowFrequency, 0, 1, Contrast=true);

            % no contrast enhancement for color video, it's already been done previously
            generate_video(video_color, path, 'Color', app.cache.temporal_filter, isLowFrequency, 0, 1);
            generate_video(video_directional, path, 'Directional', [], false, 0);
            generate_video(video_fmean, path, 'Fmean', [], false, 0);
            generate_video(video_M0_pos, path, 'M0pos', app.cache.temporal_filter, isLowFrequency, 0, 1);
            generate_video(video_M0_neg, path, 'M0neg', app.cache.temporal_filter, isLowFrequency, 0, 1);
            generate_video(video_velocity, path, 'Velocity', app.cache.temporal_filter, isLowFrequency, 0, 1);

            SH_time = reshape(SH_time, size(SH_time, 1), size(SH_time, 2), size(SH_time, 3), size(SH_time, 4) * size(SH_time, 5));
            generate_video(SH_time, path, 'SH', [], false, true, 1);

            if enable_shack_hartmann
                % phase video
                video_phase = correction_phase_video(aberration_correction, numX, numY);
                video_measured_phase = mesured_phase_video(shifts_vector, num_subapertures_positions, measured_phase);
                video_PSF2D = PSF2D_video(aberration_correction, numX, numY);
                generate_video(video_measured_phase, path, 'MeasuredPhase', [], false, false, 1);
                generate_video(video_phase, path, 'ZernikePhase', [], false, false, 1);
                generate_video(video_PSF2D, path, 'PSF2D', [], false, false, 1);
                generate_video(stiched_moments_video, path, 'StichedMoments', [], false, false, 1);
                generate_video(stitched_correlation_video, path, 'StichedCorrelations', [], false, false, 1);
            end

            % generate additional images

            [color_img, img_low_freq, img_high_freq] = construct_colored_image(video_M_freq_low, video_M_freq_high);

            % convert spectrogram_matrix_video to one spectrogram
            %                     spectrogram_matrix_video = squeeze(spectrogram_matrix_video(:,:,:,1));%reshape(spectrogram_matrix_video, numX, numY, j_win * numBatches);
            %                     S_video = (fft(spectrogram_matrix_video, [], 3));
            %
            %                         S_video = squeeze(mean(abs(spectrogram_matrix_video), 2));
            %                         figure(1);
            %                         set(figure(1), 'Visible', 'off');
            %                         plot(S_video);

            color_output_filename = sprintf('%s_%s.%s', ToolBox.HD_name, 'Color', 'png');
            img_low_freq_output_filename = sprintf('%s_%s.%s', ToolBox.HD_name, 'M0_high_flow', 'png');
            img_high_freq_output_filename = sprintf('%s_%s.%s', ToolBox.HD_name, 'M0_low_flow', 'png');

            imwrite(color_img, fullfile(path_png,  color_output_filename));
            imwrite(img_low_freq, fullfile(path_png,  img_low_freq_output_filename));
            imwrite(img_high_freq, fullfile(path_png,  img_high_freq_output_filename));
            imwrite(RI, fullfile(path_png,  RI_output_filename));
            % imwrite(mat2gray((abs(spectrogram_array.^2))), fullfile(path_png,  'spectrogram_artery.png'));

        case 'dark_field'
            generate_video(video_M0_dark_field, path, 'M0_dark_field', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);
            output_dirname_df = fullfile(path_mat, 'H_dark_field_stack.mat');
            save(output_dirname_df, 'H_dark_field_stack', '-v7.3');

        case 'choroid'
            generate_video(video_M0, path, 'M0', app.cache.temporal_filter, isLowFrequency, 0, 1, Contrast=true);
            generate_video(video_M0_reg, path, 'M0_registration', app.cache.temporal_filter, isLowFrequency, 0, 1, Contrast=true);
            generate_video(video_moment0, path, 'moment0', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);
            generate_video(video_moment1, path, 'moment1', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);
            generate_video(video_moment2, path, 'moment2', app.cache.temporal_filter, isLowFrequency, exportRaw, 1, Contrast=true);
            for freq_idx = 1:num_F
                generate_video(images_choroid(:, :, :, :, freq_idx), path, sprintf('choroid_%d', freq_idx), app.cache.temporal_filter, isLowFrequency, 0, 1, NoIntensity=1, Contrast=true);
            end
            generate_video(video_color, path, 'Color', app.cache.temporal_filter, isLowFrequency, 0, 1);
    end

    tEndVideoGen = toc(tVideoGen);
    fprintf("Video Generation took %f s\n", tEndVideoGen)

end % local_low_memory

    function update_waitbar(sig)
        % signal table
        % 0 => increment value
        % 1 => reset for stage 1 (registration)
        % 2 => reset for stage 2 (video_M0 computation)
        switch sig
            case 0
                waitbar(p / N, h);
                p = p + 1;
            case -1
                waitbar(0, h, 'Translation registration...');
                p = 1;
                disp('Translation registration...')
            case -2
                waitbar(0, h, 'Image rendering...');
                p = 1;
                disp('Image rendering...')
            case 1
                waitbar(0, h, 'Optimizing defocus...');
                p = 1;
                disp('Optimizing defocus...')
            case 2
                waitbar(0, h, 'Optimizing astigmatism...');
                p = 1;
                disp('Optimizing astigmatism...')
            case 3
                waitbar(0, h, 'Shack-Hartmann...')
                p = 1;
                disp('Shack-Hartmann...')
            otherwise
                waitbar(0, h, 'Iterative optimization...');
                p = 1;
                disp('Iterative optimization')
        end

    end

fprintf("Additional data export...\n")

% export shifts to AberrationCorrection struct as zernikes
if registration_pass || app.cache.registration
    magic_number = 710;
    aberration_correction.rephasing_zernike_indices = [1 2];
    aberration_correction.rephasing_zernike_coefs = [shifts(1, :) / numX; shifts(2, :) / numY] * magic_number * 2;
    aberration_correction.rephasing_in_z_coefs = shifts(3, :) / batchSize * magic_number * 2;
end

if strcmp(output_video, 'choroid') == 1
    numX = size(images_choroid, 1);
    numY = size(images_choroid, 2);
    [X, Y] = meshgrid(1:numX, 1:numY);
    L = (numX + numY) / 2;
    fileID = fopen(fullfile(path_txt, 'intervals.txt'),'w');

    meanIm = mean(images_choroid(:, :, :, :, freq_idx), [3 4]);
    maskDiaphragm = ((X-numX/2)^2 + (Y-numY/2)^2) < L * 0.4;
    T = graythresh(meanIm);
    for freq_idx = 1:num_F
        meanIm = mean(images_choroid(:, :, :, :, freq_idx), [3 4]);
        binIm = imbinarize(meanIm, T);
        fprintf(fileID, "Interval %d: %0.2d%%\n", freq_idx, 100 * nnz(binIm .* maskDiaphragm) / (nnz(maskDiaphragm)));
    end
    fclose(fileID);
end

% add computed correction to rephasing data
new_rephasing_data = RephasingData(app.cache.batch_size, batchStride, aberration_correction);
new_rephasing_data = new_rephasing_data.compute_frame_ranges();
% update rephasing array
rephasing_data = [rephasing_data new_rephasing_data];

% export patient informations to text file_M0

% export some workspace variables to .mat file
mat_filename = sprintf('%s.mat', ToolBox.HD_name);
cache = app.cache;

save(fullfile(path_mat, mat_filename), 'cache');

% export the most useful parameters to a json file in the log
% folder

s = struct();
s.wavelength = cache.wavelength;
s.fs = cache.Fs;
s.time_transform = cache.time_transform;
s.spatial_transform = cache.spatialTransformation;
s.depth.z = cache.(cache.z_switch);
s.depth.z_switch = cache.z_switch;
s.batch_size = cache.batch_size;
s.ref_batch_size = cache.ref_batch_size;
s.batch_stride = cache.batch_stride;
s.SVD = cache.SVD;
s.SVDx = isSVDx;
s.SVDxSubAp = SVDx_SubAp_num;
JSON_parameters = jsonencode(s, PrettyPrint = true);
fid = fopen(fullfile(path_log, 'RenderingParameters.json'), "wt+");
fprintf(fid, JSON_parameters);
fclose(fid);
%             disp(s)

save(fullfile(path_mat, mat_filename), 'aberration_correction', '-append');
save(fullfile(path_mat, mat_filename), 'image_registration', '-append');

if app.cache.rephasing
    save(fullfile(path_mat, mat_filename), 'rephasing_data', '-append');
end

%PNG/VIDEO%

if ~isempty(app.NotesTextArea.Value)
    disp(app.NotesTextArea.Value)
end

% close progress bar window
close(h);

fprintf("End Computer Time: %s\n", datetime('now', 'Format', 'yyyy/MM/dd HH:mm:ss'))
% display elapsed time
toc;

% disable diary
diary off;
end
