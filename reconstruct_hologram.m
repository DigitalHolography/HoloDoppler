function [hologram] = reconstruct_hologram(FH, f1, f2, acquisition, gaussian_width, use_gpu, phase_correction)
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
% convert frequency bounds to indices bounds
n1 = round(f1 * j_win / ac.fs);
n2 = round(f2 * j_win / ac.fs);
moment = squeeze(sum(abs(SH(:, :, n1:n2)), 3));
clear SH;
% apply flat field correction
moment = moment ./ imgaussfilt(moment, gaussian_width);
hologram = gather(moment);
end