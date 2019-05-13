function [moment] = compute_moment(batch, kernel, f1, f2, fs, delta_x, delta_y, gaussian_width, phase_correction)
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

%% complex valued hologram
FH = fftshift(fft2(batch));
FH = FH .* kernel;

if exist('phase_correction', 'var')
    FH = FH .* exp(-1i * phase_correction);
end

H = ifft2(FH);

%% squared magnitude of hologram
SH = fft(H, [], 3);
SH = abs(SH).^2;
SH = permute(SH, [2 1 3]);
SH = circshift(SH, [delta_x, delta_y, 0]);

%% moment
j_win = size(batch, 3);
% convert frequency bounds to indices bounds
n1 = round(f1 * j_win / fs);
n2 = round(f2 * j_win / fs);
moment = squeeze(sum(abs(SH(:, :, n1:n2)), 3));
% apply flat field correction
moment = moment ./ imgaussfilt(moment, gaussian_width);
end