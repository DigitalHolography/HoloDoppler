function compute_hologram(app, use_gpu)

if ~app.file_loaded
    return;
end

% update cache parameters
% save all gui parameters to a struct.
% The current computation will fetch every parameter
% from the cache and not from the gui.
% The purpose of this is to prevent gui interactions
% to mess up the parameters while a computation is ongoing.
app.var_ImageTypeList.clear();
app.cache = GuiCache(app);

%FIXME : change function name DopplerAcquisition ->
%HologramRenderingParameters & Remove Fs ?
acquisition = DopplerAcquisition(app.Nx,app.Ny,app.Fs/1000, app.z_reconstruction, app.z_retina, app.z_iris, app.wavelengthEditField.Value,app.DX,app.DY,app.pix_width,app.pix_height);
is_low_frequency = app.lowfrequencyCheckBox.Value;

% change the reconstruction type name to a form compatible with
% structures
type = (strrep(app.ImageChoiceDropDown.Value, ' ', '_'));

% set the select_boolean field value to true for the chosen
% reconstruction
switch app.time_transform.type
    case 'FFT'
        type = (strrep(app.ImageChoiceDropDown.Value, ' ', '_'));
    case 'PCA'
        type = 'pure_PCA';
end

app.var_ImageTypeList.(type).select();
% reconstruct given image and store it in the struct


if strcmp((type), 'dark_field_image')
    app.z_reconstruction = app.z_retina;
    compute_kernel(app, use_gpu);
    compute_FH(app, use_gpu);
    app.Switch.Value = 'z_retina';
    %ZSwitchValueChanged(app, []);
end

app.var_ImageTypeList.construct_image(app.FH, app.cache.wavelength, acquisition, app.blur, use_gpu, app.SVDCheckBox.Value, app.SVDTresholdCheckBox.Value,...
    app.SVDxCheckBox.Value, app.SVDTresholdEditField.Value, app.SVDx_SubApEditField.Value, [], app.compositef1EditField.Value, app.compositef2EditField.Value, app.compositef3EditField.Value, is_low_frequency, app.spatialTransformationDropDown.Value, app.time_transform, app.SubAp_PCA, app.xystrideEditField.Value, app.unitcellsinlatticeEditField.Value, app.r1EditField.Value, ...
    app.temporalCheckBox.Value, app.phi1EditField.Value, app.phi2EditField.Value, app.spatialCheckBox.Value, app.nu1EditField.Value, app.nu2EditField.Value, app.numFreqEditField.Value);

app.FH = [];
%% FIXME
%             H_df = app.images.dark_field_image.H;
%             [file_name, suffix] = get_last_file_name(app.filepath, 'H_df');
%             output_dirname = sprintf('%s%s_%d.mat', app.filepath, file_name, suffix + 1);
%             save(output_dirname, 'H_df');

app.hologram = app.var_ImageTypeList.(type).image;
app.hologram = flip(app.hologram);
app.var_ImageTypeList.clear();


end