function SH2 = construct_SH(FH, f1, acquisition, use_gpu, svd, phase_correction)

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
SH2 = abs(SH).^2; 

%% shifts related to acquisition wrong positioning
SH2 = permute(SH2, [2 1 3]);
SH2 = circshift(SH2, [-ac.delta_y, ac.delta_x, 0]);

end
