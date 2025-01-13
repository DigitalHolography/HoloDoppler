function scan3D = Show_3D_scan(app)

if ~app.file_loaded
    return
end

f = waitbar(0, 'Please wait ...');

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
f1 = app.f1EditField.Value;
f2 = app.f2EditField.Value;
blur = app.blurEditField.Value;
numX = app.numX;
numY = app.numY;

z_list = (app.z_reconstruction - 0.1):0.005:(app.z_reconstruction + 0.1);

scan3D = zeros([numX, numY, length(z_list)]);
frame_batch = app.interferogram_stream.read_frame_batch(app.batchsizeEditField.Value, app.positioninfileSlider.Value);

i = 1;

for z_ = z_list

    waitbar(i / length(z_list), f, 'Please wait while 3D scan ...');

    switch spatial_transformation
        case 'angular spectrum'
            kernelAngularSpectrum = propagation_kernelAngularSpectrum(numX, numY, z_, app.wavelengthEditField.Value, app.pix_width, app.pix_height, false);
            FH = fftshift(fft2(frame_batch)) .* kernelAngularSpectrum;
        case 'Fresnel'
            kernelFresnel = propagation_kernelFresnel(numX, numY, z_, app.wavelengthEditField.Value, app.pix_width, app.pix_height, false);
            FH = frame_batch .* kernelFresnel;
    end

    switch spatial_transformation
        case 'angular spectrum'
            H = ifft2(FH);
        case 'Fresnel'
            H = fftshift(fft2(FH));
    end

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

    SH = abs(SH) .^ 2;

    scan3D(:, :, i) = (moment0(SH, f1, f2, app.Fs / 1000, size(frame_batch, 3), blur))';
    i = i + 1;
end

close(f)

implay(rescale(scan3D));

[~, file_name, ~] = fileparts(app.filename);
folder_name = strcat(file_name, '_preview');

if exist(fullfile(app.filepath, folder_name), 'dir')
    output_dirpath = fullfile(app.filepath, folder_name);
else
    mkdir(fullfile(app.filepath, folder_name));
    output_dirpath = fullfile(app.filepath, folder_name);
end

preview_folder_name = create_output_directory_name(output_dirpath, sprintf('%s_%s.%s', file_name, 'preview', 'cine'));
mkdir(fullfile(output_dirpath));
writeVideoOnDisk(rescale(scan3D), fullfile(output_dirpath, sprintf("%s_3Dscan", folder_name)));
% Careful too much points crashes matlab

% figure(58)
%
% X = linspace(-numX/2*app.pix_width,numX/2*app.pix_width,numX);
% Y = linspace(-numY/2*app.pix_height,numY/2*app.pix_height,numY);
% Z = single(z_list);
% isosurface(X,Y,Z,scan3D)

% scan3Dbin = scan3D(1:8:end,1:8:end,:);
% figure(58);isosurface(X(1:8:end),Y(1:8:end),Z,rescale(scan3Dbin),0.6)

end
