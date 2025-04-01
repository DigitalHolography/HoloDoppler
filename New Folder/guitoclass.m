function guitoclass(HD, app)
% Transfers all values from app UI to HD.params

HD.params.fs = app.fs.Value;
HD.params.lambda = app.lambda.Value;
HD.params.ppx = app.ppx.Value;
HD.params.ppy = app.ppy.Value;
HD.params.parfor_arg = app.parfor_arg.Value;
HD.params.batch_size = app.batch_size.Value;
HD.params.batch_size_registration = app.batch_size_registration.Value;

HD.params.batch_stride = app.batch_stride.Value;
HD.params.frame_position = app.frame_position.Value;
HD.params.registration_disc_ratio = app.registration_disc_ratio.Value;

% Handle image types as a cell array
HD.params.image_types = app.Image_typesListBox.Value;

HD.params.frame_position = app.frame_position.Value;
HD.params.image_registration = app.image_registration.Value;

% Spatial filtering parameters
HD.params.spatial_filter = app.spatial_filter.Value;
HD.params.hilbert_filter = app.hilbert_filter.Value;
HD.params.spatial_filter_range = [app.spatial_filter_range1.Value, app.spatial_filter_range2.Value];
HD.params.spatial_transformation = app.spatial_transformation.Value;
HD.params.spatial_propagation = app.spatial_propagation.Value;

% SVD parameters
HD.params.svd_filter = app.svd_filter.Value;
HD.params.svdx_filter = app.svdx_filter.Value;
HD.params.svdx_t_filter = app.svdx_t_filter.Value;
HD.params.svd_threshold = app.svd_threshold.Value;
HD.params.svdx_threshold = app.svdx_threshold.Value;
HD.params.svdx_t_threshold = app.svdx_t_threshold.Value;
HD.params.svdx_Nsub = app.svdx_Nsub.Value;
HD.params.svdx_t_Nsub = app.svdx_t_Nsub.Value;


% Time transformation parameters
HD.params.time_transform = app.time_transform.Value;
HD.params.time_range = [app.time_range1.Value, app.time_range2.Value];
HD.params.index_range = [app.index_range1.Value, app.index_range2.Value];

% Flatfield correction
HD.params.flatfield_gw = app.flat_field_gw.Value;

HD.params.flip_y = app.flip_y.Value;

% Shack-Hartmann correction
if app.ShackHartmannCheckBox.Value
    HD.params.ShackHartmannCorrection.ZernikeProjection = app.ZernikeProjectionCheckBox.Value;
    HD.params.ShackHartmannCorrection.zernikeranks = app.shackhartmannzernikeranksEditField.Value;
    HD.params.ShackHartmannCorrection.subapnumpositions = app.subapnumpositionsEditField.Value;
    HD.params.ShackHartmannCorrection.imagesubapsizeratio = app.imagesubapsizeratioEditField.Value;
    HD.params.ShackHartmannCorrection.subaperturemargin = app.subaperturemarginEditField.Value;
    HD.params.ShackHartmannCorrection.referenceimage = app.referenceimageDropDown.Value;
else
    HD.params.ShackHartmannCorrection = [];
end


end
