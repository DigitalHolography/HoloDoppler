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

FH=[];

if svd
    if svd_treshold
        H = svd_filter(H, time_transform.f1, app.Fs/1000,svd_treshold_value);
    else
        H = svd_filter(H, time_transform.f1,app.Fs/1000);
    end
end

if (svdx)
    if svd_treshold
        H = svd_x_filter(H, time_transform.f1, app.Fs/1000,Nb_SubAp,svd_treshold_value);
    else
        H = svd_x_filter(H, time_transform.f1, app.Fs/1000, Nb_SubAp);
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
H=[];

SH = abs(SH).^2;

% [X,Y]=meshgrid(((1:app.Nx) - round(app.Nx/2))*2/app.Nx,((1:app.Ny) - round(app.Ny/2))*2/app.Nx);
% circle = X.^2+Y.^2<0.5;
% imshow(circle);
circle = single(ones([app.Nx,app.Ny]));
spectrum = squeeze(sum(SH.*circle,[1,2])/nnz(circle)); % The full spectrum of the power doppler image

fullfreq = linspace(-app.Fs/2,app.Fs/2,length(spectrum));

plot(fullfreq/1000, 10*log(fftshift(spectrum)),'k-', 'LineWidth', 2)
hold on 
xline(time_transform.f1,'k--', 'LineWidth', 2)
xline(time_transform.f2,'k--', 'LineWidth', 2)
xline(-time_transform.f1,'k--', 'LineWidth', 2)
xline(-time_transform.f2,'k--', 'LineWidth', 2)
hold off
title('Spectrum');
fontsize(gca, 14, "points");
xlabel("Frequency (kHz)", 'FontSize', 14);
ylabel("S(f) (dB)", 'FontSize', 14);
pbaspect([1.618 1 1]);
set(gca, 'LineWidth', 2);
axis tight;
end