classdef ImageTypeList < handle
% Registry of every image type the rendering pipeline can produce.
%
% Usage pattern:
%   list.select('power_Doppler', 'directional_Doppler')
%   ... run pipeline ...
%   list.construct_image(Params, SH)
%   img = list.power_Doppler.image;

% -----------------------------------------------------------------------
properties
    % --- Doppler variants -----------------------------------------------
    power_Doppler
    power_1_Doppler
    power_2_Doppler
    color_Doppler
    directional_Doppler
    broadening
    power_Doppler_wiener
    power_adapt

    % --- Spectral moments -----------------------------------------------
    moment_0
    moment_1
    moment_2
    arg_0
    f_RMS

    % --- Raw / intermediate field ---------------------------------------
    SH
    SH_avg
    FH_modulus_mean
    FH_arg_mean

    % --- SVD outputs ----------------------------------------------------
    SVD_cov
    SVD_U

    % --- Correlation / variance -----------------------------------------
    doppler_variance_mod
    doppler_variance_mod_pha
    amplitude_decorrelation
    diff_mod
    diff_mod_pha
    phase_diff
    phase_variance

    % --- Spectral statistics --------------------------------------------
    cumulative_distribution
    band_ratio
    color_band_ratio
    entropy
    negentropy

    % --- Frequency buckets ----------------------------------------------
    buckets
    full_buckets
end

