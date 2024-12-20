function [hologram0, sqrt_hologram0] = reconstruct_hologram(FH, acquisition, gaussian_width, use_gpu, svd, svd_treshold, svd_treshold_value, svdx, Nb_SubAp, phase_correction, time_transform, spatial_transformation)
% Compute the moment of a batch of interferograms.
% For more moment outputs, use reconstruct_hologram_extra, this function
% only computes one output for speed
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

switch spatial_transformation
    case 'angular spectrum'
        H = ifft2(FH);
    case 'Fresnel'
        H = fftshift(ifft2(FH));
end

% H = ifft2(FH);
clear FH;

%% SVD filtering
if (svd)
    if svd_treshold
        H = svd_filter(H, time_transform.f1, ac.fs, svd_treshold_value);
    else
        H = svd_filter(H, time_transform.f1, ac.fs);
    end
end

if (svdx)
    H = svd_x_filter(H, time_transform.f1, ac.fs, Nb_SubAp);
end

%% squared magnitude of hologram : SH
switch time_transform.type
    case 'PCA' % if the time transform is PCA
        SH = short_time_PCA(H);
        n1 = time_transform.f1;
        n2 = time_transform.f2;
    
    case 'FFT' % if the time transform is FFT
        SH = fft(H, [], 3);
        f1 = time_transform.f1;
        f2 = time_transform.f2;
end
clear("H");
SH = abs(SH).^2;
%% shifts related to acquisition wrong positioning
SH = permute(SH, [2 1 3]);
SH = circshift(SH, [-ac.delta_y, ac.delta_x, 0]);
%% moment

switch time_transform.type
    case 'PCA' % if the time transform is PCA
        [hologram0] = cumulant(SH, n1, n2);
    case 'FFT' % if the time transform is FFT
        [hologram0, sqrt_hologram0] = moment0(SH, f1, f2, ac.fs, j_win, gaussian_width);
end

end

