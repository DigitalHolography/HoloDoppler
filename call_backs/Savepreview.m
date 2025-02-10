function Savepreview(app)

%FIXME only works for FFT and darkfield doesn't work "out of gpu
%memory"

app.savelamp.Color = [1, 0, 0];
drawnow;
app.cache = GuiCache(app);

% ,''dark_field_image',
acquisition = DopplerAcquisition(app.Nx,app.Ny,app.Fs/1000, app.z_reconstruction, app.z_retina, app.z_iris, app.wavelengthEditField.Value,app.DX,app.DY,app.pix_width,app.pix_height);

GPUpreview = check_GPU_for_preview(app);
compute_FH(app,GPUpreview);

[~,file_name,~] = fileparts(app.filename);

folder_name = strcat( file_name, '_preview');
if exist(fullfile(app.filepath, folder_name), 'dir')
    output_dirpath = fullfile(app.filepath, folder_name);
else
    mkdir(fullfile(app.filepath,folder_name));
    output_dirpath = fullfile(app.filepath, folder_name);
end
preview_folder_name = create_output_directory_name(output_dirpath, sprintf('%s_%s.%s', file_name,'preview', 'cine'));
mkdir(fullfile(output_dirpath,preview_folder_name));
output_dirpath = fullfile(output_dirpath, preview_folder_name);

%Compute and save all the doppler images save them


mkdir(fullfile(output_dirpath, 'png'));
folder_path_png = fullfile(output_dirpath, 'png');
mkdir(fullfile(output_dirpath, 'freq_shift'));
folder_path_freq = fullfile(output_dirpath, 'freq_shift');

%% PNG

app.var_ImageTypeList.clear();
app.var_ImageTypeList.select('power_Doppler','color_Doppler','directional_Doppler','velocity_estimate', 'phase_variation',  'spectrogram');
app.var_ImageTypeList.construct_image(app.FH, app.cache.wavelength, acquisition, app.blur, false, app.SVDCheckBox.Value, app.SVDThresholdCheckBox.Value,app.SVDStrideEditField.Value,...
    app.SVDxCheckBox.Value, app.SVDThresholdEditField.Value, app.SVDx_SubApEditField.Value, [], app.compositef1EditField.Value, app.compositef2EditField.Value, app.compositef3EditField.Value, app.spatialTransformationDropDown.Value, app.time_transform, app.SubAp_PCA, app.xystrideEditField.Value, app.unitcellsinlatticeEditField.Value, app.r1EditField.Value, ...
    app.temporalCheckBox.Value, app.phi1EditField.Value, app.phi2EditField.Value, app.spatialCheckBox.Value, app.nu1EditField.Value, app.nu2EditField.Value, app.numFreqEditField.Value);
 app.var_ImageTypeList.images2png(preview_folder_name,folder_path_png,'power_Doppler','color_Doppler','directional_Doppler','velocity_estimate', 'phase_variation',  'spectrogram')
%% Spectrum

Show_spectrum(app);
preview_spectrum_name = sprintf('%s_%s.%s', preview_folder_name, "spectrum_of_the_full_image", 'png');
saveas(57,fullfile(folder_path_png,preview_spectrum_name));
close(57);

%% Frequency Shift
freq_nyq = app.Fs/1000;
local_num_frame = 5;

freq_basse = linspace(0.2,freq_nyq/8,local_num_frame);
freq_haute = linspace(1,freq_nyq/2,local_num_frame);

%video = zeros(app.Nx, app.Ny, 1, 5*local_num_frame,'single');
app.var_ImageTypeList.clear();
app.var_ImageTypeList.select('power_Doppler');

for i=1:local_num_frame

    app.time_transform.f1 = freq_basse(i);
    app.time_transform.f2 = freq_haute(i);
   app.var_ImageTypeList.construct_image(app.FH, app.cache.wavelength, acquisition, app.blur, false, app.SVDCheckBox.Value, app.SVDThresholdCheckBox.Value,app.SVDStrideEditField.Value,...
    app.SVDxCheckBox.Value, app.SVDThresholdEditField.Value, app.SVDx_SubApEditField.Value, [], app.compositef1EditField.Value, app.compositef2EditField.Value, app.compositef3EditField.Value, app.spatialTransformationDropDown.Value, app.time_transform, app.SubAp_PCA, app.xystrideEditField.Value, app.unitcellsinlatticeEditField.Value, app.r1EditField.Value, ...
    app.temporalCheckBox.Value, app.phi1EditField.Value, app.phi2EditField.Value, app.spatialCheckBox.Value, app.nu1EditField.Value, app.nu2EditField.Value, app.numFreqEditField.Value);
 
    app.hologram = app.var_ImageTypeList.('power_Doppler').image;
    app.hologram = flip(app.hologram);
    app.hologram = mat2gray(app.hologram);
    image_temp_2 = app.hologram;

    preview_name_freq = sprintf('%s_%s_%.1f_%.1f.%s', preview_folder_name, 'freq_shift',round(app.time_transform.f1,1) ,round(app.time_transform.f2,1) , 'png');
    imwrite(image_temp_2, fullfile(folder_path_freq, preview_name_freq));

    %Generate a video of the freq shift
    %video(:,:,:,indice) = image_temp_2;
    %video(:,:,:,indice+1) = image_temp_2;
    %video(:,:,:,indice+2) = image_temp_2;
    %video(:,:,:,indice+3) = image_temp_2;
    %video(:,:,:,indice+4) = image_temp_2;
    %indice = indice+5;


end

app.var_ImageTypeList.clear();

%Correctly name and write the precomputated images
preview_name = sprintf('%s.%s', preview_folder_name, 'png');
image_left = app.ImageLeft.ImageSource;
alpha = 10;

if app.ShackHartmannCheckBox.Value
    image_right = app.ImageRight.ImageSource;


    image_phase = mat2gray(app.phasePlane);
    image_psf2D = mat2gray((ones(app.Nx)-abs(fftshift(ifft2(exp(1i*alpha.*app.phasePlane))))));


end

if app.ShackHartmannCheckBox.Value
    preview_name_sh = sprintf('%s_%s.%s', preview_folder_name, 'SH', 'png');
    preview_name_phase = sprintf('%s_%s.%s', preview_folder_name, 'phase', 'png');
    preview_name_psf2D = sprintf('%s_%s.%s', preview_folder_name, 'psf2D', 'png');

    imwrite(image_right, fullfile(folder_path_png, preview_name_sh));
    imwrite(image_phase, fullfile(folder_path_png, preview_name_phase));
    imwrite(image_psf2D, fullfile(folder_path_png, preview_name_psf2D));
end


imwrite(image_left, fullfile(folder_path_png, preview_name));

app.savelamp.Color = [0, 1, 0];

end