% -----------------------------------------------------------------------
methods

    function obj = ImageTypeList()

        % Doppler
        obj.power_Doppler = ImageType('power', struct('M0sqrt', []));
        obj.power_1_Doppler = ImageType('power1');
        obj.power_2_Doppler = ImageType('power2');
        obj.color_Doppler = ImageType('color', struct('freq_low', [], 'freq_high', []));
        obj.directional_Doppler = ImageType('directional', struct('M0_pos', [], 'M0_neg', []));
        obj.broadening = ImageType('broadening');
        obj.power_Doppler_wiener = ImageType('power_wiener');
        obj.power_adapt = ImageType('power_adapt');

        % Moments
        obj.moment_0 = ImageType('M0');
        obj.moment_1 = ImageType('M1');
        obj.moment_2 = ImageType('M2');
        obj.arg_0 = ImageType('arg0');
        obj.f_RMS = ImageType('f_RMS');

        % Raw field
        obj.SH = ImageType('SH', struct('vector', [], 'SH', []));
        obj.SH_avg = ImageType('SH_avg', struct('SH', []));
        obj.FH_modulus_mean = ImageType('FH_modulus_mean');
        obj.FH_arg_mean = ImageType('FH_arg_mean');

        % SVD
        obj.SVD_cov = ImageType('SVD_cov');
        obj.SVD_U = ImageType('SVD_U');

        % Correlation / variance
        obj.doppler_variance_mod = ImageType('doppler_variance_mod');
        obj.doppler_variance_mod_pha = ImageType('doppler_variance_mod_pha');
        obj.amplitude_decorrelation = ImageType('amplitude_decorrelation');
        obj.diff_mod = ImageType('diff_mod');
        obj.diff_mod_pha = ImageType('diff_mod_pha');
        obj.phase_diff = ImageType('phase_diff');
        obj.phase_variance = ImageType('phase_variance');

        % Spectral statistics
        obj.cumulative_distribution = ImageType('cdf');
        obj.band_ratio = ImageType('energy_ratio');
        obj.color_band_ratio = ImageType('color_energy_ratio');
        obj.entropy = ImageType('entropy');
        obj.negentropy = ImageType('negentropy');

        % Buckets
        obj.buckets = ImageType('buckets', struct('intervals_0', [], 'intervals_1', [], ...
            'intervals_2', [], 'M0', []));
        obj.full_buckets = ImageType('full_buckets', struct('SH_full', []));
    end

    % ------------------------------------------------------------------
    function clear(obj, varargin)
        % clear()          – clear all image types
        % clear(n1, n2, …) – clear only the named types
        targets = obj.resolveTargets(varargin);

        for k = 1:numel(targets)
            obj.(targets{k}).clear();
        end

    end

    % ------------------------------------------------------------------
    function select(obj, varargin)
        % select()          – deselect all (same as clear)
        % select('all')     – select all
        % select(n1, n2, …) – select only named types (all others cleared first)
        obj.clearAll();

        if nargin == 1
            return % caller wants nothing selected
        end

        if isscalar(varargin) && isequal(varargin{1}, 'all')
            allFields = fieldnames(obj);

            for k = 1:numel(allFields)
                obj.(allFields{k}).select();
            end

            return
        end

        for k = 1:numel(varargin)
            obj.(varargin{k}).select();
        end

    end

    % ------------------------------------------------------------------
    function copy_from(obj, src)
        fields = fieldnames(src);

        for k = 1:numel(fields)
            obj.(fields{k}).copy_from(src.(fields{k}));
        end

    end

    % ------------------------------------------------------------------
    function images2png(obj, preview_folder_name, folder_path, varargin)
        % images2png(pfx, dir)          – save all selected images
        % images2png(pfx, dir, n1, …)   – save only named (if selected)
        if isempty(varargin)
            targets = fieldnames(obj);
        else
            targets = varargin;
        end

        for k = 1:numel(targets)
            slot = obj.(targets{k});

            if slot.is_selected
                slot.image2png(preview_folder_name, folder_path);
            end

        end

    end

    % ------------------------------------------------------------------
    function construct_image(obj, Params, SHin)
        % Populate all selected image slots from the short-time-transformed
        % complex field SHin  [Nx × Ny × T].

        if isempty(SHin), return, end

        f1 = Params.frequencyRange1;
        f2 = Params.frequencyRange2;
        fi1 = Params.frequencyRangeInter1;
        fi2 = Params.frequencyRangeInter2;
        [~, ~, batchSize] = size(SHin);
        fs = Params.fs;
        gw = Params.flatfield_gw;

        SH_mod = abs(SHin) .^ 2;
        SH_arg = angle(SHin);

        % --- Power Doppler variants ------------------------------------
        if obj.power_Doppler.is_selected
            obj.power_Doppler.image = moment0(SH_mod, f1, f2, fs, batchSize, gw);
        end

        if obj.power_Doppler_wiener.is_selected
            base = moment0(SH_mod, f1, f2, fs, batchSize, gw);
            obj.power_Doppler_wiener.image = wiener2(base, [2 2], 10);
        end

        if obj.power_adapt.is_selected
            base = moment0(SH_mod, f1, f2, fs, batchSize);
            obj.power_adapt.image = adapthisteq(rescale(base), ...
                'NumTiles', [12 12], 'NBins', 128);
        end

        if obj.power_1_Doppler.is_selected
            obj.power_1_Doppler.image = moment1(SH_mod, f1, f2, fs, batchSize, gw);
        end

        if obj.power_2_Doppler.is_selected
            obj.power_2_Doppler.image = moment2(SH_mod, f1, f2, fs, batchSize, gw);
        end

        % --- Color / directional Doppler --------------------------------
        if obj.color_Doppler.is_selected
            f3 = obj.midOrExtra(f1, f2, Params.frequencyRange_extra);
            [freq_low, freq_high] = composite(SH_mod, f1, f3, f2, fs, batchSize, max(gw, 20));
            obj.color_Doppler.image = construct_colored_image(gather(freq_low), gather(freq_high));
        end

        if obj.directional_Doppler.is_selected
            [M0_pos, M0_neg] = directional(SH_mod, f1, f2, fs, batchSize, max(gw, 20));
            obj.directional_Doppler.image = construct_directional_image(gather(M0_pos), gather(M0_neg));
        end

        % --- Spectral broadening plot -----------------------------------
        if obj.broadening.is_selected
            obj.broadening.image = obj.renderBroadeningPlot(SH_mod, Params, fs);
        end

        % --- Raw SH output ---------------------------------------------
        if obj.SH.is_selected
            obj.SH.parameters.SH = gather(SH_mod); % full-res, no binning
            obj.SH.parameters.vector = zeros(1, batchSize);
        end

        if obj.SH_avg.is_selected
            obj.SH_avg.parameters.SH = mean(gather(SH_mod), 3);
        end

        % --- Spectral moments ------------------------------------------
        if obj.moment_0.is_selected
            obj.moment_0.image = moment0(SH_mod, f1, f2, fs, batchSize);
        end

        if obj.moment_1.is_selected
            obj.moment_1.image = moment1(SH_mod, f1, f2, fs, batchSize);
        end

        if obj.moment_2.is_selected
            obj.moment_2.image = moment2(SH_mod, f1, f2, fs, batchSize);
        end

        if obj.arg_0.is_selected
            obj.arg_0.image = moment0(SH_arg, f1, f2, fs, batchSize);
        end

        if obj.f_RMS.is_selected
            M0 = moment0(SH_mod, f1, f2, fs, batchSize);
            M2 = moment2(SH_mod, f1, f2, fs, batchSize);
            obj.f_RMS.image = sqrt(M2 ./ mean(M0, [1, 2]));
        end

        % --- Correlation / variance ------------------------------------
        if obj.doppler_variance_mod.is_selected
            A = SH_mod(:, :, 1:end - 1);
            B = SH_mod(:, :, 2:end);
            obj.doppler_variance_mod.image = 1 - (2 .* sum(A .* B, 3)) ./ (sum(A .^ 2, 3) + sum(B .^ 2, 3));
        end

        if obj.doppler_variance_mod_pha.is_selected
            A = SH_mod(:, :, 1:end - 1);
            B = SH_mod(:, :, 2:end);
            Ac = SHin(:, :, 1:end - 1);
            Bc = SHin(:, :, 2:end);
            obj.doppler_variance_mod_pha.image = ...
                1 - (2 .* abs(sum(Ac .* Bc, 3))) ./ (sum(A .^ 2, 3) + sum(B .^ 2, 3));
        end

        if obj.amplitude_decorrelation.is_selected
            A = SH_mod(:, :, 1:end - 1);
            B = SH_mod(:, :, 2:end);
            S = sum(A .* B ./ (A .^ 2 + B .^ 2), 3);
            obj.amplitude_decorrelation.image = 1 - S ./ (size(SH_mod, 3) - 1);
        end

        if obj.diff_mod.is_selected
            M = size(SH_mod, 3);
            obj.diff_mod.image = 1 - sum(diff(SH_mod, 1, 3), 3) ./ (M - 1);
        end

        if obj.diff_mod_pha.is_selected
            M = size(SHin, 3);
            obj.diff_mod_pha.image = 1 - sum(abs(diff(SHin, 1, 3)), 3) ./ (M - 1);
        end

        if obj.phase_diff.is_selected
            obj.phase_diff.image = mean(diff(SH_arg, 1, 3), 3);
        end

        if obj.phase_variance.is_selected
            M = size(SH_mod, 3);
            obj.phase_variance.image = std(diff(SH_arg, 1, 3), [], 3) ./ (M - 1);
        end

        % --- Spectral statistics ---------------------------------------
        if obj.cumulative_distribution.is_selected
            obj.cumulative_distribution.image = cdf(SH_mod, f1, f2, fs, 0.5, batchSize);
        end

        if obj.band_ratio.is_selected
            obj.band_ratio.image = energy_ratio(SH_mod, f1, f2, fi1, fi2, fs, batchSize);
        end

        if obj.color_band_ratio.is_selected
            obj.color_band_ratio.image = color_energy_ratio(SH_mod, f1, f2, fi1, fi2, fs, batchSize);
        end

        if obj.entropy.is_selected
            obj.entropy.image = spectral_entropy(SH_mod, f1, f2, fs, batchSize);
        end

        if obj.negentropy.is_selected
            obj.negentropy.image = spectral_negentropy(SH_mod, f1, f2, fs, batchSize);
        end

        % --- Frequency buckets -----------------------------------------
        if obj.buckets.is_selected
            obj.computeBuckets(SH_mod, Params, fs, batchSize, gw);
        end

        if obj.full_buckets.is_selected
            obj.computeFullBuckets(SH_mod);
        end

    end

    % ------------------------------------------------------------------
    function construct_image_from_FH(obj, Params, FHin)
        % Populate FH_modulus_mean and FH_arg_mean from the Fourier-domain field.

        if isempty(FHin), return, end

        isAngular = strcmp(Params.spatialTransformation, 'angular spectrum');

        if obj.FH_modulus_mean.is_selected
            m = mean(abs(FHin), 3);

            if isAngular
                m = log10(fftshift(m));
            end

            obj.FH_modulus_mean.image = squeeze(m);
        end

        if obj.FH_arg_mean.is_selected
            m = mean(angle(FHin), 3);

            if isAngular
                m = fftshift(m);
            end

            obj.FH_arg_mean.image = squeeze(m);
        end

    end

    % ------------------------------------------------------------------
    function construct_image_from_SVD(obj, ~, covin, Uin, szin)
        % Populate SVD_cov and SVD_U.
        % szin – size of the H batch [Nx Ny Nt] for reshaping Uin.

        if isempty(covin)
            obj.SVD_cov.image = [];
            obj.SVD_U.image = [];
            return
        end

        if obj.SVD_cov.is_selected
            obj.SVD_cov.image = abs(covin);
        end

        if obj.SVD_U.is_selected
            obj.SVD_U.image = obj.renderSvdMontage(Uin, szin);
        end

    end

