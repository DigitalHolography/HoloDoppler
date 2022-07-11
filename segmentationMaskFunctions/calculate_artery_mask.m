function mask = calculate_vessels_mask(video, contrast_enhancement_tol, temporal_filter_sigma, contrast_inversion, export_raw, export_avg_img)

%% temporal filter
if ~isempty(temporal_filter_sigma)
    sigma = [0.0001 0.0001 temporal_filter_sigma];
    for c = 1:size(video, 3)
        video(:,:,c,:) = imgaussfilt3(squeeze(video(:,:,c,:)), sigma);
    end
end

%% fix intensity flashes
video = video - mean(mean(video, 2), 1);

%% contrast enhancement
if ~isempty(contrast_enhancement_tol)
    tol_pdi_low = contrast_enhancement_tol;  % default 0.0005
    tol_pdi = [tol_pdi_low 1-tol_pdi_low];
    video = enhance_video_constrast(video, tol_pdi);
end



%% contrast inversion
if contrast_inversion
    video = -1.0 * video;
end

%% prepare for writing
video = mat2gray(video);




    video = squeeze(video);
    mask = squeeze(std(video, 0, 3));
    mask = imbinarize((mask), 'adaptive', 'ForegroundPolarity', 'bright', 'Sensitivity', 0.2);
    pulse = squeeze(mean(video .* mask, [1 2]));

    pulse_init = pulse - mean(pulse, "all");
    C = video;
    for kk = 1:size(video, 3)
        C(:,:,kk) = video(:,:,kk) - squeeze(mean(video, 3));
    end
    pulse_init_3d = zeros(size(video));
    for mm = 1:size(video, 1)
        for pp = 1:size(video, 2)
            pulse_init_3d(mm,pp,:) = pulse_init;
        end
    end
    C = C .* pulse_init_3d;
    C = squeeze(mean(C, 3));

    mask = C > max(C(:))*0.2;

    mask = flip(mask);

end