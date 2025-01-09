function RenderFile(fullfilepath,cache)

    ToolBox = ToolBoxClassHD();
    [filepath,filename,ext] = fileparts(fullfilepath);
    ToolBox.CreateToolBox(filepath,filename,ext)
    output_dirpath = ToolBox.HD_path;
    
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
        wavelength = 852e-9; 
        j_win = 512;
        ref_j_win = 1024;
        j_step = 512;
        blur = 35;
        is_svd = true;
        spatialTransformation = 'Fresnel';
        is_SVDx = false;
        SVDx_SubAp_num = 0;
        is_SVDThreshold = false;
        SVDThresholdValue = 0;
        f1 = 6;
        f2 = fs/2;
        is_registration = true;
        is_registration_disc = true;
        registration_disc_ratio = 0.7;
        position_in_file = 1;
        temporal_filter = 2;
    else
        num_workers = cache.nb_cpu_cores;
        wavelength = cache.wavelength; 
        j_win = cache.batch_size;
        ref_j_win = cache.ref_batch_size;
        j_step = cache.batch_stride;
        blur = cache.blur;
        is_svd = cache.SVD;
        spatialTransformation = cache.spatialTransformation;
        try
            is_SVDx = cache.SVDx;
            SVDx_SubAp_num = cache.SVDx_SubAp_num;
            is_SVDThreshold = cache.svd_threshold;
            SVDThresholdValue = cache.svd_threshold_value;
        catch
            is_SVDx = 0;
            SVDx_SubAp_num = 0;
            is_SVDThreshold = 0;
        SVDThresholdValue = 0;
        end
        f1 = cache.time_transform.f1;
        f2 = cache.time_transform.f2;
        fs = cache.Fs/1000;
        is_registration = cache.registration;
        is_registration_disc = cache.registration_disc;
        registration_disc_ratio = cache.registration_disc_ratio;
        if isempty(registration_disc_ratio)
            registration_disc_ratio = 0.7;
        end
        position_in_file = cache.position_in_file;
        temporal_filter = cache.temporal_filter;
        z = cache.z_retina;
        mat_filename = sprintf('%s.mat', output_dirname);
        save(fullfile(output_dirpath,'mat', mat_filename), 'cache');
    end

    switch spatialTransformation
        case 'angular spectrum'
            kernel = propagation_kernelAngularSpectrum(Nx, Ny, z, wavelength, pix_width, pix_height, 0);  % propagation kernel initialization
        case 'Fresnel'
            kernel = propagation_kernelFresnel(Nx, Ny, z, wavelength, pix_width, pix_height, 0);  % propagation kernel initialization
    end

    num_batches = floor((istream.num_frames-j_win) / j_step);
    
    
    
    % parfor waitbar
    % we have to use a DataQueue
    % since there are no synchronization
    % primitives in matlab (mutex)
    D = parallel.pool.DataQueue;
    h = waitbar(0, '');
    afterEach(D, @update_waitbar);
    N = double(num_batches-1);
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
    
    if ~is_SVDThreshold
        SVDThresholdValue = round(f1 * j_win / fs)*2 + 1; % default value if none specified
    end

    send(D,-2); % display 'Image rendering' on progress bar
    video_M0 = zeros(Nx, Ny, 1, num_batches,'single');
    video_moment0 = video_M0;
    video_moment1 = video_M0;
    video_moment2 = video_M0;
    
    fprintf("Parfor loop: %u workers\n",parfor_arg)
    tParfor = tic;
    
    parfor (batch_idx = 1:num_batches, parfor_arg)

        frame_batch = istream.read_frame_batch(j_win, (batch_idx - 1) * j_step);
        SH = ri(frame_batch,spatialTransformation,kernel,is_svd,is_SVDx,SVDThresholdValue,0);

        %% permute related to acquisition optical inversion of the image
        SH = permute(SH, [2 1 3]);
        M0 = m0(SH, f1, f2, fs, j_win, blur); % with flatfield of gaussian_width applied
        moment0 = m0(SH, f1, f2, fs, j_win, 0); % no flatfield : raw
        moment1 = m1(SH, f1, f2, fs, j_win, 0);
        moment2 = m1(SH, f1, f2, fs, j_win, 0);


        video_M0(:,:,:,batch_idx) = M0;
        video_moment0(:,:,:,batch_idx) = moment0;
        video_moment1(:,:,:,batch_idx) = moment1;
        video_moment2(:,:,:,batch_idx) = moment2;

        send(D, 0);
    end
    
    
    tEndParfor = toc(tParfor);
    fprintf("Parfor loop took %f s\n",tEndParfor)

    send(D,-3);

    if is_registration
        % post reconstruction image registration.
        % This registration is performed on the final video,
        % it does not use tilts zernikes to perform the
        % registration.
        tRegistration = tic;
        fprintf("Registration...\n")
        
        if is_registration_disc
            [X,Y] = meshgrid(linspace(-Nx/2,Nx/2,Nx),linspace(-Ny/2,Ny/2,Ny));
            disc = X.^2+Y.^2 < (registration_disc_ratio * min(Nx,Ny)/2)^2; 
        else
            disc = ones([Ny,Nx]);
        end

        
        video_M0_reg = video_M0 .* disc - disc .* sum(video_M0.* disc,[1,2])/nnz(disc); % minus the mean in the disc of each frame
        video_M0_reg = video_M0_reg ./(max(abs(video_M0_reg),[],[1,2])); % rescaling each frame but keeps mean at zero
        

        % % construct reference image
        ref_batch_idx = min(floor((position_in_file) / j_step) + 1,size(video_M0,4)-j_win);

        reg_frame_batch = istream.read_frame_batch(ref_j_win, floor(ref_batch_idx*j_step));
        
        SH = ri(reg_frame_batch,spatialTransformation,kernel,is_svd,is_SVDx,SVDThresholdValue,0);


        %% permute related to acquisition optical invertion
        SH = permute(SH, [2 1 3]);
        reg_hologram = m0(SH, f1, f2, fs, j_win, blur); % with flatfield of gaussian_width applied
        
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
    generate_video(video_M0, output_dirpath, 'M0', 0.0005, temporal_filter, 0, 0, true);
    if is_registration
        generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, temporal_filter, 0, 0, true);
    end
    generate_video(video_moment0, output_dirpath, 'moment0', 0.0005, temporal_filter, 0, true, true);
    generate_video(video_moment1, output_dirpath, 'moment1', 0.0005, temporal_filter, 0, true, true);
    generate_video(video_moment2, output_dirpath, 'moment2', 0.0005, temporal_filter, 0, true, true);
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
    s.wavelength = wavelength;
    s.fs = fs*1000;
    time_transform.type = 'FFT';
    time_transform.f1 = f1;
    time_transform.f2 = f2;
    s.time_transform = time_transform ;
    s.spatial_transform =  spatialTransformation;
    s.depth.z =  z;
    s.batch_size =  j_win;
    s.ref_batch_size =  j_win;
    s.batch_stride =  j_step;
    s.SVD = is_svd;
    s.SVDThreshold = is_SVDThreshold;
    s.SVDThresholdValue = SVDThresholdValue;
    s.SVDx = is_SVDx;
    s.SVDxSubAp = SVDx_SubAp_num;
    JSON_parameters = jsonencode(s,PrettyPrint=true);
    fid = fopen(fullfile(output_dirpath, 'log', 'RenderingParameters.json'), "wt+");
    fprintf(fid, JSON_parameters);
    fclose(fid);

    % close progress bar window
    close(h);
    
    fprintf("End Computer Time: %s\n",datestr(now,'yyyy/mm/dd HH:MM:ss'))
    toc;


end
