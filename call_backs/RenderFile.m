function RenderFile(fullfilepath,cache)

    [filepath,filename,ext] = fileparts(fullfilepath);
    output_dirname = create_output_directory_name(filepath, filename);
    output_dirpath = fullfile(filepath, output_dirname);
    mkdir(output_dirpath);
    mkdir(fullfile(output_dirpath, 'avi'));
    mkdir(fullfile(output_dirpath, 'mp4'));
    mkdir(fullfile(output_dirpath, 'png'));
    mkdir(fullfile(output_dirpath, 'mat'));
    mkdir(fullfile(output_dirpath, 'log'));
    mkdir(fullfile(output_dirpath, 'raw'));

    switch ext
        case '.cine'
            istream = CineReader(fullfilepath);
            fs = double(istream.frame_rate)/1000;
            pix_width = 1 / double(istream.horizontal_pix_per_meter);
            pix_height = 1 / double(istream.vertical_pix_per_meter);
            Nx = double(istream.frame_width);
            Ny = double(istream.frame_height);

        case '.holo'
            istream = HoloReader(fullfilepath);
            fs = istream.footer.info.input_fps/1000;
            pix_width = istream.footer.info.pixel_pitch.x * 1e-6;
            pix_height = istream.footer.info.pixel_pitch.y * 1e-6;
            Nx = single(istream.frame_height);
            Ny = single(istream.frame_width); %% find the real info in the footer
            z = istream.footer.compute_settings.image_rendering.propagation_distance;
    end    

    if nargin == 1 || isempty(cache) % if no parameter cache is given
        num_workers = 10;
        local_wavelength = 852e-9; 
        j_win = 512;
        ref_j_win = 1024;
        j_step = 512;
        local_blur = 35;
        local_svd = true;
        local_spatialTransformation = 'Fresnel';
        local_SVDx = false;
        local_SVDx_SubAp_num = 0;
        localSVDThreshold = false;
        localSVDThresholdValue = 0;
        local_fs = fs;
        local_f1 = 6;
        local_f2 = fs/2;
        local_registration = true;
        local_registration_disc = true;
        local_registration_disc_ratio = 0.7;
        local_position_in_file = 1;
        local_z = z;
        local_temporal_filter = 2;
    else
        num_workers = cache.nb_cpu_cores;
        local_wavelength = cache.wavelength; 
        j_win = cache.batch_size;
        ref_j_win = cache.ref_batch_size;
        j_step = cache.batch_stride;
        local_blur = cache.blur;
        local_svd = cache.SVD;
        local_spatialTransformation = cache.spatialTransformation;
        try
            local_SVDx = cache.SVDx;
            local_SVDx_SubAp_num = cache.SVDx_SubAp_num;
            localSVDThreshold = cache.svd_threshold;
            localSVDThresholdValue = cache.svd_threshold_value;
        catch
            local_SVDx = 0;
            local_SVDx_SubAp_num = 0;
            localSVDThreshold = 0;
        localSVDThresholdValue = 0;
        end
        local_f1 = cache.time_transform.f1;
        local_f2 = cache.time_transform.f2;
        local_fs = cache.Fs/1000;
        local_registration = cache.registration;
        local_registration_disc = cache.registration_disc;
        local_registration_disc_ratio = cache.registration_disc_ratio;
        if isempty(local_registration_disc_ratio)
            local_registration_disc_ratio = 0.7;
        end
        local_position_in_file = cache.position_in_file;
        local_temporal_filter = cache.temporal_filter;
        local_z = cache.z_retina;
        mat_filename = sprintf('%s.mat', output_dirname);
        save(fullfile(output_dirpath,'mat', mat_filename), 'cache');
    end

    switch local_spatialTransformation
        case 'angular spectrum'
            local_kernel = propagation_kernelAngularSpectrum(Nx, Ny, local_z, local_wavelength, pix_width, pix_height, 0);  % propagation kernel initialization
        case 'Fresnel'
            local_kernel = propagation_kernelFresnel(Nx, Ny, local_z, local_wavelength, pix_width, pix_height, 0);  % propagation kernel initialization
    end

    local_num_batches = floor((istream.num_frames-j_win) / j_step);
    
    
    
    % parfor waitbar
    % we have to use a DataQueue
    % since there are no synchronization
    % primitives in matlab (mutex)
    D = parallel.pool.DataQueue;
    h = waitbar(0, '');
    afterEach(D, @update_waitbar);
    N = double(local_num_batches-1);
    p = 1;
    
    send(D,-1);
    parfor_arg = num_workers;
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

    send(D,-2); % display 'Image rendering' on progress bar
    video_M0 = zeros(Nx, Ny, 1, local_num_batches,'single');
    video_moment0 = video_M0;
    video_moment1 = video_M0;
    video_moment2 = video_M0;
    
    fprintf("Parfor loop: %u workers\n",parfor_arg)
    tParfor = tic;
    
    parfor (batch_idx = 1:local_num_batches, parfor_arg)

        frame_batch = istream.read_frame_batch(j_win, (batch_idx - 1) * j_step);
        SH = ri(frame_batch,local_spatialTransformation,local_kernel,local_svd,local_SVDx,localSVDThresholdValue,0);

        %% permute related to acquisition optical inversion of the image
        SH = permute(SH, [2 1 3]);
        M0 = m0(SH, local_f1, local_f2, local_fs, j_win, local_blur); % with flatfield of gaussian_width applied
        moment0 = m0(SH, local_f1, local_f2, local_fs, j_win, 0); % no flatfield : raw
        moment1 = m1(SH, local_f1, local_f2, local_fs, j_win, 0);
        moment2 = m1(SH, local_f1, local_f2, local_fs, j_win, 0);


        video_M0(:,:,:,batch_idx) = M0;
        video_moment0(:,:,:,batch_idx) = moment0;
        video_moment1(:,:,:,batch_idx) = moment1;
        video_moment2(:,:,:,batch_idx) = moment2;

        send(D, 0);
    end
    
    
    tEndParfor = toc(tParfor);
    fprintf("Parfor loop took %f s\n",tEndParfor)

    send(D,-3);

    if local_registration
        % post reconstruction image registration.
        % This registration is performed on the final video,
        % it does not use tilts zernikes to perform the
        % registration.
        tRegistration = tic;
        fprintf("Registration...\n")
        
        if local_registration_disc
            [X,Y] = meshgrid(linspace(-Nx/2,Nx/2,Nx),linspace(-Ny/2,Ny/2,Ny));
            disc = X.^2+Y.^2 < (local_registration_disc_ratio * min(Nx,Ny)/2)^2; 
        else
            disc = ones([Ny,Nx]);
        end

        
        video_M0_reg = video_M0 .* disc - disc .* sum(video_M0.* disc,[1,2])/nnz(disc); % minus the mean in the disc of each frame
        video_M0_reg = video_M0_reg ./(max(abs(video_M0_reg),[],[1,2])); % rescaling each frame but keeps mean at zero
        

        % % construct reference image
        ref_batch_idx = min(floor((local_position_in_file) / j_step) + 1,size(video_M0,4)-j_win);

        reg_frame_batch = istream.read_frame_batch(ref_j_win, floor(ref_batch_idx*j_step));
        
        SH = ri(reg_frame_batch,local_spatialTransformation,local_kernel,local_svd,local_SVDx,localSVDThresholdValue,0);


        %% permute related to acquisition optical invertion
        SH = permute(SH, [2 1 3]);
        reg_hologram = m0(SH, local_f1, local_f2, local_fs, j_win, local_blur); % with flatfield of gaussian_width applied
        
        reg_hologram = reg_hologram.*disc - disc .* sum(reg_hologram.*disc,[1,2])/nnz(disc); % minus the mean 
        reg_hologram = reg_hologram./(max(abs(reg_hologram),[],[1,2])); % rescaling but keeps mean at zero

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
    generate_video(video_M0, output_dirpath, 'M0', 0.0005, local_temporal_filter, 0, 0, true);
    if local_registration
        generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, local_temporal_filter, 0, 0, true);
    end
    generate_video(video_moment0, output_dirpath, 'moment0', 0.0005, local_temporal_filter, 0, true, true);
    generate_video(video_moment1, output_dirpath, 'moment1', 0.0005, local_temporal_filter, 0, true, true);
    generate_video(video_moment2, output_dirpath, 'moment2', 0.0005, local_temporal_filter, 0, true, true);
    tEndVideoGen = toc(tVideoGen);
    fprintf("Video Generation took %f s\n",tEndVideoGen)
    
    function update_waitbar(sig)
        % signal table
        switch sig
            case 0
                waitbar(p/N, h);
                p = p + 1;
            case -1
                waitbar(0,h,'Creating Parallel pool...');
                p = 1;
                disp('Creating Parallel pool...')
            case -2
                waitbar(0,h,'Image rendering...');
                p = 1;
                disp('Image rendering...')
            case -3
                waitbar(0,h,'Translation registration...');
                p = 1;
                disp('Translation registration...')
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
    s.wavelength = local_wavelength;
    s.fs = local_fs*1000;
    local_time_transform.type = 'FFT';
    local_time_transform.f1 = local_f1;
    local_time_transform.f2 = local_f2;
    s.time_transform = local_time_transform ;
    s.spatial_transform =  local_spatialTransformation;
    s.depth.z =  local_z;
    s.batch_size =  j_win;
    s.ref_batch_size =  j_win;
    s.batch_stride =  j_step;
    s.SVD = local_svd;
    s.SVDThreshold = localSVDThreshold;
    s.SVDThresholdValue = localSVDThresholdValue;
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
