function Rendervideo(app)
    % main program loop
    % light version designed to use matlab coder and utlimately make a very fast
    % C based rendering function 
    % Select a file and call other functions
    % to perform a full computation and create
    % output videos.

    %% check the necessary conditions for this function
    
    if ~app.file_loaded
        return
    end

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

    if app.setUpDropDown.Value~='Dopper'
        return
    end 
    set_up = app.setUpDropDown.Value; 


    
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
    local_time_transform = app.cache.time_transform;
    local_blur = app.cache.blur;
    local_Nx = app.Nx;
    local_Ny = app.Ny;
    local_wavelength = app.cache.wavelength;
    local_svd = app.SVDCheckBox.Value;
    local_output_video = app.cache.output_videos;
    local_rephasing = app.cache.rephasing;
    local_low_memory = app.cache.low_memory;
    local_spatialTransformation = app.cache.spatialTransformation;
    local_temporal_filter = app.cache.temporal_filter;
    local_SubAp_PCA.Value = app.SubAp_PCA.Value;
    local_SubAp_PCA.min = app.SubAp_PCA.min;
    local_SubAp_PCA.max = app.SubAp_PCA.max;
    local_temporal = app.temporalCheckBox.Value;
    local_phi1 = app.phi1EditField.Value;
    local_phi2 = app.phi2EditField.Value;
    local_spatial = app.spatialCheckBox.Value;
    local_nu1 = app.nu1EditField.Value;
    local_nu2 = app.nu2EditField.Value;
    local_SVDx = app.SVDxCheckBox.Value;
    local_SVDx_SubAp_num = app.SVDx_SubApEditField.Value;
    localSVDThreshold = app.SVDTresholdCheckBox.Value;
    localSVDThresholdValue = app.SVDTresholdEditField.Value;
    local_f1 = app.cache.time_transform.f1;
    local_f2 = app.cache.time_transform.f2;
    local_fs = app.Fs;
    local_registration = app.cache.registration;
    local_registration_disc = app.cache.registration_disc;
    local_registration_disc_ratio = app.cache.registration_disc_ratio;
    local_position_in_file = app.cache.position_in_file;
    
    local_image_registration = [];
    
    % FIXME : add new elements to cache
    
    switch app.cache.spatialTransformation
        case 'angular spectrum'
            local_kernel = app.kernelAngularSpectrum;  % propagation kernel initialization
        case 'Fresnel'
            local_kernel = app.kernelFresnel;  % propagation kernel initialization
    end
    
    %%acquisition = DopplerAcquisition(app.Nx,app.Ny,app.cache.Fs/1000, app.cache.z, app.cache.z_retina, app.cache.z_iris,app.cache.wavelength,app.cache.DX,app.cache.DY,app.cache.pix_width,app.cache.pix_height);
    
    %%local_image_type_list = ImageTypeList();

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
    
    send(D,-2); % display 'video construction' on progress bar
    fprintf("Parfor loop: %u workers\n",parfor_arg)
    tParfor = tic;
    parfor (batch_idx = 1:local_num_batches, parfor_arg)

        frame_batch = istream.read_frame_batch(j_win, (batch_idx - 1) * j_step);
        switch local_spatialTransformation
            case 'angular spectrum'
                FH = fftshift(fft2(frame_batch)) .* local_kernel;
            case 'Fresnel'
                FH = frame_batch .* local_kernel;
        end
        %% local_image_type_list_par = local_image_type_list;

        %% local_image_type_list_par.construct_image(FH_par, local_wavelength, acquisition, local_blur, use_gpu, local_svd,localSVDTreshold, local_SVDx,localSVDTresholdValue, local_SVDx_SubAp_num, [], local_color_f1, local_color_f2, local_color_f3, ...
        %%     0, local_spatialTransformation, local_time_transform, local_SubAp_PCA, local_xystride, local_num_unit_cells_x, local_r1, ...
        %%     local_temporal, local_phi1, local_phi2, local_spatial, local_nu1, local_nu2);

        switch local_spatialTransformation
            case 'angular spectrum'
                H = ifft2(FH);
            case 'Fresnel'
                H = fftshift(fft2(FH));
        end
        if local_svd
            if localSVDThreshold
                H = svd_filter(H, local_f1, local_fs,localSVDThresholdValue);
            else
                H = svd_filter(H, local_f1, local_fs);
            end
        end
        if svdx
            if svd_treshold
                H = svd_x_filter(H, local_f1, local_fs,local_SVDx_SubAp_num,svd_treshold_value);
            else
                H = svd_x_filter(H, local_f1, local_fs, local_SVDx_SubAp_num);
            end
        end
        SH = fft(H, [], 3);
        SH = abs(SH).^2;

        %% shifts related to acquisition wrong positioning
        SH = permute(SH, [2 1 3]);
        M0 = m0(SH, local_f1, local_f2, local_fs, j_win, gaussian_width); % with flatfield of gaussian_width applied
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

        reg_frame_batch = istream.read_frame_batch(j_win, floor(ref_batch_idx*j_step));
        switch local_spatialTransformation
            case 'angular spectrum'
                reg_FH = fftshift(fft2(reg_frame_batch)) .* local_kernel;
            case 'Fresnel'
                reg_FH = reg_frame_batch .* local_kernel;
        end
        %% acquisition = DopplerAcquisition(app.Nx,app.Ny,app.Fs/1000, app.cache.z, app.cache.z_retina, app.cache.z_iris, app.cache.wavelength,app.cache.DX,app.cache.DY,app.pix_width,app.pix_height);
        switch local_spatialTransformation
            case 'angular spectrum'
                H = ifft2(FH);
            case 'Fresnel'
                H = fftshift(fft2(FH));
        end
        if local_svd
            if localSVDThreshold
                H = svd_filter(H, local_f1, local_fs,localSVDThresholdValue);
            else
                H = svd_filter(H, local_f1, local_fs);
            end
        end
        if svdx
            if svd_treshold
                H = svd_x_filter(H, local_f1, local_fs,local_SVDx_SubAp_num,svd_treshold_value);
            else
                H = svd_x_filter(H, local_f1, local_fs, local_SVDx_SubAp_num);
            end
        end
        SH = fft(H, [], 3);
        SH = abs(SH).^2;

        %% shifts related to acquisition wrong positioning
        SH = permute(SH, [2 1 3]);
        reg_hologram = m0(SH, local_f1, local_f2, local_fs, j_win, gaussian_width); % with flatfield of gaussian_width applied
        
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
        image_registration.translation_z = shifts(3,:);

        tEndRegistration = toc(tRegistration);
        fprintf("Registration took %f s\n",tEndRegistration)
    end

    fprintf("Video generation...\n")
    tVideoGen = tic;
    % FIXME add 'or' statement
    % add colors to M0_registration
    video_M0_reg = cat(3,rescale(video_M0_reg),repmat(rescale(reg_hologram),[1,1,1,size(video_M0,4)]),rescale(video_M0(:,:,1,:))); % new in red, ref in green, old in blue
        switch local_output_video
        case 'power_Doppler'
            generate_video(video_M0, output_dirpath, 'M0', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, true);
            generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, true);
        case 'moments'
            generate_video(video_M0, output_dirpath, 'M0', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, true);
            generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, true);
            generate_video(video_moment0, output_dirpath, 'moment0', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, true);
            generate_video(video_moment1, output_dirpath, 'moment1', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, true);
            generate_video(video_moment2, output_dirpath, 'moment2', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, true);

        case 'all_videos'
            generate_video(video_M0, output_dirpath, 'M0', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, true);
            %                         generate_video(video_M1, output_dirpath, 'DopplerAVG', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, true);
            %                         generate_video(video_M2, output_dirpath, 'DopplerRMS', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, true);
            generate_video(video_M0_reg, output_dirpath, 'M0_registration', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, true);

            generate_video(video_moment0, output_dirpath, 'moment0', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, true);
            generate_video(video_moment1, output_dirpath, 'moment1', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, true);
            generate_video(video_moment2, output_dirpath, 'moment2', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, true);

            generate_video(video_M1_over_M0, output_dirpath, 'NormalizedDopplerAVG', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, true);
            generate_video(video_M2_over_M0, output_dirpath, 'NormalizedDopplerRMS', 0.0005, app.cache.temporal_filter, local_low_frequency, 0, true);

            % no contrast enhancement for color video, it's already
            % been done previously
            generate_video(video_color, output_dirpath, 'Color', [], app.cache.temporal_filter, local_low_frequency, 0, false);
            generate_video(video_directional, output_dirpath, 'Directional', [], [], false, 0, true);
            generate_video(video_fmean, output_dirpath, 'Fmean', [], [], false, 0, true);
            generate_video(video_M0_pos, output_dirpath, 'M0pos', [], app.cache.temporal_filter, local_low_frequency, 0, true);
            generate_video(video_M0_neg, output_dirpath, 'M0neg', [], app.cache.temporal_filter, local_low_frequency, 0, true);
            generate_video(video_velocity, output_dirpath, 'Velocity', [], app.cache.temporal_filter, local_low_frequency, 0, true);
            % generate_video(video_mask, output_dirpath, 'Mask', [], app.cache.temporal_filter, local_low_frequency, 0, true);
            % generate_video(video_mask, output_dirpath, 'Mask', [], app.cache.temporal_filter, local_low_frequency, 0, true);
            %FIXME Move  tmp_SH_time_avg elsewhere divide by
            %number of strides/long times
            %                       tmp_SH_time_avg = SH_time_avg(:,:,:,2:(end-1));
            %SH_time_avg = SH_time_avg./double(local_num_batches);
            SH_time = reshape(SH_time,size(SH_time,1),size(SH_time,2),size(SH_time,3),size(SH_time,4)*size(SH_time,5));

            generate_video(SH_time, output_dirpath, 'SH', [], [], false, true, false);



            if enable_shack_hartmann
                % phase video
                video_phase = correction_phase_video(aberration_correction, app.Nx, app.Ny);
                video_measured_phase = mesured_phase_video(shifts_vector, num_subapertures_positions, measured_phase);
                video_PSF2D = PSF2D_video(aberration_correction, app.Nx, app.Ny);
                generate_video(video_measured_phase, output_dirpath, 'MeasuredPhase', [], [], false, false, false);
                generate_video(video_phase, output_dirpath, 'ZernikePhase', [], [], false, false, false);
                generate_video(video_PSF2D, output_dirpath, 'PSF2D', [], [], false, false, false);
                generate_video(stiched_moments_video, output_dirpath, 'StichedMoments', [], [], false, false, false);
                generate_video(stitched_correlation_video, output_dirpath, 'StichedCorrelations', [], [], false, false, false);
            end

            % generate additional images
            if local_low_frequency
                [color_img, img_low_freq, img_high_freq] = construct_colored_image(video_M_freq_high, video_M_freq_low, true);
            else
                [color_img, img_low_freq, img_high_freq] = construct_colored_image(video_M_freq_low, video_M_freq_high, false);
            end


            % convert spectrogram_matrix_video to one spectrogram
            %                     spectrogram_matrix_video = squeeze(spectrogram_matrix_video(:,:,:,1));%reshape(spectrogram_matrix_video, app.Nx, app.Ny, j_win * local_num_batches);
            %                     S_video = (fft(spectrogram_matrix_video, [], 3));
            %
            %                         S_video = squeeze(mean(abs(spectrogram_matrix_video), 2));
            %                         figure(1);
            %                         set(figure(1), 'Visible', 'off');
            %                         plot(S_video);

            color_output_filename = sprintf('%s_%s.%s', output_dirname, 'Color', 'png');
            img_low_freq_output_filename = sprintf('%s_%s.%s', output_dirname, 'M0_high_flow', 'png');
            img_high_freq_output_filename = sprintf('%s_%s.%s', output_dirname, 'M0_low_flow', 'png');

            RI_output_filename = sprintf('%s_%s.%s', output_dirname, 'Resistivity', 'png');

            RI = construct_resistivity_index(video_M0,output_dirpath, RI_output_filename);

            % FIXME : replace sprintf by fullfile
            imwrite(color_img, sprintf('%s\\png\\%s', output_dirpath, color_output_filename));
            imwrite(img_low_freq, sprintf('%s\\png\\%s', output_dirpath, img_low_freq_output_filename));
            imwrite(img_high_freq, sprintf('%s\\png\\%s', output_dirpath, img_high_freq_output_filename));
            imwrite(RI, sprintf('%s\\png\\%s', output_dirpath, RI_output_filename));
            % imwrite(mat2gray((abs(spectrogram_array.^2))), sprintf('%s\\png\\%s', output_dirpath, 'spectrogram_artery.png'));

            if exist(fullfile(output_dirpath, 'mat'), 'dir')
                output_dirpath_mat = fullfile(output_dirpath, 'mat');
            else
                output_dirpath_mat = output_dirpath;
            end


            %save(fullfile(output_dirpath_mat, 'spectro.mat'), 'spectrogram_array')

            color_img = flip(color_img);
            %                         RI = flip(RI);


            %FIXME spectrogram
        case 'dark_field'
            generate_video(video_M0_dark_field, output_dirpath, 'M0_dark_field', 0.0005, app.cache.temporal_filter, local_low_frequency, export_raw, true);

            %                         [file_name, suffix] = get_last_file_name(app.filepath, 'H_dark_field_stack');
            %                         output_dirname_df = sprintf('%s%s_%d.mat', app.filepath, 'H_dark_field_stack', suffix + 1);
            output_dirname_df = fullfile(app.filepath, output_dirname, 'mat', 'H_dark_field_stack.mat');
            save(output_dirname_df, 'H_dark_field_stack', '-v7.3');
    end
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