function LightRendervideoGPU(app)
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
    ToolBox = ToolBoxClassHD(app);
    dirpath = ToolBox.HD_path;
    
    app.cache = GuiCache(app);
    num_workers = app.cache.nb_cpu_cores;
    image_registration = ImageRegistration();

    parfor_arg = min(num_workers,2);
    use_multithread = true;
    use_gpu = true;
    
    % create proxy variables so that the entire gui
    % is not broadcasted to workers
    % in the parfor loops
    % in parfor (batch_idx = 1:num_batches, parfor_arg)
    % error message: "Dot indexing is not supported for variables of this type".
    
    istream = app.interferogram_stream;

    j_win = app.cache.batch_size;
    j_step = app.cache.batch_stride;
    blur = app.cache.blur;
    numX = app.Nx;
    numY = app.Ny;
    wavelength = app.cache.wavelength;
    output_video = app.cache.output_videos;
    is_svd = app.SVDCheckBox.Value;
    spatialTransformation = app.cache.spatialTransformation;
    is_SVDx = app.SVDxCheckBox.Value;
    SVDx_SubAp_num = app.SVDx_SubApEditField.Value;
    is_SVDThreshold = app.SVDThresholdCheckBox.Value;
    SVDThresholdValue = app.SVDThresholdEditField.Value;
    f1 = app.cache.time_transform.f1;
    f2 = app.cache.time_transform.f2;
    fs = app.Fs/1000;
    registration = app.cache.registration;
    registration_disk = app.cache.registration_disc;
    registration_disk_ratio = app.cache.registration_disc_ratio;
    position_in_file = app.cache.position_in_file;
        
    switch spatialTransformation
        case 'angular spectrum'
            kernel = gpuArray(app.kernelAngularSpectrum);  % propagation kernel initialization
        case 'Fresnel'
            kernel = gpuArray(app.kernelFresnel);  % propagation kernel initialization
    end

    numFrames = istream.num_frames;
    numBatches = floor((numFrames-j_win) / j_step);
    
    
    switch output_video
        case 'power_Doppler'
            return
        case 'moments'
            video_M0 = zeros(app.Nx, app.Ny, 1, numBatches,'single');
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
    N = double(numBatches-1);
    p = 1;
    
    % poolobj = gcp('nocreate'); % check if a pool already exist
    % if isempty(poolobj)
    %     poolobj = parpool(parfor_arg); % create a new pool
    % elseif poolobj.NumWorkers ~= parfor_arg
    %     delete(poolobj); %close the current pool to create a new one with correct num of workers
    %     poolobj = parpool(parfor_arg);
    % end
    
    if ~is_SVDThreshold
        SVDThresholdValue = round(f1 * j_win / fs)*2 + 1; % default value if none specified
    end

    
    
    send(D,-2); % display 'video construction' on progress bar
    fprintf("Parfor loop: %u workers\n",parfor_arg)
    tParfor = tic;
    
    switch spatialTransformation
        case 'angular spectrum'
            for batch_idx = 1:numBatches 
                frame_batch = gpuArray(istream.read_frame_batch(j_win, (min(batch_idx,numBatches) - 1) * j_step));
                SH = riassf(frame_batch,kernel,SVDThresholdValue);            
                %% permute related to acquisition optical inversion of the image
                SH = permute(SH, [2 1 3]);
                M0 = m0(SH, f1, f2, fs, j_win, local_blur); % with flatfield of gaussian_width applied
                moment0 = m0(SH, f1, f2, fs, j_win, 0); % no flatfield : raw
                moment1 = m1(SH, f1, f2, fs, j_win, 0);
                moment2 = m2(SH, f1, f2, fs, j_win, 0);
            
                send(D, 0);
                video_M0(:,:,:,batch_idx) = gather(M0);
                video_moment0(:,:,:,batch_idx) = gather(moment0);
                video_moment1(:,:,:,batch_idx) = gather(moment1);
                video_moment2(:,:,:,batch_idx) = gather(moment2);
            end
        case 'Fresnel'
            for batch_idx = 1:numBatches 
                frame_batch = gpuArray(istream.read_frame_batch(j_win, (min(batch_idx,numBatches) - 1) * j_step));
                SH = rifsf(frame_batch,kernel,SVDThresholdValue);
        
                %% permute related to acquisition optical inversion of the image
                SH = permute(SH, [2 1 3]);
                M0 = m0(SH, f1, f2, fs, j_win, local_blur); % with flatfield of gaussian_width applied
                moment0 = m0(SH, f1, f2, fs, j_win, 0); % no flatfield : raw
                moment1 = m1(SH, f1, f2, fs, j_win, 0);
                moment2 = m2(SH, f1, f2, fs, j_win, 0);
            
                send(D, 0); 
                video_M0(:,:,:,batch_idx) = gather(M0);
                video_moment0(:,:,:,batch_idx) = gather(moment0);
                video_moment1(:,:,:,batch_idx) = gather(moment1);
                video_moment2(:,:,:,batch_idx) = gather(moment2);
            end
    end
    
    
    kernel = gather(kernel);
    reset(gpuDevice); % free GPU memory allocated with GPUArray
    tEndParfor = toc(tParfor);
    fprintf("Parfor loop took %f s\n",tEndParfor)

    if registration
        % post reconstruction image registration.
        % This registration is performed on the final video,
        % it does not use tilts zernikes to perform the
        % registration.
        tRegistration = tic;
        fprintf("Registration...\n")
        
        if registration_disk
            disk = diskMask(numX, numY, registration_disk_ratio);
        else
            disk = ones([numY,numX]);
        end

        
        video_M0_reg = video_M0 .* disk - disk .* sum(video_M0.* disk,[1,2])/nnz(disk); % minus the mean in the disc of each frame
        video_M0_reg = video_M0_reg ./(max(abs(video_M0_reg),[],[1,2])); % rescaling each frame but keeps mean at zero
        

        % % construct reference image
        ref_batch_idx = min(floor((position_in_file) / j_step) + 1,size(video_M0,4)-j_win);

        reg_frame_batch = istream.read_frame_batch(j_win, floor(ref_batch_idx*j_step));
        
        SH = ri(reg_frame_batch,spatialTransformation,kernel,is_svd,is_SVDx,SVDThresholdValue,0);


        %% permute related to acquisition optical invertion
        SH = permute(SH, [2 1 3]);
        reg_hologram = m0(SH, f1, f2, fs, j_win, local_blur); % with flatfield of gaussian_width applied
        
        reg_hologram = reg_hologram.*disk - disk .* sum(reg_hologram.*disk,[1,2])/nnz(disk); % minus the mean 
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
    video_M0_reg = cat(3,rescale(video_M0_reg),repmat(rescale(reg_hologram),[1,1,1,size(video_M0,4)]),rescale(video_M0(:,:,1,:))); % new in red, ref in green
    generate_video(video_M0, dirpath, 'M0', 0.0005, app.cache.temporal_filter, 0, 0, true);
    generate_video(video_M0_reg, dirpath, 'M0_registration', 0.0005, app.cache.temporal_filter, 0, 0, true);
    generate_video(video_moment0, dirpath, 'moment0', 0.0005, app.cache.temporal_filter, 0, true, true);
    generate_video(video_moment1, dirpath, 'moment1', 0.0005, app.cache.temporal_filter, 0, true, true);
    generate_video(video_moment2, dirpath, 'moment2', 0.0005, app.cache.temporal_filter, 0, true, true);
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
    s.wavelength = app.cache.wavelength;
    s.fs =  app.cache.Fs;
    s.time_transform =  app.cache.time_transform;
    s.spatial_transform =  app.cache.spatialTransformation;
    s.depth.z =  app.cache.z_switch;
    s.depth.z_switch =  app.cache.z_switch;
    s.batch_size =  app.cache.batch_size;
    s.ref_batch_size =  app.cache.ref_batch_size;
    s.batch_stride =  app.cache.batch_stride;
    s.SVD =  app.cache.SVD;
    s.SVDx = is_SVDx;
    s.SVDxSubAp = SVDx_SubAp_num;
    JSON_parameters = jsonencode(s,PrettyPrint=true);
    fid = fopen(fullfile(dirpath, 'log', 'RenderingParameters.json'), "wt+");
    fprintf(fid, JSON_parameters);
    fclose(fid);

    % close progress bar window
    close(h);
    
    fprintf("End Computer Time: %s\n",datestr(now,'yyyy/mm/dd HH:MM:ss'))
    toc;
    
end