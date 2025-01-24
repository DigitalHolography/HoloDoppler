classdef ImageTypeList2 < handle 

    % images output types from the rendering pipeline 
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
        denoised
    end
    
    methods
        
        function obj = ImageTypeList2()
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
            obj.denoised = ImageType('denoised');
            
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
                % If no input is specified then no images are selected
                for field = fieldnames(obj)'
                    obj.(field{:}).clear();
                end
                
            else
                % Else you only select the requested ones

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
        
        function construct_image(obj,Params, SH)
            r1 = Params.time_range(1);
            r2 = Params.time_range(2);
            [~,~,NT] = size(SH);

            

            
            % clear phase
            SH = abs(SH) .^ 2;

            if obj.pure_PCA.is_selected
                if ~(isinteger(r1) && ~isinteger(r2)) 
                    r1p = floor(r1*2/Params.fs*NT);
                    r2p = floor(r2*2/Params.fs*NT);
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

            if obj.color_Doppler.is_selected % Color Doppler has been chosen
                [freq_low, freq_high] = composite(SH, r1, (r1+r2)/2, r2, Params.fs, NT, max(Params.flatfield_gw,20));
                obj.color_Doppler.image = construct_colored_image(gather(freq_low),gather(freq_high));
            end
            
            if obj.directional_Doppler.is_selected % Directional Doppler has been chosen
                [M0_pos, M0_neg] = directional(SH, r1, r2, Params.fs, NT, max(Params.flatfield_gw,20));
                obj.directional_Doppler.image = construct_directional_image( gather(M0_pos), gather(M0_neg));
            end
            
            if obj.spectrogram.is_selected
                bin_x = 4;
                bin_y = 4;
                bin_w = 16;
                obj.spectrogram.parameters.SH = imresize3(gather(SH), [size(SH, 1) / bin_x size(SH, 2) / bin_y size(SH, 3) / bin_w], 'Method', 'linear');
                obj.spectrogram.parameters.vector = zeros(1, NT);
            end
            
            if obj.moment_0.is_selected % Moment 0 has been chosen
                img = moment0(SH, r1, r2 , Params.fs, NT, 0);
                obj.moment_0.image = img;            
            end
            
            if obj.moment_1.is_selected % Moment 0 has been chosen
                img = moment1(SH, r1, r2, Params.fs, NT, 0);
                obj.moment_1.image = img;
            end
            
            if obj.moment_2.is_selected % Moment 0 has been chosen
                img = moment2(SH, r1, r2, Params.fs, NT, 0);
                obj.moment_2.image = img;
            end

            if obj.choroid.is_selected % choroid has been chosen
                numX = size(SH, 1);
                numY = size(SH, 2);
                num_F = 4;
                obj.choroid.parameters.intervals_0 = zeros(numX, numY, 1, num_F);
                obj.choroid.parameters.intervals_1 = zeros(numX, numY, 1, num_F);
                circleMask = fftshift(diskMask(numY, numX, 0.15));
                frequencies = linspace(r1, r2, num_F + 1);
                for freqIdx = 1:num_F
                    img = moment0(SH, frequencies(freqIdx), frequencies(freqIdx+1), Params.fs, NT, Params.flatfield_gw);
                    img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));

                    obj.choroid.parameters.intervals_0(:, :, :, freqIdx) = img;

                    img = moment1(SH, frequencies(freqIdx), frequencies(freqIdx+1), Params.fs, NT, Params.flatfield_gw);
                    img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));

                    obj.choroid.parameters.intervals_1(:, :, :, freqIdx) = img;
                end
            end

            if obj.denoised.is_selected 
                SHdenoised = denoiseNGMeet(SH,'Sigma',0.01,'NumIterations',2);
                img = moment0(SHdenoised, r1, r2 , Params.fs, NT, 0);
                obj.denoised.image = img;            
            end

        end
        
    end
    
end
