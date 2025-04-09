classdef ImageTypeList2 < handle
    
    % images output types from the rendering pipeline
    properties
        power_Doppler
        power_1_Doppler
        power_2_Doppler
        color_Doppler
        directional_Doppler
        pure_PCA
        spectrogram
        broadening
        SH
        autocorrelogram
        moment_0
        moment_1
        moment_2
        arg_0
        f_RMS
        buckets
        denoised
        cluster_projection
        intercorrel0
        FH_modulus_mean
        FH_arg_mean
        SVD_cov
        SVD_U
        ShackHartmann_Cropped_Moments
        ShackHartmann_Phase
        power_Doppler_wiener
    end
    
    methods
        
        function obj = ImageTypeList2()
            obj.power_Doppler = ImageType('power', struct("M0sqrt", []));
            obj.power_1_Doppler = ImageType('power1');
            obj.power_2_Doppler = ImageType('power2');
            obj.color_Doppler = ImageType('color', struct('freq_low', [], 'freq_high', []));
            obj.directional_Doppler = ImageType('directional', struct('M0_pos', [], 'M0_neg', []));
            obj.pure_PCA = ImageType('PCA');
            obj.spectrogram = ImageType('spectrogram');
            obj.broadening = ImageType('broadening');
            obj.SH = ImageType('SH', struct('vector', [], 'SH', []));
            obj.autocorrelogram = ImageType('autocorrelogram');
            obj.moment_0 = ImageType('M0');
            obj.moment_1 = ImageType('M1');
            obj.moment_2 = ImageType('M2');
            obj.arg_0 = ImageType('arg0');
            obj.f_RMS = ImageType('f_RMS');
            obj.buckets = ImageType('buckets', struct('intervals_0', [], 'intervals_1', []));
            obj.denoised = ImageType('denoised');
            obj.cluster_projection = ImageType('cluster_projection');
            obj.intercorrel0 = ImageType('intercorrel0');
            obj.FH_modulus_mean = ImageType('FH_modulus_mean');
            obj.FH_arg_mean = ImageType('FH_arg_mean');
            obj.SVD_cov = ImageType('SVD_cov');
            obj.SVD_U = ImageType('SVD_U');
            obj.ShackHartmann_Cropped_Moments = ImageType('ShackMoments');
            obj.ShackHartmann_Phase = ImageType('ShackPhase');
            obj.power_Doppler_wiener = ImageType('power_wiener');
            
            
        end
        
        function clear(obj, varargin)
            
            if nargin == 1
                % If no input is specified then all images are cleared
                for field = fieldnames(obj)'
                    obj.(field{:}).clear();
                end
                
            else
                % Else you only clear the requested ones
                for i = 1:nargin - 1
                    obj.(varargin{i}).clear();
                end
                
            end
            
        end
        
        function copy_from(obj, o)
            fields = fieldnames(o);
            for i=1:length(fields)
                obj.(fields{i}).copy_from(o.(fields{i}));
            end
        end
        
        function select(obj, varargin)
            
            if nargin == 1
                % If no input is specified then no images are selected
                for field = fieldnames(obj)'
                    obj.(field{:}).clear();
                end
                
            else
                % Else you only select the requested ones
                
                if varargin{1} == "all"
                    for field = fieldnames(obj)'
                        obj.(field{:}).select();
                    end
                    return
                end
                
                obj.select(); %clear all first
                
                
                for i = 1:nargin - 1
                    obj.(varargin{i}).select();
                end
                
            end
            
        end
        
        function images2png(obj, preview_folder_name, folder_path, varargin)
            
            if nargin == 1
                % If no input is specified then all images are selected
                for field = fieldnames(obj)'
                    
                    if obj.(field{:}).is_selected
                        obj.(field{:}).image2png(preview_folder_name, folder_path);
                    end
                    
                end
                
            else
                % Else you only select the requested ones
                for i = 1:nargin - 3
                    
                    if obj.(varargin{i}).is_selected
                        obj.(varargin{i}).image2png(preview_folder_name, folder_path);
                    end
                    
                end
                
            end
            
        end
        
        function construct_image(obj,Params, SHin)
            f1 = Params.time_range(1);
            f2 = Params.time_range(2);
            
            r1 = Params.index_range(1);
            r2 = Params.index_range(2);
            [~,~,NT] = size(SHin);
            
            
            
            
            % clear phase
            SH = abs(SHin) .^2;
            SH_arg = angle(SHin);
            
            if obj.pure_PCA.is_selected
                if ~(r1-floor(r1)==0) && ~(r2-floor(r2)==0) %both not integer
                    r1p = floor(r1*2/Params.fs*NT);
                    r2p = floor(r2*2/Params.fs*NT);
                else
                    r1p =r1;
                    r2p=r2;
                end
                r1p = min(max(r1p,1),NT);
                r2p = min(max(r2p,1),NT);
                obj.pure_PCA.image = cumulant(SH, r1p, r2p);
                obj.pure_PCA.image = flat_field_correction(obj.pure_PCA.image, Params.flatfield_gw);
            end
            
            if obj.power_Doppler.is_selected % Power Doppler has been chosen
                img = moment0(SH, f1, f2, Params.fs, NT, Params.flatfield_gw);
                obj.power_Doppler.image = img;
            end

            if obj.power_Doppler_wiener.is_selected % Power Doppler has been chosen
                img = moment0(SH, f1, f2, Params.fs, NT, Params.flatfield_gw);
                obj.power_Doppler_wiener.image = wiener2(img,[2 2],10);
            end
            
            if obj.power_1_Doppler.is_selected % Power Doppler has been chosen
                img = moment1(SH, f1, f2, Params.fs, NT, Params.flatfield_gw);
                obj.power_1_Doppler.image = img;
            end
            
            if obj.power_2_Doppler.is_selected % Power Doppler has been chosen
                img = moment2(SH, f1, f2, Params.fs, NT, Params.flatfield_gw);
                obj.power_2_Doppler.image = img;
            end
            
            if obj.color_Doppler.is_selected % Color Doppler has been chosen
                if Params.time_range_extra <0
                    f3 = (f1+f2)/2;
                else
                    f3 = Params.time_range_extra;
                end
                [freq_low, freq_high] = composite(SH, f1, f3, f2, Params.fs, NT, max(Params.flatfield_gw,20));
                obj.color_Doppler.image = construct_colored_image(gather(freq_low),gather(freq_high));
            end
            
            if obj.directional_Doppler.is_selected % Directional Doppler has been chosen
                [M0_pos, M0_neg] = directional(SH, f1, f2, Params.fs, NT, max(Params.flatfield_gw,20));
                obj.directional_Doppler.image = construct_directional_image( gather(M0_pos), gather(M0_neg));
            end
            
            if obj.spectrogram.is_selected
                fi=figure("Visible", "off");
                freqs = ((0:(NT-1))-NT/2).* (Params.fs / NT);
                spect = fftshift(abs(squeeze(sum(SHin, [1 2])/(size(SH,1)*size(SH,2))).^2));
                
                plot(freqs, 10*log10(spect));
                
                ylim([-60 150]);
                xlabel('Frequency (kHz)');
                ylabel('Power Spectrum Density (dB)');
                
                frame = getframe(fi); % Capture the figure
                obj.spectrogram.graph = gca;
                obj.spectrogram.image = frame.cdata;
            end
            
            if obj.broadening.is_selected
                fi=figure("Visible", "off");
                disc = diskMask(size(SH,1), size(SH,2), Params.registration_disc_ratio)';
                spectrum_ploting(SH(:,:,:), disc, Params.fs, Params.time_range(1), Params.time_range(2));
                % ylim([-0 50])
                frame = getframe(fi); % Capture the figure
                obj.broadening.graph = gca;
                obj.broadening.image = frame.cdata;
            end
            
            if obj.SH.is_selected
                bin_x = 4;
                bin_y = 4;
                bin_w = 16;
                obj.SH.parameters.SH = imresize3(gather(SH), [size(SH, 1) / bin_x size(SH, 2) / bin_y size(SH, 3) / bin_w], 'Method', 'linear');
                obj.SH.parameters.vector = zeros(1, NT);
            end
            
            if obj.autocorrelogram.is_selected
                
                fi=figure("Visible", "off");
                indices = ((0:(NT-1))-NT/2).* (1/(Params.fs*1000));
                % disc = diskMask(size(SH,1),size(SH,2),0.7)';
                disc = ones(size(SH,1),size(SH,2));
                spect = squeeze(abs(sum(SHin.*disc, [1 2]))/nnz(disc));
                
                plot(indices, 10*log10(spect));
                
                xlim([min(indices), max(indices)]);
                ylim([-60 180]);
                xlabel('Time (s)');
                ylabel('(dB)');
                
                frame = getframe(fi); % Capture the figure
                obj.autocorrelogram.graph = gca;
                obj.autocorrelogram.image = frame.cdata;
            end
            
            if obj.moment_0.is_selected % Moment 0 has been chosen
                img = moment0(SH, f1, f2 , Params.fs, NT, 0);
                obj.moment_0.image = img;
            end
            
            if obj.arg_0.is_selected % Arg 0 has been chosen
                img = moment0(SH_arg, f1, f2 , Params.fs, NT, 0);
                obj.arg_0.image = img;
            end
            
            if obj.moment_1.is_selected % Moment 1 has been chosen
                img = moment1(SH, f1, f2, Params.fs, NT, 0);
                obj.moment_1.image = img;
            end
            
            if obj.moment_2.is_selected % Moment 2 has been chosen
                img = moment2(SH, f1, f2, Params.fs, NT, 0);
                obj.moment_2.image = img;
            end

            if obj.f_RMS.is_selected
                M0 = moment0(SH, f1, f2, Params.fs, NT, 0);
                M2 = moment2(SH, f1, f2, Params.fs, NT, 0);
                fi=figure("Visible", "off");
                imagesc(sqrt(M2./mean(M0,[1,2])));
                %imagesc(sqrt(M2./M0));
                axis off; axis image;
                title("f_{RMS} (in kHz)")
                colormap("gray");
                colorbar;
                frame = getframe(fi); % Capture the figure
                obj.f_RMS.graph = gca;
                obj.f_RMS.image= frame.cdata;
            end
            if obj.intercorrel0.is_selected %
                img = moment0(SH, f1, f2, Params.fs, NT, 0);
                obj.intercorrel0.image = reorder_directions(img,3,1);
            end
            if obj.buckets.is_selected % buckets has been chosen
                numX = size(SH, 1);
                numY = size(SH, 2);
                num_F = Params.buckets_number;
                obj.buckets.parameters.intervals_0 = zeros(numX, numY, 1, num_F);
                obj.buckets.parameters.intervals_1 = zeros(numX, numY, 1, num_F);
                circleMask = fftshift(diskMask(numY, numX, 0.15));
                frequencies = linspace(f1, f2, num_F + 1);
                for freqIdx = 1:num_F
                    img = moment0(SH, frequencies(freqIdx), frequencies(freqIdx+1), Params.fs, NT, Params.flatfield_gw);
                    img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));
                    
                    obj.buckets.parameters.intervals_0(:, :, :, freqIdx) = img;
                    
                    img = moment1(SH, frequencies(freqIdx), frequencies(freqIdx+1), Params.fs, NT, Params.flatfield_gw);
                    img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));
                    
                    obj.buckets.parameters.intervals_1(:, :, :, freqIdx) = img;
                end
            end
            
            if obj.denoised.is_selected
                try
                    SHdenoised = denoiseNGMeet(SH,'Sigma',0.01,'NumIterations',2);
                    img = moment0(SHdenoised, f1, f2 , Params.fs, NT, 0);
                    obj.denoised.image = img;
                catch ME
                    % Display error message and line number
                    fprintf('Error: %s\n', ME.message);
                    fprintf('Occurred in: %s at line %d\n', ME.stack(1).name, ME.stack(1).line);
                    obj.denoised.image = [];
                end
            end
            
            if obj.cluster_projection.is_selected
                try
                    % Get the size of the 3D array
                    
                    if 0
                        [xSize, ySize, zSize] = size(SH(1:4:end,1:4:end,1:1:end));
                        
                        % Generate grid coordinates for each voxel
                        [x, y, z] = ndgrid(1:xSize, 1:ySize, 1:zSize);
                        
                        % Flatten the 3D array into a list of points
                        points = [64*x(:), 64*y(:), z(:)]; % add more weight to the frequency dimension z
                        values = SH(1:4:end,1:4:end,1:1:end);  % Flatten values as well
                        values = values(:);
                        % Combine spatial and intensity information (optional)
                        features = [points, values]; % [x, y, z, intensity]
                        
                        % Number of clusters (N)
                        N = 3;
                        
                        % Apply K-means clustering
                        [idx, ~] = kmeans(features, N, 'Distance', 'sqeuclidean');
                        
                        % Reshape the cluster labels back to 3D
                        clusters = reshape(idx, xSize, ySize, zSize);
                        
                        colors = lines(N);
                        
                        image = 0;
                        
                        for i=1:N
                            image = image + rescale(sum((clusters==i),3).*reshape(colors(i,:),1,1,[]));
                        end
                    elseif ~1
                        video = SH(1:4:end,1:4:end,1:1:end);
                        [numX, numY, zSize] = size(video);
                        video_flat = reshape(video,[numY*numX,zSize]);
                        if true
                            video_flat = normalize(video_flat,2);
                        end
                        N=3;
                        [idx] = kmeans(video_flat,N,'Distance',"cityblock",'MaxIter',100);
                        idx = reshape(idx,[numX,numY]);
                        image = ind2rgb(idx,lines(N));
                        
                    elseif 1
                        [~,image] = max(diff(SH(1:1:end,1:1:end,1:1:end),1,3),[],3);
                        % image = moment0(diff(SH(1:1:end,1:1:end,1:1:end),1,3), f1, f2 , Params.fs, NT, 0);
                        %image = flat_field_correction(image,Params.flatfield_gw);
                        
                    end
                    
                    obj.cluster_projection.image = image;
                    
                catch ME
                    % Display error message and line number
                    fprintf('Error: %s\n', ME.message);
                    fprintf('Occurred in: %s at line %d\n', ME.stack(1).name, ME.stack(1).line);
                    obj.denoised.image = [];
                end
            end
            
        end
        
        function construct_image_from_FH(obj,Params, FHin)
            if obj.FH_modulus_mean.is_selected
                switch Params.spatial_transformation
                    case 'angular spectrum' % log10
                        obj.FH_modulus_mean.image = squeeze(log10(fftshift(mean(abs(FHin),3))));
                    case 'Fresnel' % no log10
                        obj.FH_modulus_mean.image = squeeze((mean(abs(FHin),3)));
                        
                end
            end
            if obj.FH_arg_mean.is_selected
                switch Params.spatial_transformation
                    case 'angular spectrum' %
                        obj.FH_arg_mean.image = squeeze((fftshift(mean(angle(FHin),3))));
                    case 'Fresnel'
                        obj.FH_arg_mean.image = squeeze((mean(angle(FHin),3)));
                end
            end
            
        end
        
        function construct_image_from_SVD(obj,Params, covin, Uin, szin)
            % szin is just the size of a batch nx ny nt for reference
            if isempty(covin)
                obj.SVD_cov.image = [];
                obj.SVD_U.image = [];
                return 
            end
            if obj.SVD_cov.is_selected
                obj.SVD_cov.image = abs(covin);
            end
            if obj.SVD_U.is_selected
                Uin = reshape(Uin,szin(1),szin(2),[]);
                fi = figure(Visible="off");
                Uin = abs(Uin);
                Uin = rescale(Uin,InputMax=max(Uin,[],[1,2]),InputMin=min(Uin,[],[1,2]));
                C = cell(1, size(Uin, 3));
                for i = 1:size(Uin, 3)
                    C{i} = Uin(:, :, i)';
                end
                montage(C, 'BorderSize', [0 0]); 

                set(gca, 'Position', [0 0 1 1]); % Remove extra spaceù=
                frame = getframe(fi);
                obj.SVD_U.graph = gca;
                obj.SVD_U.image = frame.cdata;
            end
        end
        function construct_image_from_ShackHartmann(obj,Params, moment_chunks_crop_array , ShackHartmannMask)
            if isempty(ShackHartmannMask) 
                obj.ShackHartmann_Cropped_Moments.image = [];
                obj.ShackHartmann_Phase.image = [];
                return 
            end
            if obj.ShackHartmann_Cropped_Moments.is_selected
                obj.ShackHartmann_Cropped_Moments.image = moment_chunks_crop_array;
            end
            if obj.ShackHartmann_Phase.is_selected
                obj.ShackHartmann_Phase.image = angle(ShackHartmannMask);
            end
        end
    end
    
end
