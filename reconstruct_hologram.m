function [hologram0, sqrt_hologram0, hologram1, hologram2, freq_low, freq_high] = reconstruct_hologram(FH, f1, f2, acquisition, gaussian_width, use_gpu, svd, phase_correction,...
                                                                                                       color_f1, color_f2, color_f3)
% Compute the moment of a batch of interferograms
%
% INPUT ARGUMENT
% FH: the preprocessed input interferograms batch
% kernel: wave propagation kernel
% f1, f2: frequency integration bounds
% acquisition: a DopplerAcquisition struct containing informations
%              about the experimental setup
% gaussian_width: size of the gaussian filter
% use_gpu: use gpu or not for the reconstruction
% svd: add SVD filtering to hologram reconstruction
% phase_correction: optional parameter, a phase correction to apply before
%                   reconstructing the hologram
%
% OUTPUT ARGUMENTS
% hologram0: M0
% sqrt_hologram0: sqrt(M0)
% hologram1: M1
% hologram2: M2
% composite_(1|2|3): reduced frequency bands of M0 to create a composite
%                    RGB image in post processing

j_win = size(FH, 3);
ac = acquisition;

% move data to gpu if available
if use_gpu
    if exist('phase_correction', 'var')
        phase_correction = gpuArray(phase_correction);
    end
end

if exist('phase_correction', 'var') && ~isempty(phase_correction)
    FH = FH .* exp(-1i * phase_correction);
end

H = ifft2(FH);
clear FH;

%% SVD filtering
if svd
    H = svd_filter(H, f1, ac.fs);
end

%% squared magnitude of hologram
SH = fft(H, [], 3);
SH = abs(SH).^2;

%% shifts related to acquisition wrong positioning
SH = permute(SH, [2 1 3]);
SH = circshift(SH, [-ac.delta_y, ac.delta_x, 0]);

%% moment

% hologram0

% integration interval
n1 = round(f1 * j_win / ac.fs) + 1;
n2 = round(f2 * j_win / ac.fs);
% symetric integration interval
n3 = size(SH, 3) - n2 + 2;
n4 = size(SH, 3) - n1 + 2;
moment = squeeze(sum(abs(SH(:, :, n1:n2)), 3)) + squeeze(sum(abs(SH(:, :, n3:n4)), 3));
ms = sum(sum(moment,1),2);
sqrt_moment = sqrt(moment);

% apply flat field correction
moment = moment ./ imgaussfilt(moment, gaussian_width);
sqrt_moment = sqrt_moment ./ imgaussfilt(sqrt_moment, gaussian_width);
ms2 = sum(sum(moment,1),2);
moment = (ms / ms2) * moment;
hologram0 = gather(moment);
sqrt_hologram0 = gather(sqrt_moment);

% low and high frequency bands
if exist('color_f3', 'var')
    freq_1 = color_f1;
    freq_2 = color_f2;
    freq_3 = color_f3;
    low_n1 = round(freq_1 * j_win / ac.fs) + 1;
    low_n2 = round(freq_2 * j_win / ac.fs);
    high_n1 = low_n2 + 1;
    high_n2 = round(freq_3 * j_win / ac.fs);

    freq_low = squeeze(sum(abs(SH(:, :, low_n1:low_n2)), 3));
    freq_high = squeeze(sum(abs(SH(:, :, high_n1:high_n2)), 3));
    freq_low = freq_low ./ imgaussfilt(freq_low, gaussian_width);
    freq_high = freq_high./ imgaussfilt(freq_high, gaussian_width);
else
    freq_low = [];
    freq_high = [];
end

% hologram1
f_range = (n1:n2) .* (ac.fs / j_win);
f_range_sym = (-n2:-n1) .* (ac.fs / j_win);
SH(:,:,n1:n2) = SH(:,:,n1:n2) .* reshape(f_range, 1, 1, numel(f_range));
SH(:,:,n3:n4) = SH(:,:,n3:n4) .* reshape(f_range_sym, 1, 1, numel(f_range_sym));
moment1 = gather(squeeze(sum(abs(SH(:, :, n1:n2)), 3))) + gather(squeeze(sum(abs(SH(:, :, n3:n4)), 3)));
ms = sum(sum(moment,1),2);
moment1 = moment1 ./ imgaussfilt(moment1, gaussian_width);
ms2 = sum(sum(moment,1),2);
moment1 = (ms/ms2) * moment1;
hologram1 = moment1;

% hologram2
% scale SH again
SH(:,:,n1:n2) = SH(:,:,n1:n2) .* reshape(f_range, 1, 1, numel(f_range));
SH(:,:,n3:n4) = SH(:,:,n3:n4) .* reshape(f_range_sym, 1, 1, numel(f_range_sym));
moment2 = gather(squeeze(sum(abs(SH(:, :, n1:n2)), 3))) + gather(squeeze(sum(abs(SH(:, :, n3:n4)), 3)));
moment2 = sqrt(moment2);
moment2 = moment2 ./ imgaussfilt(moment2, gaussian_width);
hologram2 = moment2;
end

