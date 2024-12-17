function SH = ri(frame_batch,spatial_transformation,kernel,svd,svdx,svd_threshold,svdx_nb_sub_ap,use_gpu)
    % ri -> render image : main rendering pipeline
    FH = single(zeros(size(frame_batch)))+1j*single(zeros(size(frame_batch)));
    switch spatial_transformation
        case 'angular spectrum'
            FH = fftshift(fft2(frame_batch)) .* kernel;
        case 'Fresnel'
            FH = frame_batch .* kernel;
    end
    H = single(zeros(size(frame_batch)))+1j*single(zeros(size(frame_batch)));
    switch spatial_transformation
        case 'angular spectrum'
            H = ifft2(FH);
        case 'Fresnel'
            H = fftshift(fft2(FH));
    end
    if svd
        H = sf(H, svd_threshold);
    end
    if svdx
        H = sfx(H, svd_threshold, svdx_nb_sub_ap );
    end
    SH = fft(H, [], 3);
    SH = abs(SH).^2; %% loosing phase ...
end