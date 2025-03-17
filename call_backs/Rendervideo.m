function Rendervideo(app)
    % main program loop
    % Select a file and call other functions
    % to perform a full computation and create
    % output videos.

    if ~app.file_loaded
        return
    end

    if strcmp(app.outputvideoDropDown.Value, 'dark field') && (app.z_reconstruction == app.z_iris)
        app.Switch.Value = 'z_retina';
        app.ZSwitchValueChanged();
    end

    % start clock to monitor
    % computation duration

    tic;
    close all
    ToolBox = ToolBoxClassHD(app);
    setGlobalToolBox(ToolBox);

    % save all gui parameters to a struct.
    % The current computation will fetch every parameter
    % from the cache and not from the gui.
    % The purpose of this is to prevent gui interactions
    % to mess up the parameters while a computation is ongoing.

    app.cache = GuiCache(app);
    numWorkers = app.cache.nb_cpu_cores;

    aberration_correction = AberrationCorrection();

    % select parallelism policy
    switch app.cache.parallelism
        case 'CPU multithread'
            %                     parfor_arg = app.numCPUCores(0.2);
            % parfor_arg = Inf;
            parfor_arg = numWorkers;
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
            parfor_arg = numWorkers;
            use_multithread = true;
            reset(gpuDevice(1));
            use_gpu = check_GPU_for_render(app);

    end

    if use_gpu
        disp("Using GPU.")
    else
        disp("Not using GPU.")
    end

    % create proxy variables so that the entire gui
    % is not broadcasted to workers
    % in the parfor loops
    % in parfor (batch_idx = 1:num_batches, parfor_arg)
    % error message: "Dot indexing is not supported for variables of this type".

    %% VARIABLES INITIALISATION

    istream = app.interferogram_stream;

    batch_size = app.cache.batch_size;
    batch_stride = app.cache.batch_stride;
    time_transform = app.cache.time_transform;
    blur = app.cache.blur;

    numX = app.Nx;
    numY = app.Ny;
    numFrames = istream.num_frames;
    numBatches = floor((numFrames - batch_size) / batch_stride);

    fs = app.cache.Fs;
    wl = app.cache.wavelength;
    Dx = app.cache.DX;
    Dy = app.cache.DY;
    pix_width = app.cache.pix_width;
    pix_height = app.cache.pix_height;

    isSvd = app.SVDCheckBox.Value;
    output_video = app.cache.output_videos;
    isRephasing = app.cache.rephasing;
    spatialTransformation = app.cache.spatialTransformation;
    t_filt = app.cache.temporal_filter;

    SubAp_PCA.Value = app.SubAp_PCA.Value;
    SubAp_PCA.min = app.SubAp_PCA.min;
    SubAp_PCA.max = app.SubAp_PCA.max;

    isTemporalFiltered = app.temporalCheckBox.Value;
    phi1 = app.phi1EditField.Value;
    phi2 = app.phi2EditField.Value;
    isSpatialFiltered = app.spatialCheckBox.Value;
    nu1 = app.nu1EditField.Value;
    nu2 = app.nu2EditField.Value;

    isSVDx = app.SVDxCheckBox.Value;
    SVDx_SubAp_num = app.SVDx_SubApEditField.Value;
    isSVDThreshold = app.SVDThresholdCheckBox.Value;
    SVDThresholdValue = app.SVDThresholdEditField.Value;
    SVDStride = app.SVDStrideEditField.Value;
    numF = app.numFreqEditField.Value;

    color_f1 = app.cache.color_f1;
    color_f2 = app.cache.color_f2;
    color_f3 = app.cache.color_f3;
    xystride = app.cache.xystride;
    num_unit_cells_x = app.cache.num_unit_cells_x;
    r1 = app.cache.r1;
    image_type_list = ImageTypeList();

    z = app.cache.z;
    z_retina = app.cache.z_retina;
    z_iris = app.cache.z_iris;

    % FIXME
    % num_focus = 1;
    % enable_peripheral_defocus_correction = false;

    if ~isempty(app.image_registration)
        image_registration = cat(1, app.image_registration.translation_x, app.image_registration.translation_y);

        if size(image_registration, 2) == numBatches % if registration from previous folder results
            disp('found last registration that will be used.')
        end

    else
        image_registration = [];
    end

    % FIXME : add new elements to cache

    if isRephasing
        rephasing_data = app.rephasing_data;
    else
        rephasing_data = [];
    end

    switch app.cache.spatialTransformation
        case 'angular spectrum'
            kernel = app.kernelAngularSpectrum; % propagation kernel initialization
        case 'Fresnel'
            kernel = app.kernelFresnel; % propagation kernel initialization
    end

    acquisition = DopplerAcquisition(numX, numY, fs / 1000, z, z_retina, z_iris, wl, Dx, Dy, pix_width, pix_height);

    spatialFilterRatio = app.spatialfilterratio.Value;

    if spatialFilterRatio ~= 0
        spatialFilterMask = diskMask(numX, numY, spatialFilterRatio, app.spatialfilterratiohigh.Value);
    else
        spatialFilterMask = ones(numX, numY);
    end

    % allocate video buffers

    switch output_video
        case 'power_Doppler'
            image_type_list.select('power_Doppler');
            video_M0 = zeros(numX, numY, 1, numBatches, 'single');

        case 'moments'
            image_type_list.select('power_Doppler', 'moment_0', 'moment_1', 'moment_2');
            video_M0 = zeros(numX, numY, 1, numBatches, 'single');
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;

        case 'all_videos'
            app.time_transform.type = 'FFT';
            image_type_list.select('power_Doppler', 'power_1_Doppler', 'power_2_Doppler', 'color_Doppler', 'directional_Doppler', 'M0sM1r', 'velocity_estimate', 'spectrogram', 'moment_0', 'moment_1', 'moment_2')

            video_M0 = zeros(numX, numY, 1, numBatches, 'single');
            % video_M1 = video_M0;
            % video_M2 = video_M0;
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;
            video_M1_over_M0 = video_M0;
            video_M2_over_M0 = video_M0;
            video_M_freq_low = video_M0;
            video_M_freq_high = video_M0;
            video_M0_pos = video_M0;
            video_M0_neg = video_M0;
            % video_M0sM1r = video_M0;

            video_velocity = zeros(numX, numY, 3, numBatches, 'single');

            video_directional = zeros(numX, numY, 3, numBatches, 'single');
            video_fmean = video_directional;

            % video_mask = video_M0;
            % psf_through_time = video_M0;
            % spectrogram_array = zeros(batch_size, num_batches, 'single');

            %FIX ME binx biny bint binw à paramétriser et
            %mettre dans le .mat + config
            bin_x = 4;
            bin_y = 4;
            bin_t = 1;
            bin_w = 16;
            % SH_time = zeros(numX, numY, 1, batch_size, 1, 'single');
            %FIX ME prévoir les cas ou ça tombe pas entier
            SH_time = zeros(numX / bin_x, numY / bin_y, 1, batch_size / bin_w, ceil(numBatches / bin_t), 'single');
            % SH_time = zeros(256, 256, 1, 32, ceil(num_batches/bin_t), 'single');
            % tmp_SH = zeros(numX, numY, 1, batch_size,ceil(num_batches/bin_t), 'single');
            % idx_tab_SH_time = 1:ceil(num_batches/bin_t);
            % idx_tab_SH_time = repmat(idx_tab_SH_time,2,1);
            % idx_tab_SH_time = reshape(idx_tab_SH_time,[],1);s

        case 'dark_field'
            image_type_list.select('dark_field_image');
            H_dark_field_stack = 1i * ones(numX, numY, batch_size, numBatches, 'single');
            video_M0_dark_field = zeros(numX, numY, 1, numBatches, 'single');

        case 'choroid'
            image_type_list.select('power_Doppler', 'moment_0', 'moment_1', 'moment_2', 'choroid');
            video_M0 = zeros(numX, numY, 1, numBatches, 'single');
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;
            images_choroid_0 = zeros(numX, numY, 1, numBatches, numF, 'single');
            images_choroid_1 = zeros(numX, numY, 1, numBatches, numF, 'single');
            video_M_freq_low = video_M0;
            video_M_freq_high = video_M0;
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
        current_batch_idx = 1 + floor(app.positioninfileSlider.Value / (batch_size + batch_stride));
        shifts = compute_temporal_registration(istream, app.cache, batch_size, batch_stride, current_batch_idx, blur, ...
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
            [~, current_correction_zernikes] = zernikePhase(current_zernike_indices, numX, numY);

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
            [~, current_correction_zernikes] = zernikePhase(current_zernike_indices, numX, numY);

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

    %% VIDEO CONSTRUCTION

    tVideoConstruction = tic;
    send(D, -2); % display 'video construction' on progress bar

    fprintf("Parfor loop: %u workers\n", parfor_arg)

    poolobj = gcp('nocreate'); % check if a pool already exist

    if isempty(poolobj)
        parpool(parfor_arg); % create a new pool
    elseif poolobj.NumWorkers ~= parfor_arg
        delete(poolobj); %close the current pool to create a new one with correct num of workers
        parpool(parfor_arg);
    end

    all_batches = uint8(istream.read_all_frames(batch_size, batch_stride));

    parfor batch_idx = 1:numBatches

        frame_batch = all_batches(:, :, :, batch_idx);

        if spatialFilterRatio ~= 0
            frame_batch = abs(ifft2(fft2(frame_batch) .* fftshift(spatialFilterMask')));
        end

        FH = compute_FH_from_frame_batch(frame_batch, kernel, spatialTransformation, use_gpu);

        if isRephasing
            FH = rephase_FH(FH, rephasing_data, batch_size, (batch_idx - 1) * batch_stride);
        end

        % add tilted phase for FH registration
        if registration_pass
            FH = register_FH(FH, shifts(:, batch_idx:(batch_idx + 1) - 1), batch_size, 1);
        end

        if enable_iterative_optimization || enable_shack_hartmann

            if zernike_projection
                phase = aberration_correction.compute_total_phase(batch_idx, rephasing_zernikes, shack_zernikes, iterative_zernikes);
                correction = exp(-1i * phase);
            else
                %                             phase = aberration_correction.compute_total_phase(batch_idx,rephasing_zernikes,[],iterative_zernikes);
                phase = measured_phase(:, :, batch_idx);
                correction = exp(-1i * phase);
            end

            % apply correction
            FH = FH .* correction;
        end

        image_type_list_par = image_type_list;
        image_type_list_par.construct_image(FH, wl, acquisition, blur, use_gpu, isSvd, isSVDThreshold, SVDStride, isSVDx, SVDThresholdValue, SVDx_SubAp_num, [], color_f1, color_f2, color_f3, ...
            spatialTransformation, time_transform, SubAp_PCA, xystride, num_unit_cells_x, r1, ...
            isTemporalFiltered, phi1, phi2, isSpatialFiltered, nu1, nu2, numF);

        switch output_video
            case 'all_videos'
                tmp_video_M0 = image_type_list_par.power_Doppler.image;
                video_M0(:, :, :, batch_idx) = tmp_video_M0;
                % video_M1(:, :, :, batch_idx) = image_type_list_par.power_1_Doppler.image;
                % video_M2(:, :, :, batch_idx) = image_type_list_par.power_2_Doppler.image;
                video_moment0(:, :, :, batch_idx) = gather(image_type_list_par.moment_0.image);
                video_moment1(:, :, :, batch_idx) = gather(image_type_list_par.moment_1.image);
                video_moment2(:, :, :, batch_idx) = gather(image_type_list_par.moment_2.image);
                video_M1_over_M0(:, :, :, batch_idx) = gather(image_type_list_par.power_1_Doppler.image) ./ gather(image_type_list_par.power_Doppler.image);
                video_M2_over_M0(:, :, :, batch_idx) = gather(image_type_list_par.power_2_Doppler.image) ./ gather(image_type_list_par.power_Doppler.parameters.M0_sqrt);
                video_M_freq_low(:, :, :, batch_idx) = gather(image_type_list_par.color_Doppler.parameters.freq_low);
                video_M_freq_high(:, :, :, batch_idx) = gather(image_type_list_par.color_Doppler.parameters.freq_high);
                tmp_video_M0_pos = gather(image_type_list_par.directional_Doppler.parameters.M0_pos);
                video_M0_pos(:, :, :, batch_idx) = tmp_video_M0_pos;
                tmp_video_M0_neg = gather(image_type_list_par.directional_Doppler.parameters.M0_neg);
                video_M0_neg(:, :, :, batch_idx) = tmp_video_M0_neg;
                tmp_video_M0sM1r = gather(image_type_list_par.M0sM1r.image);
                % video_M0sM1r(:, :, :, batch_idx) = tmp_video_M0sM1r;
                video_velocity(:, :, :, batch_idx) = gather(image_type_list_par.velocity_estimate.image);
                video_directional(:, :, :, batch_idx) = construct_directional_video(tmp_video_M0_pos, tmp_video_M0_neg, t_filt);
                video_fmean(:, :, :, batch_idx) = construct_fmean_video(tmp_video_M0sM1r, tmp_video_M0, t_filt);

                bin_t = 1;

                if (batch_idx / bin_t) == round(batch_idx / bin_t)
                    SH_time(:, :, :, :, batch_idx) = gather(image_type_list_par.spectrogram.parameters.SH);
                end

                % FIXME : modify entire reconstruct hologram
                % extras to acquire additional videos
            case 'dark_field'
                % H_dark_field_stack(:, :, :, batch_idx) = gather(image_type_list_par.dark_field_image.parameters.H);
                video_M0_dark_field(:, :, :, batch_idx) = gather(image_type_list_par.dark_field_image.image);
            case 'power_Doppler'
                tmp_video_M0 = gather(image_type_list_par.power_Doppler.image);
                video_M0(:, :, :, batch_idx) = tmp_video_M0;
            case 'moments'
                tmp_video_M0 = gather(image_type_list_par.power_Doppler.image);
                video_M0(:, :, :, batch_idx) = tmp_video_M0;
                video_moment0(:, :, :, batch_idx) = gather(image_type_list_par.moment_0.image);
                video_moment1(:, :, :, batch_idx) = gather(image_type_list_par.moment_1.image);
                video_moment2(:, :, :, batch_idx) = gather(image_type_list_par.moment_2.image);
            case 'choroid'
                tmp_video_M0 = gather(image_type_list_par.power_Doppler.image);
                video_M0(:, :, :, batch_idx) = tmp_video_M0;
                video_moment0(:, :, :, batch_idx) = gather(image_type_list_par.moment_0.image);
                video_moment1(:, :, :, batch_idx) = gather(image_type_list_par.moment_1.image);
                video_moment2(:, :, :, batch_idx) = gather(image_type_list_par.moment_2.image);
                images_choroid_0(:, :, :, batch_idx, :) = gather(image_type_list_par.choroid.parameters.intervals_0);
                images_choroid_1(:, :, :, batch_idx, :) = gather(image_type_list_par.choroid.parameters.intervals_1);
                tmp = images_choroid_0(:, :, :, batch_idx, :);
                video_M_freq_low(:, :, :, batch_idx) = tmp(:, :, :, 1);
                video_M_freq_high(:, :, :, batch_idx) = tmp(:, :, :, end);

        end

        send(D, 0);
    end

    tVideoConstruction = toc(tVideoConstruction);
    fprintf("Video Construction took %f s\n", tVideoConstruction)

    if strcmp(output_video, 'all_videos') || strcmp(output_video, 'choroid')
        % generate color video

        video_color = construct_colored_video(video_M_freq_low, video_M_freq_high);
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

        if size(image_registration, 2) == numBatches && app.cache.iterative_registration % si iterative registration est activée et une registration précédente a été trouvée
            disp('Importing last registration.')
            video_M0 = register_video_from_shifts(video_M0, image_registration(1:2, :));
        end

        % construct treshold M0
        numX = size(video_M0, 1);
        numY = size(video_M0, 2);

        if app.cache.registration_disc
            disk_ratio = app.cache.registration_disc_ratio;
            disk = diskMask(numX, numY, disk_ratio);
        else
            disk = ones([numX, numY]);
        end

        disk = disk'; % TODO: Understand
        video_M0_reg = video_M0 .* disk - disk .* sum(video_M0 .* disk, [1, 2]) / nnz(disk); % minus the mean in the disc of each frame
        video_M0_reg = video_M0_reg ./ (max(abs(video_M0_reg), [], [1, 2])); % rescaling each frame but keeps mean at zero

        % % construct reference image
        ref_batch_idx = min(floor((app.cache.position_in_file) / batch_stride) + 1, size(video_M0, 4));

        reg_frame_batch = istream.read_frame_batch(app.cache.ref_batch_size, floor((ref_batch_idx - 1) * batch_stride));

        switch app.cache.spatialTransformation
            case 'angular spectrum'
                reg_FH = fftshift(fft2(reg_frame_batch)) .* kernel;
            case 'Fresnel'
                reg_FH = (reg_frame_batch) .* kernel;
        end

        reg_FH = rephase_FH(reg_FH, rephasing_data, app.cache.ref_batch_size, floor(ref_batch_idx * batch_stride));
        acquisition = DopplerAcquisition(numX, numY, fs / 1000, z, z_retina, z_iris, wl, Dx, Dy, pix_width, pix_height);
        reg_hologram = reconstruct_hologram(reg_FH, acquisition, app.blur, use_gpu, app.SVDCheckBox.Value, isSVDThreshold, SVDThresholdValue, app.SVDxCheckBox.Value, app.SVDx_SubApEditField.Value, [], app.time_transform, spatialTransformation);

        reg_hologram = reg_hologram .* disk - disk .* sum(reg_hologram .* disk, [1, 2]) / nnz(disk); % minus the mean
        reg_hologram = reg_hologram ./ (max(abs(reg_hologram), [], [1, 2])); % rescaling but keeps mean at zero

        switch app.cache.spatialTransformation
            case 'Fresnel'
                reg_hologram = flip(flip(reg_hologram, 1), 2);
        end

        if app.showrefCheckBox.Value
            frame_ = video_M0_reg(:, :, 1, ref_batch_idx);

            figure(7)
            montage({mat2gray(frame_) mat2gray(reg_hologram)})
            title('Current frame vs calculated reference for registration')
            % plot the mean of M0 columns for registration
            plot_columns_reg(video_M0_reg, reg_hologram, ToolBox.HD_path);
        end

        switch output_video
            case 'moments'

                if size(image_registration, 2) == numBatches && ~app.cache.iterative_registration % if registration from previous folder results
                    disp('rendering from old registration')
                    video_M0 = register_video_from_shifts(video_M0, image_registration(1:2, :));
                    shifts(1:2, :) = image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end

                video_moment0 = register_video_from_shifts(video_moment0, shifts);
                video_moment1 = register_video_from_shifts(video_moment1, shifts);
                video_moment2 = register_video_from_shifts(video_moment2, shifts);
            case 'choroid'

                if size(image_registration, 2) == numBatches && ~app.cache.iterative_registration % if registration from previous folder results
                    disp('rendering from old registration')
                    video_M0 = register_video_from_shifts(video_M0, image_registration(1:2, :));
                    shifts(1:2, :) = image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end

                video_moment0 = register_video_from_shifts(video_moment0, shifts);
                video_moment1 = register_video_from_shifts(video_moment1, shifts);
                video_moment2 = register_video_from_shifts(video_moment2, shifts);
                video_color = register_video_from_shifts(video_color, shifts);

                for freq_idx = 1:numF
                    images_choroid_0(:, :, :, :, freq_idx) = register_video_from_shifts(images_choroid_0(:, :, :, :, freq_idx), shifts);
                    images_choroid_1(:, :, :, :, freq_idx) = register_video_from_shifts(images_choroid_1(:, :, :, :, freq_idx), shifts);
                end

            case 'power_Doppler'

                if size(image_registration, 2) == numBatches && ~app.cache.iterative_registration % if registration from previous folder results
                    video_M0 = register_video_from_shifts(video_M0, image_registration(1:2, :));
                    shifts(1:2, :) = image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end

            case 'all_videos'

                if size(image_registration, 2) == numBatches && ~app.cache.iterative_registration % if registration from previous folder results
                    video_M0 = register_video_from_shifts(video_M0, image_registration(1:2, :));
                    shifts(1:2, :) = image_registration(1:2, :);
                else
                    % FIXME : use "reg_hologram" as reference (current preview from frontend)
                    [video_M0_reg, shifts(1:2, :)] = register_video_from_reference(video_M0_reg, reg_hologram);
                    video_M0 = register_video_from_shifts(video_M0, shifts(1:2, :));
                end

                % video_M1 = register_video_from_shifts(video_M1, shifts);
                % video_M2 = register_video_from_shifts(video_M2, shifts);
                video_moment0 = register_video_from_shifts(video_moment0, shifts);
                video_moment1 = register_video_from_shifts(video_moment1, shifts);
                video_moment2 = register_video_from_shifts(video_moment2, shifts);
                video_M1_over_M0 = register_video_from_shifts(video_M1_over_M0, shifts);
                video_M2_over_M0 = register_video_from_shifts(video_M2_over_M0, shifts);
                video_color = register_video_from_shifts(video_color, shifts);
                % video_M_freq_high = register_video_from_shifts(video_M_freq_high, shifts);
                % video_M_freq_low = register_video_from_shifts(video_M_freq_low, shifts);
                video_M0_pos = register_video_from_shifts(video_M0_pos, shifts);
                video_M0_neg = register_video_from_shifts(video_M0_neg, shifts);
                % video_M0sM1r = register_video_from_shifts(video_M0sM1r, shifts);
                video_velocity = register_video_from_shifts(video_velocity, shifts);
                video_directional = register_video_from_shifts(video_directional, shifts);
                video_fmean = register_video_from_shifts(video_fmean, shifts);
            case 'dark_field'

                if size(image_registration, 2) == numBatches % if registration from previous folder results
                    video_M0_dark_field = register_video_from_shifts(video_M0_dark_field, image_registration(1:2, :));
                    shifts(1:2, :) = image_registration(1:2, :);
                else
                    [video_M0_dark_field, shifts] = register_video_from_reference(video_M0_dark_field, video_M0_dark_field(:, :, :, ref_batch_idx));
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

    fprintf("Video generation...\n")
    tVideoGen = tic;
    % FIXME add 'or' statement
    % add colors to M0_registration
    video_M0_reg = cat(3, rescale(video_M0_reg), repmat(rescale(reg_hologram), [1, 1, 1, size(video_M0, 4)]), rescale(video_M0(:, :, 1, :))); % new in red, ref in green, old in blue

    switch output_video
        case 'power_Doppler'
            generate_video(video_M0, ToolBox.HD_path, 'M0', temporal_filter = t_filt);
            generate_video(video_M0_reg, ToolBox.HD_path, 'M0_registration', temporal_filter = t_filt);
        case 'moments'
            generate_video(video_M0, ToolBox.HD_path, 'M0', temporal_filter = t_filt);
            generate_video(video_M0_reg, ToolBox.HD_path, 'M0_registration', temporal_filter = t_filt);
            generate_video(video_moment0, ToolBox.HD_path, 'moment0', temporal_filter = t_filt, export_raw = true);
            generate_video(video_moment1, ToolBox.HD_path, 'moment1', temporal_filter = t_filt, export_raw = true);
            generate_video(video_moment2, ToolBox.HD_path, 'moment2', temporal_filter = t_filt, export_raw = true);

        case 'all_videos'
            generate_video(video_M0, ToolBox.HD_path, 'M0', temporal_filter = t_filt);
            generate_video(video_M0_reg, ToolBox.HD_path, 'M0_registration', temporal_filter = t_filt);

            generate_video(video_moment0, ToolBox.HD_path, 'moment0', temporal_filter = t_filt, export_raw = true);
            generate_video(video_moment1, ToolBox.HD_path, 'moment1', temporal_filter = t_filt, export_raw = true);
            generate_video(video_moment2, ToolBox.HD_path, 'moment2', temporal_filter = t_filt, export_raw = true);

            generate_video(video_M1_over_M0, ToolBox.HD_path, 'NormalizedDopplerAVG', temporal_filter = t_filt);
            generate_video(video_M2_over_M0, ToolBox.HD_path, 'NormalizedDopplerRMS', temporal_filter = t_filt);

            % no contrast enhancement for color video, it's already
            % been done previously
            generate_video(video_color, ToolBox.HD_path, 'Color', contrast_tol = 0, temporal_filter = t_filt);
            generate_video(video_directional, ToolBox.HD_path, 'Directional', contrast_tol = 0);
            generate_video(video_fmean, ToolBox.HD_path, 'Fmean', contrast_tol = 0);
            generate_video(video_M0_pos, ToolBox.HD_path, 'M0pos', contrast_tol = 0, temporal_filter = t_filt);
            generate_video(video_M0_neg, ToolBox.HD_path, 'M0neg', contrast_tol = 0, temporal_filter = t_filt);
            generate_video(video_velocity, ToolBox.HD_path, 'Velocity', contrast_tol = 0, temporal_filter = t_filt);

            SH_time = reshape(SH_time, size(SH_time, 1), size(SH_time, 2), size(SH_time, 3), size(SH_time, 4) * size(SH_time, 5));
            generate_video(SH_time, ToolBox.HD_path, 'SH', contrast_tol = 0, export_raw = 1);

            if enable_shack_hartmann
                % phase video
                video_phase = correction_phase_video(aberration_correction, numX, numY);
                video_measured_phase = mesured_phase_video(shifts_vector, num_subapertures_positions, measured_phase);
                video_PSF2D = PSF2D_video(aberration_correction, numX, numY);
                generate_video(video_measured_phase, ToolBox.HD_path, 'MeasuredPhase', contrast_tol = 0);
                generate_video(video_phase, ToolBox.HD_path, 'ZernikePhase', contrast_tol = 0);
                generate_video(video_PSF2D, ToolBox.HD_path, 'PSF2D', contrast_tol = 0);
                generate_video(stiched_moments_video, ToolBox.HD_path, 'StichedMoments', contrast_tol = 0);
                generate_video(stitched_correlation_video, ToolBox.HD_path, 'StichedCorrelations', contrast_tol = 0);
            end

            % generate additional images

            % [color_img, img_low_freq, img_high_freq] = construct_colored_image(video_M_freq_low, video_M_freq_high);

            % convert spectrogram_matrix_video to one spectrogram
            %                     spectrogram_matrix_video = squeeze(spectrogram_matrix_video(:,:,:,1));%reshape(spectrogram_matrix_video, numX, numY, batch_size * num_batches);
            %                     S_video = (fft(spectrogram_matrix_video, [], 3));
            %
            %                         S_video = squeeze(mean(abs(spectrogram_matrix_video), 2));
            %                         figure(1);
            %                         set(figure(1), 'Visible', 'off');
            %                         plot(S_video);

            % color_output_filename = sprintf('%s_%s.%s', ToolBox.HD_name, 'Color', 'png');
            % img_low_freq_output_filename = sprintf('%s_%s.%s', ToolBox.HD_name, 'M0_high_flow', 'png');
            % img_high_freq_output_filename = sprintf('%s_%s.%s', ToolBox.HD_name, 'M0_low_flow', 'png');

            % imwrite(color_img, fullfile(ToolBox.HD_path_png, color_output_filename));
            % imwrite(img_low_freq, fullfile(ToolBox.HD_path_png, img_low_freq_output_filename));
            % imwrite(img_high_freq, fullfile(ToolBox.HD_path_png, img_high_freq_output_filename));
            % imwrite(RI, fullfile(ToolBox.HD_path_png, RI_output_filename));
            % imwrite(mat2gray((abs(spectrogram_array.^2))), fullfile(ToolBox.HD_path_png,  'spectrogram_artery.png'));

        case 'dark_field'
            generate_video(video_M0_dark_field, ToolBox.HD_path, 'M0_dark_field', temporal_filter = t_filt, export_raw = true);
            output_dirname_df = fullfile(ToolBox.HD_path_mat, 'H_dark_field_stack.mat');
            save(output_dirname_df, 'H_dark_field_stack', '-v7.3');

        case 'choroid'
            generate_video(video_M0, ToolBox.HD_path, 'M0', temporal_filter = t_filt);
            generate_video(video_M0_reg, ToolBox.HD_path, 'M0_registration', temporal_filter = t_filt);
            generate_video(video_moment0, ToolBox.HD_path, 'moment0', temporal_filter = t_filt, export_raw = true);
            generate_video(video_moment1, ToolBox.HD_path, 'moment1', temporal_filter = t_filt, export_raw = true);
            generate_video(video_moment2, ToolBox.HD_path, 'moment2', temporal_filter = t_filt, export_raw = true);

            for freq_idx = 1:numF
                generate_video(images_choroid_0(:, :, :, :, freq_idx), ToolBox.HD_path, sprintf('bucket_sym_%d', freq_idx), temporal_filter = t_filt, NoIntensity = 1, cornerNorm = 1.2);
                generate_video(images_choroid_1(:, :, :, :, freq_idx), ToolBox.HD_path, sprintf('bucket_asy_%d', freq_idx), temporal_filter = t_filt, NoIntensity = 1, cornerNorm = 1.2);
            end

            generate_video(video_color, ToolBox.HD_path, 'Color', contrast_tol = 0, temporal_filter = t_filt, NoIntensity = 1, cornerNorm = 1.2);
    end

    tEndVideoGen = toc(tVideoGen);
    fprintf("Video Generation took %f s\n", tEndVideoGen)

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
        aberration_correction.rephasing_in_z_coefs = shifts(3, :) / batch_size * magic_number * 2;
    end

    if strcmp(output_video, 'choroid') == 1
        numX = size(images_choroid_0, 1);
        numY = size(images_choroid_0, 2);
        fileID = fopen(fullfile(ToolBox.HD_path_txt, 'intervals.txt'), 'w');

        meanIm = mean(images_choroid_0(:, :, :, :, freq_idx), [3 4]);
        maskDiaphragm = diskMask(numX, numY, 0.8);
        T = graythresh(meanIm);

        for freq_idx = 1:numF
            meanIm = mean(images_choroid_0(:, :, :, :, freq_idx), [3 4]);
            binIm = imbinarize(meanIm, T);
            fprintf(fileID, "Interval %d: %0.2d%%\n", freq_idx, 100 * nnz(binIm .* maskDiaphragm) / (nnz(maskDiaphragm)));
        end

        fclose(fileID);
    end

    % add computed correction to rephasing data
    new_rephasing_data = RephasingData(batch_size, batch_stride, aberration_correction);
    new_rephasing_data = new_rephasing_data.compute_frame_ranges();
    % update rephasing array
    rephasing_data = [rephasing_data new_rephasing_data];

    % export patient informations to text file_M0

    % export some workspace variables to .mat file
    mat_filename = sprintf('%s.mat', ToolBox.HD_name);
    cache = app.cache;

    save(fullfile(ToolBox.HD_path_mat, mat_filename), 'cache');

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
    fid = fopen(fullfile(ToolBox.HD_path_log, 'RenderingParameters.json'), "wt+");
    fprintf(fid, JSON_parameters);
    fclose(fid);
    %             disp(s)

    save(fullfile(ToolBox.HD_path_mat, mat_filename), 'aberration_correction', '-append');
    save(fullfile(ToolBox.HD_path_mat, mat_filename), 'image_registration', '-append');

    if app.cache.rephasing
        save(fullfile(ToolBox.HD_path_mat, mat_filename), 'rephasing_data', '-append');
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
