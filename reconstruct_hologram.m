function [hologram0, sqrt_hologram0, hologram1, hologram2, composite_1, composite_2, composite_3] = reconstruct_hologram(FH, f1, f2, acquisition, gaussian_width, use_gpu, svd, phase_correction)
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

if exist('phase_correction', 'var')
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

% composite
nrange_1 = n1:n2;
red_1 = nrange_1(1:floor(numel(nrange_1)/4));
green_1 = nrange_1(floor(numel(nrange_1)/4):floor(numel(nrange_1)/2));
blue_1 =  nrange_1(floor(numel(nrange_1)/2):end);
nrange_2 = n3:n4;
red_2 = nrange_2(1:floor(numel(nrange_2)/4));
green_2 = nrange_2(floor(numel(nrange_2)/4):floor(numel(nrange_2)/2));
blue_2 =  nrange_2(floor(numel(nrange_2)/2):end);
composite_1 = squeeze(sum(abs(SH(:, :, red_1)), 3)) + squeeze(sum(abs(SH(:, :, red_2)), 3));
composite_2 = squeeze(sum(abs(SH(:, :, green_1)), 3)) + squeeze(sum(abs(SH(:, :, green_2)), 3));
composite_3 = squeeze(sum(abs(SH(:, :, blue_1)), 3)) + squeeze(sum(abs(SH(:, :, blue_2)), 3));
composite_1 = composite_1 ./ imgaussfilt(composite_1, gaussian_width);
composite_2 = composite_2 ./ imgaussfilt(composite_2, gaussian_width);
composite_3 = composite_3 ./ imgaussfilt(composite_3, gaussian_width);

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

