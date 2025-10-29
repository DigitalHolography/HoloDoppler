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
    SH_avg
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
    power_adapt
    pure_phase
    doppler_variance_mod
    doppler_variance_mod_pha
    amplitude_decorrelation
    diff_mod
    diff_mod_pha
    phase_diff
    phase_variance
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
        obj.SH_avg = ImageType('SH_avg', struct('SH', []));
        obj.autocorrelogram = ImageType('autocorrelogram');
        obj.moment_0 = ImageType('M0');
        obj.moment_1 = ImageType('M1');
        obj.moment_2 = ImageType('M2');
        obj.arg_0 = ImageType('arg0');
        obj.f_RMS = ImageType('f_RMS');
        obj.buckets = ImageType('buckets', struct('intervals_0', [], 'intervals_1', [], 'intervals_2', [], 'M0', []));
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
        obj.power_adapt = ImageType('power_adapt');
        obj.pure_phase = ImageType('pure_phase');
        obj.doppler_variance_mod = ImageType('doppler_variance_mod');
        obj.doppler_variance_mod_pha = ImageType('doppler_variance_mod_pha');
        obj.amplitude_decorrelation = ImageType('amplitude_decorrelation');
        obj.diff_mod = ImageType('diff_mod');
        obj.diff_mod_pha = ImageType('diff_mod_pha');
        obj.phase_diff = ImageType('phase_diff');
        obj.phase_variance = ImageType('phase_variance');
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

        for i = 1:length(fields)
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

    function construct_image(obj, Params, SHin)
        f1 = Params.time_range(1);
        f2 = Params.time_range(2);

        r1 = Params.index_range(1);
        r2 = Params.index_range(2);
        [~, ~, NT] = size(SHin);

        % clear phase
        SH_mod = abs(SHin) .^ 2;
        SH_arg = angle(SHin);

        if obj.pure_PCA.is_selected

            if ~(r1 - floor(r1) == 0) && ~(r2 - floor(r2) == 0) %both not integer
                r1p = floor(r1 * 2 / Params.fs * NT);
                r2p = floor(r2 * 2 / Params.fs * NT);
            else
                r1p = r1;
                r2p = r2;
            end

            r1p = min(max(r1p, 1), NT);
            r2p = min(max(r2p, 1), NT);
            obj.pure_PCA.image = cumulant(SH_mod, r1p, r2p);
            obj.pure_PCA.image = flat_field_correction(obj.pure_PCA.image, Params.flatfield_gw);
        end

        if obj.power_Doppler.is_selected % Power Doppler has been chosen
            img = moment0(SH_mod, f1, f2, Params.fs, NT, Params.flatfield_gw);
            obj.power_Doppler.image = img;
        end

        if obj.power_adapt.is_selected %
            img = moment0(SH_mod, f1, f2, Params.fs, NT, 0);
            img = adapthisteq(rescale(img), "NumTiles", [12 12], "NBins", 128);
            obj.power_adapt.image = img;
        end

        if obj.power_Doppler_wiener.is_selected %
            img = moment0(SH_mod, f1, f2, Params.fs, NT, Params.flatfield_gw);
            obj.power_Doppler_wiener.image = wiener2(img, [2 2], 10);
        end

        if obj.power_1_Doppler.is_selected % Power Doppler 1 has been chosen
            img = moment1(SH_mod, f1, f2, Params.fs, NT, Params.flatfield_gw);
            obj.power_1_Doppler.image = img;
        end

        if obj.power_2_Doppler.is_selected % Power Doppler has been chosen
            img = moment2(SH_mod, f1, f2, Params.fs, NT, Params.flatfield_gw);
            obj.power_2_Doppler.image = img;
        end

        if obj.color_Doppler.is_selected % Color Doppler has been chosen

            if Params.time_range_extra < 0
                f3 = (f1 + f2) / 2;
            else
                f3 = Params.time_range_extra;
            end

            [freq_low, freq_high] = composite(SH_mod, f1, f3, f2, Params.fs, NT, max(Params.flatfield_gw, 20));
            obj.color_Doppler.image = construct_colored_image(gather(freq_low), gather(freq_high));
        end

        if obj.directional_Doppler.is_selected % Directional Doppler has been chosen
            [M0_pos, M0_neg] = directional(SH_mod, f1, f2, Params.fs, NT, max(Params.flatfield_gw, 20));
            obj.directional_Doppler.image = construct_directional_image(gather(M0_pos), gather(M0_neg));
        end

        if obj.spectrogram.is_selected

            try
                fi = figure("Visible", "off");
                freqs = ((0:(NT - 1)) - NT / 2) .* (Params.fs / NT);
                spect = fftshift(abs(squeeze(sum(SH_mod, [1 2]) / (size(SH_mod, 1) * size(SH_mod, 2))) .^ 2));

                plot(freqs, 10 * log10(spect));

                ylim([-60 150]);
                xlabel('Frequency (kHz)');
                ylabel('Power Spectrum Density (dB)');

                frame = getframe(fi); % Capture the figure
                % obj.spectrogram.graph = gca;
                obj.spectrogram.image = frame.cdata;
            catch

            end

        end

        if obj.broadening.is_selected

            try
                fi = figure("Visible", "off");
                disc = diskMask(size(SH_mod, 1), size(SH_mod, 2), Params.registration_disc_ratio)';
                spectrum_ploting(SH_mod(:, :, :), disc, Params.fs, Params.time_range(1), Params.time_range(2));
                % ylim([-0 50])
                frame = getframe(fi); % Capture the figure
                % obj.broadening.graph = gca;
                obj.broadening.image = frame.cdata;
            catch E
                disp(E)
            end

        end

        if obj.SH.is_selected
            bin_x = 4;
            bin_y = 4;
            bin_w = 16;
            obj.SH.parameters.SH = imresize3(gather(SH_mod), [size(SH_mod, 1) / bin_x size(SH_mod, 2) / bin_y size(SH_mod, 3) / bin_w], 'Method', 'linear');
            obj.SH.parameters.vector = zeros(1, NT);
        end

        if obj.autocorrelogram.is_selected

            try
                fi = figure("Visible", "off");
                indices = ((0:(NT - 1)) - NT / 2) .* (1 / (Params.fs * 1000));
                % disc = diskMask(size(SH,1),size(SH,2),0.7)';
                disc = ones(size(SH_mod, 1), size(SH_mod, 2));
                spect = squeeze(abs(sum(SH_mod .* disc, [1 2])) / nnz(disc));

                plot(indices, 10 * log10(spect));

                xlim([min(indices), max(indices)]);
                ylim([-60 180]);
                xlabel('Time (s)');
                ylabel('(dB)');

                frame = getframe(fi); % Capture the figure
                % obj.autocorrelogram.graph = gca;
                obj.autocorrelogram.image = frame.cdata;
            catch

            end

        end

        if obj.moment_0.is_selected % Moment 0 has been chosen
            img = moment0(SH_mod, f1, f2, Params.fs, NT, 0);
            obj.moment_0.image = img;
        end

        if obj.arg_0.is_selected % Arg 0 has been chosen
            img = moment0(SH_arg, f1, f2, Params.fs, NT, 0);
            obj.arg_0.image = img;
        end

        if obj.moment_1.is_selected % Moment 1 has been chosen
            img = moment1(SH_mod, f1, f2, Params.fs, NT, 0);
            obj.moment_1.image = img;
        end

        if obj.moment_2.is_selected % Moment 2 has been chosen
            img = moment2(SH_mod, f1, f2, Params.fs, NT, 0);
            obj.moment_2.image = img;
        end

        if obj.f_RMS.is_selected
            M0 = moment0(SH_mod, f1, f2, Params.fs, NT, 0);
            M2 = moment2(SH_mod, f1, f2, Params.fs, NT, 0);

            try
                fi = figure("Visible", "off");
                imagesc(sqrt(M2 ./ mean(M0, [1, 2])));
                %imagesc(sqrt(M2./M0));
                axis off; axis image;
                title("f_{RMS} (in kHz)")
                colormap("gray");
                colorbar;
                frame = getframe(fi); % Capture the figure
                % obj.f_RMS.graph = gca;
                obj.f_RMS.image = frame.cdata;
            catch
            end

        end

        if obj.pure_phase.is_selected
            %
            if ~(r1 - floor(r1) == 0) && ~(r2 - floor(r2) == 0) %both not integer
                r1p = floor(r1 * 2 / Params.fs * NT);
                r2p = floor(r2 * 2 / Params.fs * NT);
            else
                r1p = r1;
                r2p = r2;
            end

            r1p = min(max(r1p, 1), NT);
            r2p = min(max(r2p, 1), NT);
            obj.pure_phase.image = cumulant(SH_arg, r1p, r2p);
            obj.pure_phase.image = flat_field_correction(obj.pure_phase.image, Params.flatfield_gw);
        end

        if obj.doppler_variance_mod.is_selected %
            img = 1 - (2 * sum(SH_mod(:, :, 1:end - 1) .* SH_mod(:, :, 2:end), 3)) ./ (sum(SH_mod(:, :, 1:end - 1) .^ 2, 3) + sum(SH_mod(:, :, 2:end) .^ 2, 3));
            obj.doppler_variance_mod.image = img;
        end

        if obj.doppler_variance_mod_pha.is_selected %
            img = 1 - (2 * abs(sum(SHin(:, :, 1:end - 1) .* SHin(:, :, 2:end), 3))) ./ (sum(SH_mod(:, :, 1:end - 1) .^ 2, 3) + sum(SH_mod(:, :, 2:end) .^ 2, 3));
            obj.doppler_variance_mod_pha.image = img;
        end

        if obj.amplitude_decorrelation.is_selected %
            S = 0;
            M = size(SH_mod, 3);

            for ii = 1:(M - 1)
                S = S + SH_mod(:, :, ii) .* SH_mod(:, :, ii + 1) ./ (SH_mod(:, :, ii) .^ 2 + SH_mod(:, :, ii + 1) .^ 2);
            end

            img = 1 - 1 / (M - 1) * S;
            obj.amplitude_decorrelation.image = img;
        end

        if obj.diff_mod.is_selected %
            M = size(SH_mod, 3);
            img = 1 - 1 / (M - 1) * sum(diff(SH_mod, 1, 3), 3);
            obj.diff_mod.image = img;
        end

        if obj.diff_mod_pha.is_selected %
            M = size(SH_mod, 3);
            img = 1 - 1 / (M - 1) * sum(abs(diff(SHin, 1, 3)), 3);
            obj.diff_mod_pha.image = img;
        end

        if obj.phase_diff.is_selected %
            img = mean(diff(SH_arg, 1, 3), 3);
            obj.phase_diff.image = img;
        end

        if obj.phase_variance.is_selected %
            M = size(SH_mod, 3);
            img = 1 / (M - 1) * std(diff(SH_arg, 1, 3), [], 3);
            obj.phase_variance.image = img;
        end

        if obj.buckets.is_selected % buckets has been chosen
            numX = size(SH_mod, 1);
            numY = size(SH_mod, 2);
            buckranges = reshape(Params.buckets_ranges, [], 2);
            numranges = size(buckranges, 1);
            obj.buckets.parameters.intervals_0 = zeros(numX, numY, 1, numranges, 'single');
            obj.buckets.parameters.intervals_1 = zeros(numX, numY, 1, numranges, 'single');
            obj.buckets.parameters.intervals_2 = zeros(numX, numY, 1, numranges, 'single');
            obj.buckets.parameters.M0 = zeros(numX, numY, 1, numranges, 'single');
            % why this here ? flatfield should be enough , circleMask = fftshift(diskMask(numY, numX, 0.15));

            for freqIdx = 1:numranges
                img = moment0(SH_mod, buckranges(freqIdx, 1), buckranges(freqIdx, 2), Params.fs, NT, 0);
                %img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));
                obj.buckets.parameters.intervals_0(:, :, :, freqIdx) = img;

                img = moment0(SH_mod, buckranges(freqIdx, 1), buckranges(freqIdx, 2), Params.fs, NT, Params.flatfield_gw);
                obj.buckets.parameters.M0(:, :, :, freqIdx) = img;

                img = moment1(SH_mod, buckranges(freqIdx, 1), buckranges(freqIdx, 2), Params.fs, NT, 0);
                %img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));
                obj.buckets.parameters.intervals_1(:, :, :, freqIdx) = img;

                img = moment2(SH_mod, buckranges(freqIdx, 1), buckranges(freqIdx, 2), Params.fs, NT, 0);
                %img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));
                obj.buckets.parameters.intervals_2(:, :, :, freqIdx) = img;
            end

        end

        if obj.denoised.is_selected

            try
                SHdenoised = denoiseNGMeet(SH_mod, 'Sigma', 0.01, 'NumIterations', 2);
                img = moment0(SHdenoised, f1, f2, Params.fs, NT, 0);
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
                [~, image] = max(diff(SH_mod(1:1:end, 1:1:end, 1:1:end), 1, 3), [], 3);

                obj.cluster_projection.image = image;

            catch ME
                % Display error message and line number
                fprintf('Error: %s\n', ME.message);
                fprintf('Occurred in: %s at line %d\n', ME.stack(1).name, ME.stack(1).line);
                obj.denoised.image = [];
            end

        end

    end

    function construct_image_from_FH(obj, Params, FHin)

        if obj.FH_modulus_mean.is_selected

            switch Params.spatial_transformation
                case 'angular spectrum' % log10
                    obj.FH_modulus_mean.image = squeeze(log10(fftshift(mean(abs(FHin), 3))));
                case 'Fresnel' % no log10
                    obj.FH_modulus_mean.image = squeeze((mean(abs(FHin), 3)));

            end

        end

        if obj.FH_arg_mean.is_selected

            switch Params.spatial_transformation
                case 'angular spectrum' %
                    obj.FH_arg_mean.image = squeeze((fftshift(mean(angle(FHin), 3))));
                case 'Fresnel'
                    obj.FH_arg_mean.image = squeeze((mean(angle(FHin), 3)));
            end

        end

    end

    function construct_image_from_SVD(obj, covin, Uin, szin)
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
            Uin = reshape(Uin, szin(1), szin(2), []);

            try
                fi = figure(Visible = "off");
                Uin = abs(Uin);
                Uin = rescale(Uin, InputMax = max(Uin, [], [1, 2]), InputMin = min(Uin, [], [1, 2]));
                C = cell(1, size(Uin, 3));

                for i = 1:size(Uin, 3)
                    C{i} = Uin(:, :, i)';
                end

                montage(C, 'BorderSize', [0 0]);

                set(gca, 'Position', [0 0 1 1]); % Remove extra spaceù=
                frame = getframe(fi);
                % obj.SVD_U.graph = gca;
                obj.SVD_U.image = frame.cdata;
            catch

            end

        end

    end

    function construct_image_from_ShackHartmann(obj, moment_chunks_crop_array, ShackHartmannMask)

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
