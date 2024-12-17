function SH = rifsf(frame_batch, kernel, svd_threshold)
    % ri -> render image : main rendering pipeline
    %Fresnel
    % SVD filter

    FH = frame_batch .* kernel;

    H = fftshift(fft2(FH));

    H = sf(H, svd_threshold);

    SH = fft(H, [], 3);
    SH = abs(SH) .^ 2; % % loosing phase ...
end
