function Show_spectrum(app)
    % Shows the spectrum of the preview batch if any

    if ~app.file_loaded
        return
    end

    figure(57)

    use_gpu = false;
    spatial_transformation = app.spatialTransformationDropDown.Value;
    svd = app.SVDCheckBox.Value;
    svd_treshold = app.SVDThresholdCheckBox.Value;
    svd_treshold_value = app.SVDThresholdEditField.Value;
    svdx = app.SVDxCheckBox.Value;
    Nb_SubAp = app.SVDx_SubApEditField.Value;
    is_spatial = app.spatialCheckBox.Value;
    is_temporal = app.temporalCheckBox.Value;
    time_transform = app.time_transform;
    nu1 = app.nu1EditField.Value;
    nu2 = app.nu2EditField.Value;
    phi1 = app.phi1EditField.Value;
    phi2 = app.phi2EditField.Value;

    if use_gpu

        switch spatial_transformation
            case 'angular spectrum'
                FH = fftshift(fft2(gpuArray(app.frame_batch))) .* app.kernelAngularSpectrum;
            case 'Fresnel'
                FH = gpuArray((app.frame_batch) .* app.kernelFresnel);
        end

    else % no gpu

        switch spatial_transformation
            case 'angular spectrum'
                FH = fftshift(fft2(app.frame_batch)) .* app.kernelAngularSpectrum;
            case 'Fresnel'
                FH = (app.frame_batch) .* app.kernelFresnel;
        end

    end

    switch spatial_transformation
        case 'angular spectrum'
            H = ifft2(FH);
        case 'Fresnel'
            H = fftshift(fft2(FH));
    end

    FH = [];

    if svd

        if svd_treshold
            H = svd_filter(H, time_transform.f1, app.Fs / 1000, svd_treshold_value);
        else
            H = svd_filter(H, time_transform.f1, app.Fs / 1000);
        end

    end

    if (svdx)

        if svd_treshold
            H = svd_x_filter(H, time_transform.f1, app.Fs / 1000, Nb_SubAp, svd_treshold_value);
        else
            H = svd_x_filter(H, time_transform.f1, app.Fs / 1000, Nb_SubAp);
        end

    end

    if is_spatial
        H = spatial_PCA(H, nu1, nu2);
    end

    if is_temporal
        H = temporal_PCA(H, phi1, phi2);
    end

    switch time_transform.type
        case 'PCA' % if the time transform is PCA
            SH = short_time_PCA(H);
        case 'FFT' % if the time transform is FFT
            SH = fft(H, [], 3);
    end

    H = [];

    SH_angle = angle(SH);
    SH = abs(SH) .^ 2;

    if ~isempty(app.mask)
        circle = imrotate(app.mask,90);
    else
        circle = ones([app.Ny,app.Nx]);
    end
    spectrum = squeeze(sum(SH .* circle, [1, 2]) / nnz(circle)); % The full spectrum of the power doppler image

    j_win = size(app.frame_batch, 3);
    fullfreq = fftshift([0:j_win / 2 - 1, -j_win / 2:-1] * app.Fs / (j_win));

    % fitting to a lorentizian
    exclude = abs(fullfreq) < time_transform.f1 * 1000;

    x = fullfreq;
    y = double(10 * log(fftshift(spectrum / sum(spectrum(fftshift(~exclude))))));

    lorentzEqn = @(a, b, x) ...
        10 * log(1 ./ ((1 + abs(x / a) .^ b)) / sum(1 ./ ((1 + abs(fullfreq(~exclude) / a) .^ b))));
    l = fittype(lorentzEqn);
    try f = fit(x', double(y), l);catch disp('Error fitting'); f.a='x';f.b='x';end

    plot(x / 1000, double(y), 'k-', 'LineWidth', 2); hold on; try plot(x / 1000, feval(f, x), 'k--', 'LineWidth', 2); hold on;end % plot(x,1/pi*(1/2*1)./(x.^2+(1/2*1)^2)*50e9) ;hold on
    xline(time_transform.f1, 'k--', 'LineWidth', 2)
    xline(time_transform.f2, 'k--', 'LineWidth', 2)
    xline(-time_transform.f1, 'k--', 'LineWidth', 2)
    xline(-time_transform.f2, 'k--', 'LineWidth', 2)
    hold off
    legend('avg spectrum', ['lorentzian model 1/(1+(x/a)^b)', 'a = ', num2str(f.a), ' b = ', num2str(f.b)]);
    title('Spectrum');
    fontsize(gca, 14, "points");
    xlabel("Frequency (kHz)", 'FontSize', 14);
    ylabel("S(f) (dB)", 'FontSize', 14);
    pbaspect([1.618 1 1]);
    set(gca, 'LineWidth', 2);
    axis tight;
    axis padded;
    % figure(58)
    % spectrum_angle = squeeze(sum(SH_angle .* circle, [1, 2]) / nnz(circle));
    % 
    % plot(fullfreq / 1000, 180 / pi * fftshift(spectrum_angle), 'k-', 'LineWidth', 2)
    % hold on
    % xline(time_transform.f1, 'k--', 'LineWidth', 2)
    % xline(time_transform.f2, 'k--', 'LineWidth', 2)
    % xline(-time_transform.f1, 'k--', 'LineWidth', 2)
    % xline(-time_transform.f2, 'k--', 'LineWidth', 2)
    % hold off
    % title('Spectrum');
    % fontsize(gca, 14, "points");
    % xlabel("Frequency (kHz)", 'FontSize', 14);
    % ylabel("arg(S(f)) (°)", 'FontSize', 14);
    % pbaspect([1.618 1 1]);
    % set(gca, 'LineWidth', 2);
    % axis tight;

    [~,filename,file_ext] = fileparts(app.filename);
    [found_dir, found] = get_last_output_dir(app.filepath, filename, file_ext);
    if found
        if isfolder(fullfile(app.filepath,found_dir,'pulsewave','mask'))
            if exist(fullfile(app.filepath,found_dir,'pulsewave','mask','forceMaskArtery.png'))
                disp('found artery mask')
                maskArtery = mat2gray(mean(imread(fullfile(app.filepath,found_dir,'pulsewave','mask','forceMaskArtery.png')), 3)) > 0;
                maskArtery = imrotate(maskArtery,-90);
            elseif ~isempty(app.mask)
                maskArtery = imrotate(app.mask,-90);
            end
           
                
                maskArtery = imresize(maskArtery,[app.Ny,app.Nx])>0;
                % maskNeighbors = imresize(maskNeighbors,[app.Ny,app.Nx])>0;
                maskNeighbors = imdilate(maskArtery, strel('disk', 4)) - imdilate(maskArtery, strel('disk', 1)); %PW_params.local_background_width = 2

                figure(59)

                spectruma = squeeze(sum(SH .* maskArtery, [1, 2]) / nnz(maskArtery));
                spectrumb = squeeze(sum(SH .* maskNeighbors, [1, 2]) / nnz(maskNeighbors));
                plot(fullfreq / 1000, 10*log10(fftshift(spectruma)), 'r-', 'LineWidth', 1); hold on;
                plot(fullfreq / 1000, 10*log10(fftshift(spectrumb)), 'k-', 'LineWidth', 1); 
                xline(time_transform.f1, 'k--', 'LineWidth', 1)
                xline(time_transform.f2, 'k--', 'LineWidth', 1)
                xline(-time_transform.f1, 'k--', 'LineWidth', 1)
                xline(-time_transform.f2, 'k--', 'LineWidth', 1)
                hold off
                legend('artery', 'neighbors');
                title('Spectrum');
                fontsize(gca, 14, "points");
                xlabel("Frequency (kHz)", 'FontSize', 14);
                ylabel("S(f) (dB)", 'FontSize', 14);
                pbaspect([1.618 1 1]);
                set(gca, 'LineWidth', 2);
                axis tight;
                axis padded;

                figure(60)
                indxs = fftshift(abs(fullfreq) > time_transform.f1);
                IM0 = rescale(sum(SH(:,:,indxs),3));
                IM0 = repmat(IM0,1,1,3);
                IM0(:,:,1) = maskArtery+ ~(maskArtery|maskNeighbors).*IM0(:,:,1);
                IM0(:,:,2) = maskNeighbors+ ~(maskArtery|maskNeighbors).*IM0(:,:,1);
                imshow(IM0);
                axis image;
        end

    end

end
