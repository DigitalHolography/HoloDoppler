function Show_spectrum(app)
    % Shows the spectrum of the preview batch if any

    if ~app.file_loaded
        return
    end

    figure(57)

    use_gpu = false;
    spatial_transformation = app.spatialTransformationDropDown.Value;
    svd = app.SVDCheckBox.Value;
    svd_treshold = app.SVDTresholdCheckBox.Value;
    svd_treshold_value = app.SVDTresholdEditField.Value;
    svdx = app.SVDxCheckBox.Value;
    Nb_SubAp = app.SVDx_SubApEditField.Value;
    local_spatial = app.spatialCheckBox.Value;
    local_temporal = app.temporalCheckBox.Value;
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

    if local_spatial
        H = local_spatial_PCA(H, nu1, nu2);
    end

    if local_temporal
        H = local_temporal_PCA(H, phi1, phi2);
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

    % if you want it can be a circle
    % [X,Y]=meshgrid(((1:app.Nx) - round(app.Nx/2))*2/app.Nx,((1:app.Ny) - round(app.Ny/2))*2/app.Nx);
    % circle = X.^2+Y.^2<0.5;
    % imshow(circle);
    if ~isempty(app.mask)
        circle = app.mask;
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
    f = fit(x', double(y), l);

    plot(x / 1000, double(y), 'k-', 'LineWidth', 2); hold on; plot(x / 1000, feval(f, x), 'k--', 'LineWidth', 2); hold on; % plot(x,1/pi*(1/2*1)./(x.^2+(1/2*1)^2)*50e9) ;hold on
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
    figure(58)
    spectrum_angle = squeeze(sum(SH_angle .* circle, [1, 2]) / nnz(circle));

    plot(fullfreq / 1000, 180 / pi * fftshift(spectrum_angle), 'k-', 'LineWidth', 2)
    hold on
    xline(time_transform.f1, 'k--', 'LineWidth', 2)
    xline(time_transform.f2, 'k--', 'LineWidth', 2)
    xline(-time_transform.f1, 'k--', 'LineWidth', 2)
    xline(-time_transform.f2, 'k--', 'LineWidth', 2)
    hold off
    title('Spectrum');
    fontsize(gca, 14, "points");
    xlabel("Frequency (kHz)", 'FontSize', 14);
    ylabel("arg(S(f)) (°)", 'FontSize', 14);
    pbaspect([1.618 1 1]);
    set(gca, 'LineWidth', 2);
    axis tight;

end
