function SH = riassf(frame_batch, kernel, svd_threshold)
    % ri -> render image : main rendering pipeline
    % Angularspectrum
    % SVD filter

    FH = fftshift(fft2(frame_batch)) .* kernel;

    H = ifft2(FH);

    H = sf(H, svd_threshold);

    SH = fft(H, [], 3);
    SH = abs(SH) .^ 2; % % loosing phase ...
end
