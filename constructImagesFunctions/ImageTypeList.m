classdef ImageTypeList < handle % This class is modified dynamically
    % handles preview images and png images output
    properties
        power_Doppler
        power_1_Doppler
        power_2_Doppler
        color_Doppler
        directional_Doppler
        M0sM1r
        velocity_estimate
        phase_variation
        dark_field_image
        pure_PCA
        spectrogram
        moment_0
        moment_1
        moment_2
        choroid
    end
    
    methods
        
        function obj = ImageTypeList()
            obj.power_Doppler = ImageType('power', struct("M0sqrt", []));
            obj.power_1_Doppler = ImageType('power1');
            obj.power_2_Doppler = ImageType('power2');
            obj.color_Doppler = ImageType('color', struct('freq_low', [], 'freq_high', []));
            obj.directional_Doppler = ImageType('directional', struct('M0_pos', [], 'M0_neg', []));
            obj.M0sM1r = ImageType('ratio');
            obj.velocity_estimate = ImageType('velocity');
            obj.phase_variation = ImageType('phase_variation');
            obj.dark_field_image = ImageType('dark_field', struct('H', []));
            obj.pure_PCA = ImageType('PCA');
            obj.spectrogram = ImageType('spectrogram', struct('vector', [], 'SH', []));
            obj.moment_0 = ImageType('M0');
            obj.moment_1 = ImageType('M1');
            obj.moment_2 = ImageType('M2');
            obj.choroid = ImageType('choroid', struct('intervals_0', [], 'intervals_1', []));
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
        
        function select(obj, varargin)
            
            if nargin == 1
                % If no input is specified then all images are selected
                for field = fieldnames(obj)'
                    obj.(field{:}).select();
                end
                
            else
                % Else you only select the requested ones
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
        
        function construct_image(obj, FH, wavelength, acquisition, gaussian_width, use_gpu, svd, svd_treshold,svd_stride, svdx, svd_treshold_value, Nb_SubAp, phase_correction, ...
                color_f1, color_f2, color_f3, is_low_frequency, ...
                spatial_transformation, time_transform, SubAp_PCA, xy_stride, num_unit_cells_x, r1, ...
                local_temporal, phi1, phi2, local_spatial, nu1, nu2, num_F)
            
            % [~, phase ] = zernike_phase([ 4 ], 512, 512);
            % phase = 30 * 0.5 * phase;
            % phase_mask =  exp(1i * phase);
            % phase_mask = imresize(phase_mask, [size(FH,1) size(FH,2)]);
            % figure;
            % imagesc(angle(phase_mask));
            % FH = FH .* phase_mask;
            
            % FIXME : replace ifs by short name functions
            j_win = size(FH, 3);
            ac = acquisition;
            
            % move data to gpu if available
            if use_gpu
                
                if exist('phase_correction', 'var')
                    phase_correction = gpuArray(phase_correction);
                end
                
            end
            
            if (SubAp_PCA.Value)
                FH = subaperture_PCA(FH, SubAp_PCA, acquisition, svd, time_transform.f1, time_transform.f2, gaussian_width);
            end
            
            if exist('phase_correction', 'var') && ~isempty(phase_correction)
                FH = FH .* exp(-1i * phase_correction);
            end
            
            % if we want dark field preview H is calculated by dark field function
            if obj.dark_field_image.is_selected
                %for now we assume that both spatial transforms are the same
                H = dark_field(FH, ac.z_retina, spatial_transformation, ac.z_iris, spatial_transformation, ac.lambda, ac.x_step, ac.y_step, xy_stride, time_transform.f1, time_transform.f2, ac.fs, num_unit_cells_x, r1);
                obj.dark_field_image.parameters.H = H;
            else
                
                switch spatial_transformation
                    case 'angular spectrum'
                        H = ifft2(FH);
                    case 'Fresnel'
                        H = fftshift(fftshift(fft2(FH),1),2);
                end
                
            end
            
            %% SVD filtering
            
            if svd
                
                if svd_treshold
                    H = svd_filter(H, time_transform.f1, ac.fs, svd_treshold_value,svd_stride);
                else
                    H = svd_filter(H, time_transform.f1, ac.fs);
                end
                
            end
            
            if (svdx)
                
                if svd_treshold
                    H = svd_x_filter(H, time_transform.f1, ac.fs, Nb_SubAp, svd_treshold_value);
                else
                    H = svd_x_filter(H, time_transform.f1, ac.fs, Nb_SubAp);
                end
                
            end
            
            if local_spatial
                H = local_spatial_PCA(H, nu1, nu2);
            end
            
            if local_temporal
                H = local_temporal_PCA(H, phi1, phi2);
            end
            
            obj.spectrogram.parameters.H = H;
            
            %% Compute moments based on dropdown value
            if is_low_frequency
                sign = -1;
            else
                sign = 1;
            end
            
            switch time_transform.type
                case 'PCA' % if the time transform is PCA
                    SH = short_time_PCA(H);
                case 'FFT' % if the time transform is FFT
                    SH = fft(H, [], 3);
            end
            
            f1 = time_transform.f1;
            f2 = time_transform.f2;
            n1 = time_transform.min_PCA;
            n2 = time_transform.max_PCA;
            
            % clear("H");
            SH = abs(SH) .^ 2;
            
            %% shifts related to acquisition wrong positioning
            SH = permute(SH, [2 1 3]);
            SH = circshift(SH, [-ac.delta_y, ac.delta_x, 0]);
            
            if obj.pure_PCA.is_selected
                obj.pure_PCA.image = cumulant(SH, n1, n2);
                obj.pure_PCA.image = flat_field_correction(obj.pure_PCA.image, gaussian_width);
            end
            
            if obj.dark_field_image.is_selected
                obj.dark_field_image.image = log(flat_field_correction(moment0(SH, f1, f2, ac.fs, j_win, gaussian_width), gaussian_width));
            end
            
            if obj.phase_variation.is_selected
                %FIXME : ecraser H
                % C = angle(phase_fluctuation(H));
                % C = permute(C, [2 1 3]);
                obj.phase_variation.image = moment0(SH, f1, f2, ac.fs, j_win, gaussian_width);
            end
            
            if obj.power_Doppler.is_selected % Power Doppler has been chosen
                [img, sqrt_img] = moment0(SH, f1, f2, ac.fs, j_win, gaussian_width);
                obj.power_Doppler.parameters.M0_sqrt = sqrt_img;
                obj.power_Doppler.image = img;
            end
            
            if obj.power_1_Doppler.is_selected % Power 1 Doppler has been chosen
                img = moment1(SH, f1, f2, ac.fs, j_win, gaussian_width);
                [img0, ~] = moment0(SH, f1, f2, ac.fs, j_win, 0);
                img = img ./ mean(img0(:));
                obj.power_1_Doppler.image = img;
            end
            
            if obj.power_2_Doppler.is_selected % Power 2 Doppler has been chosen
                img2 = moment2(SH, f1, f2, ac.fs, j_win, 0);
                [img0, ~] = moment0(SH, f1, f2, ac.fs, j_win, 0);
                obj.power_2_Doppler.image = sqrt(img2 ./ mean(img0(:)));
            end
            
            if obj.color_Doppler.is_selected % Color Doppler has been chosen
                [freq_low, freq_high] = composite(SH, color_f1, color_f2, color_f3, ac.fs, j_win, gaussian_width);
                obj.color_Doppler.parameters.freq_low = freq_low;
                obj.color_Doppler.parameters.freq_high = freq_high;
                obj.color_Doppler.image = construct_colored_image(sign * gather(freq_low), sign * gather(freq_high));
            end
            
            if obj.directional_Doppler.is_selected % Directional Doppler has been chosen
                [M0_pos, M0_neg] = directional(SH, f1, f2, ac.fs, j_win, gaussian_width);
                obj.directional_Doppler.parameters.M0_pos = M0_pos;
                obj.directional_Doppler.parameters.M0_neg = M0_neg;
                obj.directional_Doppler.image = construct_directional_image(sign * gather(M0_pos), sign * gather(M0_neg), is_low_frequency);
            end
            
            if obj.M0sM1r.is_selected % M1sM0r has been chosen
                img = fmean(SH, f1, f2, ac.fs, j_win, gaussian_width);
                obj.M0sM1r.image = img;
            end
            
            if obj.velocity_estimate.is_selected % Velocity Estimate has been chosen
                obj.velocity_estimate.image = construct_velocity_video(SH, f1, f2, ac.fs, j_win, gaussian_width, wavelength);
            end
            
            if obj.spectrogram.is_selected
                bin_x = 4;
                bin_y = 4;
                % bin_t = 1;
                bin_w = 16;

                obj.spectrogram.parameters.SH = imresize3(gather(SH), [size(SH, 1) / bin_x size(SH, 2) / bin_y size(SH, 3) / bin_w], 'Method', 'linear');
                obj.spectrogram.parameters.vector = zeros(1, j_win);
                obj.spectrogram.image = zeros(size(SH, 1), size(SH, 2));

            end
            
            if obj.moment_0.is_selected % Power 1 Doppler has been chosen
                img = moment0(SH, f1, f2, ac.fs, j_win, 0);
                obj.moment_0.image = img;            
            end
            
            if obj.moment_1.is_selected % Power 1 Doppler has been chosen
                img = moment1(SH, f1, f2, ac.fs, j_win, 0);
                obj.moment_1.image = img;
            end
            
            if obj.moment_2.is_selected % Power 1 Doppler has been chosen
                img = moment2(SH, f1, f2, ac.fs, j_win, 0);
                obj.moment_2.image = img;
            end

            if obj.choroid.is_selected % Power 1 Doppler has been chosen
                numX = size(SH, 1);
                numY = size(SH, 2);
                L = (numX + numY) / 2;
                obj.choroid.parameters.intervals_0 = zeros(numX, numY, 1, num_F);
                obj.choroid.parameters.intervals_1 = zeros(numX, numY, 1, num_F);
                [X, Y] = meshgrid(1:numX, 1:numY);
                circleMask = fftshift(sqrt((X-(numX/2)).^2 + (Y-(numY/2)).^2) < 0.15 * L);
                frequencies = linspace(f1, f2, num_F + 1);
                for freqIdx = 1:num_F
                    img = moment0(SH, frequencies(freqIdx), frequencies(end), ac.fs, j_win, gaussian_width);
                    img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));

                    obj.choroid.parameters.intervals_0(:, :, :, freqIdx) = img;

                    img = moment1(SH, frequencies(freqIdx), frequencies(end), ac.fs, j_win, gaussian_width);
                    img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));

                    obj.choroid.parameters.intervals_1(:, :, :, freqIdx) = img;
                end
            end

        end
        
    end
    
end
