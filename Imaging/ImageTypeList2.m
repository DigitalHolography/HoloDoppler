classdef ImageTypeList2 < handle

% images output types from the rendering pipeline
properties
    power_Doppler
    power_1_Doppler
    power_2_Doppler
    color_Doppler
    directional_Doppler
    broadening
    SH
    SH_avg
    moment_0
    moment_1
    moment_2
    arg_0
    f_RMS
    buckets
    full_buckets
    FH_modulus_mean
    FH_arg_mean
    SVD_cov
    SVD_U
    ShackHartmann_Cropped_Moments
    ShackHartmann_Phase
    power_Doppler_wiener
    power_adapt
    doppler_variance_mod
    doppler_variance_mod_pha
    amplitude_decorrelation
    diff_mod
    diff_mod_pha
    phase_diff
    phase_variance
    cumulative_distribution
    band_ratio
    color_band_ratio
    entropy
end

methods

    function obj = ImageTypeList2()
        obj.power_Doppler = ImageType('power', struct("M0sqrt", []));
        obj.power_1_Doppler = ImageType('power1');
        obj.power_2_Doppler = ImageType('power2');
        obj.color_Doppler = ImageType('color', struct('freq_low', [], 'freq_high', []));
        obj.directional_Doppler = ImageType('directional', struct('M0_pos', [], 'M0_neg', []));
        obj.broadening = ImageType('broadening');
        obj.SH = ImageType('SH', struct('vector', [], 'SH', []));
        obj.SH_avg = ImageType('SH_avg', struct('SH', []));
        obj.moment_0 = ImageType('M0');
        obj.moment_1 = ImageType('M1');
        obj.moment_2 = ImageType('M2');
        obj.arg_0 = ImageType('arg0');
        obj.f_RMS = ImageType('f_RMS');
        obj.buckets = ImageType('buckets', struct('intervals_0', [], 'intervals_1', [], 'intervals_2', [], 'M0', []));
        obj.full_buckets = ImageType('full_buckets', struct('SH_full', []));
        obj.FH_modulus_mean = ImageType('FH_modulus_mean');
        obj.FH_arg_mean = ImageType('FH_arg_mean');
        obj.SVD_cov = ImageType('SVD_cov');
        obj.SVD_U = ImageType('SVD_U');
        obj.ShackHartmann_Cropped_Moments = ImageType('ShackMoments');
        obj.ShackHartmann_Phase = ImageType('ShackPhase');
        obj.power_Doppler_wiener = ImageType('power_wiener');
        obj.power_adapt = ImageType('power_adapt');
        obj.doppler_variance_mod = ImageType('doppler_variance_mod');
        obj.doppler_variance_mod_pha = ImageType('doppler_variance_mod_pha');
        obj.amplitude_decorrelation = ImageType('amplitude_decorrelation');
        obj.diff_mod = ImageType('diff_mod');
        obj.diff_mod_pha = ImageType('diff_mod_pha');
        obj.phase_diff = ImageType('phase_diff');
        obj.phase_variance = ImageType('phase_variance');
        obj.cumulative_distribution = ImageType('cdf');
        obj.band_ratio = ImageType('energy_ratio');
        obj.color_band_ratio = ImageType('color_energy_ratio');
        obj.entropy = ImageType('entropy');
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
        f1 = Params.frequencyRange(1);
        f2 = Params.frequencyRange(2);
        fi1 = Params.frequencyRangeInter(1);
        fi2 = Params.frequencyRangeInter(2);

        [~, ~, batchSize] = size(SHin);
        fs = Params.fs;
        gw = Params.flatfield_gw;

        % clear phase
        SH_mod = abs(SHin) .^ 2;
        SH_arg = angle(SHin);

        if obj.power_Doppler.is_selected % Power Doppler has been chosen
            img = moment0(SH_mod, f1, f2, fs, batchSize, gw);
            obj.power_Doppler.image = img;
        end

        if obj.power_adapt.is_selected % Power Doppler with adaptive histogram equalization has been chosen
            img = moment0(SH_mod, f1, f2, fs, batchSize);
            img = adapthisteq(rescale(img), "NumTiles", [12 12], "NBins", 128);
            obj.power_adapt.image = img;
        end

        if obj.power_Doppler_wiener.is_selected %
            img = moment0(SH_mod, f1, f2, fs, batchSize, gw);
            obj.power_Doppler_wiener.image = wiener2(img, [2 2], 10);
        end

        if obj.power_1_Doppler.is_selected % Power Doppler 1 has been chosen
            img = moment1(SH_mod, f1, f2, fs, batchSize, gw);
            obj.power_1_Doppler.image = img;
        end

        if obj.power_2_Doppler.is_selected % Power Doppler has been chosen
            img = moment2(SH_mod, f1, f2, fs, batchSize, gw);
            obj.power_2_Doppler.image = img;
        end

        if obj.color_Doppler.is_selected % Color Doppler has been chosen

            if Params.frequencyRange_extra < 0
                f3 = (f1 + f2) / 2;
            else
                f3 = Params.frequencyRange_extra;
            end

            [freq_low, freq_high] = composite(SH_mod, f1, f3, f2, fs, batchSize, max(gw, 20));
            obj.color_Doppler.image = construct_colored_image(gather(freq_low), gather(freq_high));
        end

        if obj.directional_Doppler.is_selected % Directional Doppler has been chosen
            [M0_pos, M0_neg] = directional(SH_mod, f1, f2, fs, batchSize, max(gw, 20));
            obj.directional_Doppler.image = construct_directional_image(gather(M0_pos), gather(M0_neg));
        end

        if obj.broadening.is_selected

            try
                fi = figure("Visible", "off");
                disc = diskMask(size(SH_mod, 1), size(SH_mod, 2), Params.registration_disc_ratio)';
                spectrum_ploting(SH_mod(:, :, :), disc, fs, Params.frequencyRange(1), Params.frequencyRange(2));
                % ylim([-0 50])
                frame = getframe(fi); % Capture the figure
                % obj.broadening.graph = gca;
                obj.broadening.image = frame.cdata;
            catch E
                MEdisp(E);
            end

        end

        if obj.SH.is_selected
            bin_x = 1;
            bin_y = 1;
            bin_w = 1;
            obj.SH.parameters.SH = imresize3(gather(SH_mod), [size(SH_mod, 1) / bin_x size(SH_mod, 2) / bin_y size(SH_mod, 3) / bin_w], 'Method', 'linear');
            obj.SH.parameters.vector = zeros(1, batchSize);
        end

        if obj.cumulative_distribution.is_selected
            img = cdf(SH_mod, f1, f2, fs, 0.5, batchSize);
            obj.cumulative_distribution.image = img;
        end

        if obj.band_ratio.is_selected
            img = energy_ratio(SH_mod, f1, f2, fi1, fi2, fs, batchSize);
            obj.band_ratio.image = img;
        end

        if obj.color_band_ratio.is_selected
            color_img = color_energy_ratio(SH_mod, f1, f2, 5, 5, fs, batchSize);
            obj.color_band_ratio.image = color_img;
        end

        if obj.entropy.is_selected
            img = spectral_entropy(SH_mod, f1, f2, fs, batchSize);
            obj.entropy.image = img;
        end

        if obj.moment_0.is_selected % Moment 0 has been chosen
            img_M0 = moment0(SH_mod, f1, f2, fs, batchSize);
            obj.moment_0.image = img_M0;
        end

        if obj.arg_0.is_selected % Arg 0 has been chosen
            img_arg0 = moment0(SH_arg, f1, f2, fs, batchSize);
            obj.arg_0.image = img_arg0;
        end

        if obj.moment_1.is_selected % Moment 1 has been chosen
            img_M1 = moment1(SH_mod, f1, f2, fs, batchSize);
            obj.moment_1.image = img_M1;
        end

        if obj.moment_2.is_selected % Moment 2 has been chosen
            img_M2 = moment2(SH_mod, f1, f2, fs, batchSize);
            obj.moment_2.image = img_M2;
        end

        if obj.f_RMS.is_selected
            img_M0 = moment0(SH_mod, f1, f2, fs, batchSize);
            img_M2 = moment2(SH_mod, f1, f2, fs, batchSize);
            obj.f_RMS.image = sqrt(img_M2 ./ mean(img_M0, [1, 2]));
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
            buckranges = reshape(Params.bucketsRanges, [], 2);

            if buckranges(1) == -1
                disp("special case defining 32 buckets automatically");
                ra = linspace(0, fs / 2, 16 + 1);

                for kk = 1:(length(ra) - 1)
                    ra(kk)
                    buckranges(kk, :) = [ra(kk), ra(kk + 1)];
                end

            end

            numranges = size(buckranges, 1);
            obj.buckets.parameters.intervals_0 = zeros(numX, numY, 1, numranges, 'single');
            obj.buckets.parameters.intervals_1 = zeros(numX, numY, 1, numranges, 'single');
            obj.buckets.parameters.intervals_2 = zeros(numX, numY, 1, numranges, 'single');
            obj.buckets.parameters.M0 = zeros(numX, numY, 1, numranges, 'single');
            % why this here ? flatfield should be enough , circleMask = fftshift(diskMask(numY, numX, 0.15)); -> Michael

            for freqIdx = 1:numranges
                img = moment0(SH_mod, buckranges(freqIdx, 1), buckranges(freqIdx, 2), fs, batchSize);
                %img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));
                obj.buckets.parameters.intervals_0(:, :, :, freqIdx) = img;

                img = moment0(SH_mod, buckranges(freqIdx, 1), buckranges(freqIdx, 2), fs, batchSize, gw);
                obj.buckets.parameters.M0(:, :, :, freqIdx) = img;

                img = moment1(SH_mod, buckranges(freqIdx, 1), buckranges(freqIdx, 2), fs, batchSize);
                %img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));
                obj.buckets.parameters.intervals_1(:, :, :, freqIdx) = img;

                img = moment2(SH_mod, buckranges(freqIdx, 1), buckranges(freqIdx, 2), fs, batchSize);
                %img = img / (sum(img .* circleMask, [1 2]) / nnz(circleMask));
                obj.buckets.parameters.intervals_2(:, :, :, freqIdx) = img;
            end

            obj.buckets.image = mean(obj.buckets.parameters.M0, [3 4]);
        end

        if obj.full_buckets.is_selected
            numX = size(SH_mod, 1);
            numY = size(SH_mod, 2);
            nBuckets = 32;
            nFreq = size(SH_mod, 3);

            edges = round(linspace(1, nFreq + 1, nBuckets + 1));
            obj.full_buckets.parameters.SH_full = zeros(numX, numY, nBuckets, 'single');

            for freqIdx = 1:nBuckets
                i1 = edges(freqIdx);
                i2 = edges(freqIdx + 1) - 1;
                obj.full_buckets.parameters.SH_full(:, :, freqIdx) = ...
                    single(log(mean(SH_mod(:, :, i1:i2), 3)));
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

    function construct_image_from_SVD(obj, ~, covin, Uin, szin)
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
                MEdisp(E);
                obj.SVD_U.image = [];
            end

        end

    end

    function construct_image_from_ShackHartmann(obj, ~, moment_chunks_crop_array, ShackHartmannMask)

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