end % public methods

% -----------------------------------------------------------------------
methods (Access = private)

    function clearAll(obj)
        fields = fieldnames(obj);

        for k = 1:numel(fields)
            obj.(fields{k}).clear();
        end

    end

    % ------------------------------------------------------------------
    function targets = resolveTargets(obj, args)
        % Return the list of field names to act on.
        if isempty(args)
            targets = fieldnames(obj);
        else
            targets = args;
        end

    end

    % ------------------------------------------------------------------
    function f3 = midOrExtra(~, f1, f2, extra)

        if extra < 0
            f3 = (f1 + f2) / 2;
        else
            f3 = extra;
        end

    end

    % ------------------------------------------------------------------
    function img = renderBroadeningPlot(~, SH_mod, Params, fs)
        % Render the spectral broadening plot into a raster image.
        img = [];

        try
            fi = figure('Visible', 'off');
            disk = diskMask(size(SH_mod, 1), size(SH_mod, 2), Params.registrationDiskRatio)';
            spectrum_ploting(SH_mod, disk, fs, Params.frequencyRange1, Params.frequencyRange2);
            frame = getframe(fi);
            img = frame.cdata;
            close(fi);
        catch E
            MEdisp(E);
        end

    end

    % ------------------------------------------------------------------
    function img = renderSvdMontage(~, Uin, szin)
        % Render the SVD spatial modes as a montage and return raster data.
        img = [];

        try
            fi = figure('Visible', 'off');
            U3 = reshape(Uin, szin(1), szin(2), []);
            U3 = abs(U3);
            U3 = rescale(U3, 'InputMax', max(U3, [], [1, 2]), ...
                'InputMin', min(U3, [], [1, 2]));
            C = arrayfun(@(k) U3(:, :, k)', 1:size(U3, 3), 'UniformOutput', false);
            montage(C, 'BorderSize', [0 0]);
            set(gca, 'Position', [0 0 1 1]);
            frame = getframe(fi);
            img = frame.cdata;
            close(fi);
        catch E
            MEdisp(E);
        end

    end

    % ------------------------------------------------------------------
    function computeBuckets(obj, SH_mod, Params, fs, batchSize, gw)
        [numX, numY, ~] = size(SH_mod);
        buckranges = reshape(Params.bucketsRanges, [], 2);

        if buckranges(1, 1) == -1
            % Auto-define 32 equal buckets up to Nyquist
            edges = linspace(0, fs / 2, 17);
            buckranges = [edges(1:end - 1)', edges(2:end)'];
        end

        numRanges = size(buckranges, 1);

        obj.buckets.parameters.intervals_0 = zeros(numX, numY, 1, numRanges, 'single');
        obj.buckets.parameters.intervals_1 = zeros(numX, numY, 1, numRanges, 'single');
        obj.buckets.parameters.intervals_2 = zeros(numX, numY, 1, numRanges, 'single');
        obj.buckets.parameters.M0 = zeros(numX, numY, 1, numRanges, 'single');

        for rIdx = 1:numRanges
            r1 = buckranges(rIdx, 1);
            r2 = buckranges(rIdx, 2);
            obj.buckets.parameters.intervals_0(:, :, :, rIdx) = moment0(SH_mod, r1, r2, fs, batchSize);
            obj.buckets.parameters.intervals_1(:, :, :, rIdx) = moment1(SH_mod, r1, r2, fs, batchSize);
            obj.buckets.parameters.intervals_2(:, :, :, rIdx) = moment2(SH_mod, r1, r2, fs, batchSize);
            obj.buckets.parameters.M0(:, :, :, rIdx) = moment0(SH_mod, r1, r2, fs, batchSize, gw);
        end

        obj.buckets.image = mean(obj.buckets.parameters.M0, [3 4]);
    end

    % ------------------------------------------------------------------
    function computeFullBuckets(obj, SH_mod)
        [numX, numY, nFreq] = size(SH_mod);
        nBuckets = 32;
        edges = round(linspace(1, nFreq + 1, nBuckets + 1));

        SH_full = zeros(numX, numY, nBuckets, 'single');

        for bIdx = 1:nBuckets
            i1 = edges(bIdx);
            i2 = edges(bIdx + 1) - 1;
            SH_full(:, :, bIdx) = single(log(mean(SH_mod(:, :, i1:i2), 3)));
        end

        obj.full_buckets.parameters.SH_full = SH_full;
    end

end % private methods

end % classdef
