function LightRendervideo(app)
    % main program loop
    % light version designed to use matlab coder and utlimately make a very fast
    % C based rendering function 
    % Select a file and call other functions
    % to perform a full computation and create
    % output videos.

    %% check the necessary conditions for this function

    % only for the main Doppler images output (M0.avi, moment_0.raw ... moment_2.raw) necessary for the pulse analysis
    % no low frequency no darkfield 
    % no shack hartman correction (for simplicity) ie no rephasing related code
    % only for Fourier transform filtering time transform
    % no PCA
    % no spatial / temporal filtering
    % only for CPU multithread policy
    % no low memory option
    % NO iteration -> doesn't look for preceding outputs of registration for instance.

    if ~app.file_loaded
        return
    end

    if app.setUpDropDown.Value~='Doppler'
        return
    end 

    
    % start clock to monitor
    % computation duration
    
    tic
    
    % Generate output directory
    output_dirname = create_output_directory_name(app.filepath, app.filename);
    output_dirpath = fullfile(app.filepath, output_dirname);
    mkdir(output_dirpath);
    mkdir(fullfile(output_dirpath, 'avi'));
    mkdir(fullfile(output_dirpath, 'mp4'));
    mkdir(fullfile(output_dirpath, 'png'));
    mkdir(fullfile(output_dirpath, 'mat'));
    mkdir(fullfile(output_dirpath, 'log'));
    mkdir(fullfile(output_dirpath, 'raw'));
    
    
    app.cache = GuiCache(app);
    num_workers = app.cache.nb_cpu_cores;
    image_registration = ImageRegistration();

    parfor_arg = num_workers;
    use_multithread = true;
    use_gpu = false;
    
    % create proxy variables so that the entire gui
    % is not broadcasted to workers
    % in the parfor loops
    % in parfor (batch_idx = 1:num_batches, parfor_arg)
    % error message: "Dot indexing is not supported for variables of this type".
    
    istream = app.interferogram_stream;

    j_win = app.cache.batch_size;
    j_step = app.cache.batch_stride;
    local_blur = app.cache.blur;
    local_Nx = app.Nx;
    local_Ny = app.Ny;
    local_wavelength = app.cache.wavelength;
    local_output_video = app.cache.output_videos;
    local_svd = app.SVDCheckBox.Value;
    local_spatialTransformation = app.cache.spatialTransformation;
    local_SVDx = app.SVDxCheckBox.Value;
    local_SVDx_SubAp_num = app.SVDx_SubApEditField.Value;
    localSVDThreshold = app.SVDThresholdCheckBox.Value;
    localSVDThresholdValue = app.SVDThresholdEditField.Value;
    local_f1 = app.cache.time_transform.f1;
    local_f2 = app.cache.time_transform.f2;
    local_fs = app.Fs;
    local_registration = app.cache.registration;
    local_registration_disc = app.cache.registration_disc;
    local_registration_disc_ratio = app.cache.registration_disc_ratio;
    local_position_in_file = app.cache.position_in_file;
        
    switch app.cache.spatialTransformation
        case 'angular spectrum'
            local_kernel = app.kernelAngularSpectrum;  % propagation kernel initialization
        case 'Fresnel'
            local_kernel = app.kernelFresnel;  % propagation kernel initialization
    end

    local_num_frames = istream.num_frames;
    local_num_batches = floor((istream.num_frames-j_win) / j_step);
    
    
    switch local_output_video
        case 'power_Doppler'
            return
        case 'moments'
            video_M0 = zeros(app.Nx, app.Ny, 1, local_num_batches,'single');
            video_moment0 = video_M0;
            video_moment1 = video_M0;
            video_moment2 = video_M0;
        case 'all_videos'
            return
        case 'dark_field'
            return
    end 
    
    
    % parfor waitbar
    % we have to use a DataQueue
    % since there are no synchronization
    % primitives in matlab (mutex)
    D = parallel.pool.DataQueue;
    h = waitbar(0, '');
    afterEach(D, @update_waitbar);
    N = double(local_num_batches-1);
    p = 1;
    
    poolobj = gcp('nocreate'); % check if a pool already exist
    if isempty(poolobj)
        poolobj = parpool(parfor_arg); % create a new pool
    elseif poolobj.NumWorkers ~= parfor_arg
        delete(poolobj); %close the current pool to create a new one with correct num of workers
        poolobj = parpool(parfor_arg);
    end
    
    if ~localSVDThreshold
        localSVDThresholdValue = round(local_f1 * j_win / local_fs)*2 + 1; % default value if none specified
    end
    
    send(D,-2); % display 'video construction' on progress bar
    fprintf("Parfor loop: %u workers\n",parfor_arg)
    tParfor = tic;
    parfor (batch_idx = 1:local_num_batches, num_workers)

        frame_batch = istream.read_frame_batch(j_win, (batch_idx - 1) * j_step);
        SH = ri(frame_batch,local_spatialTransformation,local_kernel,local_svd,local_SVDx,localSVDThresholdValue,local_SVDx_SubAp_num,0);

        %% permute related to acquisition optical inversion of the image
        SH = permute(SH, [2 1 3]);
        M0 = m0(SH, local_f1, local_f2, local_fs, j_win, local_blur); % with flatfield of gaussian_width applied
        moment0 = m0(SH, local_f1, local_f2, local_fs, j_win, 0); % no flatfield : raw
        moment1 = m1(SH, local_f1, local_f2, local_fs, j_win, 0);
        moment2 = m2(SH, local_f1, local_f2, local_fs, j_win, 0);


        video_M0(:,:,:,batch_idx) = M0;
        video_moment0(:,:,:,batch_idx) = moment0;
        video_moment1(:,:,:,batch_idx) = moment1;
        video_moment2(:,:,:,batch_idx) = moment2;

        send(D, 0);
    end
    tEndParfor = toc(tParfor);
    fprintf("Parfor loop took %f s\n",tEndParfor)

    if local_registration
        % post reconstruction image registration.
        % This registration is performed on the final video,
        % it does not use tilts zernikes to perform the
        % registration.
        tRegistration = tic;
        fprintf("Registration...\n")
        
        if local_registration_disc
            [X,Y] = meshgrid(linspace(-local_Nx/2,local_Nx/2,local_Nx),linspace(-local_Ny/2,local_Ny/2,local_Ny));
            disc = X.^2+Y.^2 < (local_registration_disc_ratio * min(local_Nx,local_Ny)/2)^2; 
        else
            disc = ones([local_Ny,local_Nx]);
        end

        
        video_M0_reg = video_M0 .* disc - disc .* sum(video_M0.* disc,[1,2])/nnz(disc); % minus the mean in the disc of each frame
        video_M0_reg = video_M0_reg ./(max(abs(video_M0_reg),[],[1,2])); % rescaling each frame but keeps mean at zero
        

        % % construct reference image
        ref_batch_idx = min(floor((local_position_in_file) / j_step) + 1,size(video_M0,4)-j_win);

        reg_frame_batch = istream.read_frame_batch(j_win, floor(ref_batch_idx*j_step));
        
        SH = ri(reg_frame_batch,local_spatialTransformation,local_kernel,local_svd,local_SVDx,localSVDThresholdValue,0);


        %% permute related to acquisition optical invertion
        SH = permute(SH, [2 1 3]);
        reg_hologram = m0(SH, local_f1, local_f2, local_fs, j_win, local_blur); % with flatfield of gaussian_width applied
        
        reg_hologram = reg_hologram.*disc - disc .* sum(reg_hologram.*disc,[1,2])/nnz(disc); % minus the mean 
        reg_hologram = reg_hologram./(max(abs(reg_hologram),[],[1,2])); % rescaling but keeps mean at zero
        

        % maybe useful 
        % switch app.cache.spatialTransformation
        %     case 'Fresnel'
        %         reg_hologram = flip(flip(reg_hologram,1),2);
        % end

        % if app.showrefCheckBox.Value
        %     frame_ = video_M0_reg(:,:,1,ref_batch_idx);
        %     figure(7)
        %     montage({mat2gray(frame_) mat2gray(reg_hologram)})
        %     title('Current frame vs calculated reference for registration')
        %     % plot the mean of M0 columns for registration
        %     plot_columns_reg(video_M0_reg,reg_hologram,output_dirpath);
        % end

        
        [video_M0_reg, shifts(1:2,:)] = register_video_from_reference(video_M0_reg, reg_hologram);

        video_M0 = register_video_from_shifts(video_M0, shifts(1:2,:));
        video_moment0 = register_video_from_shifts(video_moment0, shifts);
        video_moment1 = register_video_from_shifts(video_moment1, shifts);
        video_moment2 = register_video_from_shifts(video_moment2, shifts);

        

        % save shifts for export
        image_registration.translation_x = shifts(1,:);
        image_registration.translation_y = shifts(2,:);

        tEndRegistration = toc(tRegistration);
        fprintf("Registration took %f s\n",tEndRegistration)
    end

    fprintf("Video generation...\n")
    tVideoGen = tic;
    % FIXME add 'or' statement
    % add colors to M0_registration
    video_M0_reg = cat(3,rescale(video_M0_reg),repmat(rescale(reg_hologram),[1,1,1,size(video_M0,4)]),rescale(video_M0(:,:,1,:))); % new in red, ref in green, old in blue
    generate_video(video_M0, output_dirpath, 'M0', 0.0005, app.cache.temporal_filter, 0, 0, true);
    generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, app.cache.temporal_filter, 0, 0, true);
    generate_video(video_moment0, output_dirpath, 'moment0', 0.0005, app.cache.temporal_filter, 0, export_raw, true);
    generate_video(video_moment1, output_dirpath, 'moment1', 0.0005, app.cache.temporal_filter, 0, export_raw, true);
    generate_video(video_moment2, output_dirpath, 'moment2', 0.0005, app.cache.temporal_filter, 0, export_raw, true);
    tEndVideoGen = toc(tVideoGen);
    fprintf("Video Generation took %f s\n",tEndVideoGen)
    
    function update_waitbar(sig)
        % signal table
        % 0 => increment value
        % 1 => reset for stage 1 (registration)
        % 2 => reset for stage 2 (video_M0 computation)
        switch sig
            case 0
                waitbar(p/N, h);
                p = p + 1;
            case -1
                waitbar(0,h,'Translation registration...');
                p = 1;
                disp('Translation registration...')
            case -2
                waitbar(0,h,'Image rendering...');
                p = 1;
                disp('Image rendering...')
            case 1
                waitbar(0,h,'Optimizing defocus...');
                p = 1;
                disp('Optimizing defocus...')
            case 2
                waitbar(0,h,'Optimizing astigmatism...');
                p = 1;
                disp('Optimizing astigmatism...')
            case 3
                waitbar(0,h,'Shack-Hartmann...')
                p = 1;
                disp('Shack-Hartmann...')
            otherwise
                waitbar(0,h,'Iterative optimization...');
                p = 1;
                disp('Iterative optimization')
        end
    end
    
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
    s.SVDx = local_SVDx;
    s.SVDxSubAp = local_SVDx_SubAp_num;
    JSON_parameters = jsonencode(s,PrettyPrint=true);
    fid = fopen(fullfile(output_dirpath, 'log', 'RenderingParameters.json'), "wt+");
    fprintf(fid, JSON_parameters);
    fclose(fid);

    % close progress bar window
    close(h);
    
    fprintf("End Computer Time: %s\n",datestr(now,'yyyy/mm/dd HH:MM:ss'))
    toc;
    
end