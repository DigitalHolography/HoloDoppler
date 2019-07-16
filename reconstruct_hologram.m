function [hologram0, hologram0_sym, hologram1, hologram1_sym] = reconstruct_hologram(FH, f1, f2, acquisition, gaussian_width, use_gpu, phase_correction)
% Compute the moment of a batch of interferograms
%
% batch: the input interferograms batch
%
% kernel: wave propagation kernel
% 
% f_lower, f_upper: frequency integration bounds
%
% fs: batch sampling frequency
%
% delta_x, delta_y: coordinates shifts to put the center of
% the interferograms at position (0, 0)
%
% phase_correction: optional parameter

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

%% squared magnitude of hologram
SH = fft(H, [], 3);
SH = abs(SH).^2;

%% shifts related to acquisition wrong positioning
SH = permute(SH, [2 1 3]);
SH = circshift(SH, [-ac.delta_y, ac.delta_x, 0]);

%% moment

% hologram0
n1 = round(f1 * j_win / ac.fs) + 1;
n2 = round(f2 * j_win / ac.fs);
moment = squeeze(sum(abs(SH(:, :, n1:n2)), 3));
ms = sum(sum(moment,1),2);

% apply flat field correction
moment = moment ./ imgaussfilt(moment, gaussian_width);
ms2 = sum(sum(moment,1),2);
moment = (ms / ms2) * moment;
hologram0 = gather(moment);

% hologram0_sym
n3 = size(SH, 3) - n2;
n4 = size(SH, 3) - n1;
moment_sym = moment + squeeze(sum(abs(SH(:, :, n3:n4)), 3));
moment_sym = moment_sym ./ imgaussfilt(moment_sym, gaussian_width);
hologram0_sym = moment_sym;

% hologram1
f_range = (n1:n2) .* (ac.fs / j_win);
SH(:,:,n1:n2) = SH(:,:,n1:n2) .* reshape(f_range, 1, 1, numel(f_range));
% for i = 0:numel(f_range)-1
%    SH(:, :, n1 + i) = SH(:, :, n1 + i) * f_range(i + 1);
% end
moment1 = gather(squeeze(sum(abs(SH(:, :, n1:n2)), 3)));
moment1 = moment1 ./ imgaussfilt(moment1, gaussian_width);
hologram1 = moment1;

% hologram1_sym
f_range_sym = (-n2:-n1) .* (ac.fs / j_win);
SH(:,:,n3:n4) = SH(:,:,n3:n4) .* reshape(f_range_sym, 1, 1, numel(f_range_sym));
moment1_sym = moment1 + gather(squeeze(sum(abs(SH(:, :, n3:n4)), 3)));
moment1_sym = moment1_sym ./ imgaussfilt(moment1_sym, gaussian_width);
hologram1_sym = moment1_sym;
end