function scan3D = Show_3D_scan(app)

if ~app.file_loaded
    return
end
f = waitbar(0,'Please wait ...');



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
f1 = app.f1EditField.Value;
f2 = app.f2EditField.Value;
blur = app.blurEditField.Value;

z_list = (app.z_reconstruction - 0.1):0.005:(app.z_reconstruction + 0.1);

scan3D = zeros([app.Nx,app.Ny,length(z_list)]);

i=1;

for z_ = z_list


    waitbar(i/length(z_list),f,'Please wait while 3D scan ...');

    switch spatial_transformation
        case 'angular spectrum'
            kernelAngularSpectrum = propagation_kernelAngularSpectrum(app.Nx, app.Ny, z_, app.wavelengthEditField.Value, app.pix_width, app.pix_height, false);
            FH = fftshift(fft2(app.frame_batch)) .* kernelAngularSpectrum;
        case 'Fresnel'
            kernelFresnel = propagation_kernelFresnel(app.Nx, app.Ny, z_, app.wavelengthEditField.Value, app.pix_width, app.pix_height, false);
            FH = app.frame_batch .* kernelFresnel;
    end
    
    switch spatial_transformation
        case 'angular spectrum'
            H = ifft2(FH);
        case 'Fresnel'
            H = fftshift(fft2(FH));
    end

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

    scan3D(:,:,i) = (moment0(SH, f1, f2, app.Fs/1000, size(app.frame_batch,3), blur))';
    i = i+1;
end

close(f)

implay(rescale(scan3D));
% Careful too much points crashes matlab

% figure(58)
% 
% X = linspace(-app.Nx/2*app.pix_width,app.Nx/2*app.pix_width,app.Nx);
% Y = linspace(-app.Ny/2*app.pix_height,app.Ny/2*app.pix_height,app.Ny);
% Z = single(z_list);
% isosurface(X,Y,Z,scan3D)

% scan3Dbin = scan3D(1:8:end,1:8:end,:);
% figure(58);isosurface(X(1:8:end),Y(1:8:end),Z,rescale(scan3Dbin),0.6)

end