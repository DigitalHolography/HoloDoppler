function SH = ri(frame_batch,spatial_transformation,kernel,svd,svdx,svd_threshold,use_gpu)
    % ri -> render image : main rendering pipeline
    switch spatial_transformation
        case 'angular spectrum'
            FH = fftshift(fft2(frame_batch)) .* kernel;
        case 'Fresnel'
            FH = frame_batch .* kernel;
    end
    
    switch spatial_transformation
        case 'angular spectrum'
            H = ifft2(FH);
        case 'Fresnel'
            H = fftshift(fft2(FH));
    end
    FH = [];
    if svd
        H = sf(H, svd_threshold);
    end
    if svdx
        H = sfx(H, svd_threshold);
    end
    SH = fft(H, [], 3);
    H = [];
    SH = abs(SH).^2; %% loosing phase ...
end