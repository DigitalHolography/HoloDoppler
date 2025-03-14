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
        buckets
        denoised
        cluster_projection
        intercorrel0
        intercorrel1
        intercorrel2
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
            obj.buckets = ImageType('buckets', struct('intervals_0', [], 'intervals_1', []));
            obj.denoised = ImageType('denoised');
            obj.cluster_projection = ImageType('cluster_projection');
            obj.intercorrel0 = ImageType('intercorrel0');
            obj.intercorrel1 = ImageType('intercorrel1');
            obj.intercorrel2 = ImageType('intercorrel2');
            
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
            r1 = Params.time_range(1);
            r2 = Params.time_range(2);
            [~,~,NT] = size(SHin);
            
            
            
            
            % clear phase
            SH = abs(SHin) .^ 2;
            
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
                img = moment0(SH, r1, r2, Params.fs, NT, Params.flatfield_gw);
                obj.power_Doppler.image = img;
            end
            
            if obj.power_1_Doppler.is_selected % Power Doppler has been chosen
                img = moment1(SH, r1, r2, Params.fs, NT, Params.flatfield_gw);
                obj.power_1_Doppler.image = img;
            end
            
            if obj.power_2_Doppler.is_selected % Power Doppler has been chosen
                img = moment2(SH, r1, r2, Params.fs, NT, Params.flatfield_gw);
                obj.power_2_Doppler.image = img;
            end
            
            if obj.color_Doppler.is_selected % Color Doppler has been chosen
                if Params.time_range_extra <0
                    r3 = (r1+r2)/2;
                else
                    r3 = Params.time_range_extra;
                end
                [freq_low, freq_high] = composite(SH, r1, r3, r2, Params.fs, NT, max(Params.flatfield_gw,20));
                obj.color_Doppler.image = construct_colored_image(gather(freq_low),gather(freq_high));
            end
            
            if obj.directional_Doppler.is_selected % Directional Doppler has been chosen
                [M0_pos, M0_neg] = directional(SH, r1, r2, Params.fs, NT, max(Params.flatfield_gw,20));
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
                obj.spectrogram.image = frame.cdata;
            end

            if obj.broadening.is_selected
                fi=figure("Visible", "off");
                disc = diskMask(size(SH,1), size(SH,2), Params.registration_disc_ratio)';
                spectrum_ploting(SH(:,:,:), disc, Params.fs, Params.time_range(1), Params.time_range(2));
                % ylim([-0 50])
                frame = getframe(fi); % Capture the figure
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
                obj.autocorrelogram.image = frame.cdata;
            end
            
            if obj.moment_0.is_selected % Moment 0 has been chosen
                img = moment0(SH, r1, r2 , Params.fs, NT, 0);
                obj.moment_0.image = img;
            end
            
            if obj.moment_1.is_selected % Moment 1 has been chosen
                img = moment1(SH, r1, r2, Params.fs, NT, 0);
                obj.moment_1.image = img;
            end
            
            if obj.moment_2.is_selected % Moment 2 has been chosen
                img = moment2(SH, r1, r2, Params.fs, NT, 0);
                obj.moment_2.image = img;
            end

            if obj.intercorrel0.is_selected % 
                img = moment0(SH, r1, r2, Params.fs, NT, 0);
                obj.intercorrel0.image = reorder_directions(img,3,1);
            end

            if obj.intercorrel1.is_selected % 
                img = moment1(SH, r1, r2, Params.fs, NT, 0);
                obj.intercorrel1.image = reorder_directions(img,3,1);
            end

            if obj.intercorrel2.is_selected % 
                img = moment2(SH, r1, r2, Params.fs, NT, 0);
                obj.intercorrel2.image = reorder_directions(img,3,1);
            end
            
            if obj.buckets.is_selected % buckets has been chosen
                numX = size(SH, 1);
                numY = size(SH, 2);
                num_F = Params.buckets_number;
                obj.buckets.parameters.intervals_0 = zeros(numX, numY, 1, num_F);
                obj.buckets.parameters.intervals_1 = zeros(numX, numY, 1, num_F);
                circleMask = fftshift(diskMask(numY, numX, 0.15));
                frequencies = linspace(r1, r2, num_F + 1);
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
                    img = moment0(SHdenoised, r1, r2 , Params.fs, NT, 0);
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
                    elseif 1
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
                        
                    elseif ~1
                        image = max(diff(SH(1:4:end,1:4:end,1:1:end),3),[],3);
                        
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
        
    end
    
end
