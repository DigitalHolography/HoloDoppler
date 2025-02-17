function classtogui(HD,app)

% handles all command transfer from HD to app

app.fs.Value = HD.params.fs;
app.lambda.Value = HD.params.lambda;
app.ppx.Value = HD.params.ppx;
app.ppy.Value = HD.params.ppy;
app.Nx.Value = double(HD.file.Nx);
app.Ny.Value = double(HD.file.Ny);
app.parfor_arg.Value = HD.params.parfor_arg;
app.batch_size.Value = HD.params.batch_size;
app.batch_size_registration.Value = HD.params.batch_size_registration_ref;

app.batch_stride.Value = HD.params.batch_stride;
app.frame_position.Value = HD.params.frame_position;
app.registration_disc_ratio.Value = HD.params.registration_disc_ratio;
app.Image_typesListBox.Items = properties(ImageTypeList2);
app.Image_typesListBox.Value = HD.params.image_types;
app.frame_position.Value = HD.params.frame_position;
app.positioninfileSlider.Value = HD.params.frame_position;
app.positioninfileSlider.Limits = double([1 HD.file.num_frames]);
app.image_registration.Value = HD.params.image_registration;
app.num_frames.Text = strcat('/ ',num2str(HD.file.num_frames));


app.spatial_filter.Value = HD.params.spatial_filter;
app.spatial_filter_range1.Value = HD.params.spatial_filter_range(1);
app.spatial_filter_range2.Value = HD.params.spatial_filter_range(2);
app.spatial_transformation.Items = ["Fresnel","angular spectrum","None"];
app.spatial_transformation.Value = HD.params.spatial_transformation;
app.spatial_propagation.Value = HD.params.spatial_propagation;
app.svd_filter.Value = HD.params.svd_filter;
app.svdx_filter.Value = HD.params.svdx_filter;
app.svd_threshold.Value = HD.params.svd_threshold;
app.time_transform.Items = ["FFT", "PCA", "ICA", "None"];
app.time_transform.Value = HD.params.time_transform;
app.time_range1.Value = HD.params.time_range(1);
app.time_range2.Value = HD.params.time_range(2);
app.flat_field_gw.Value = HD.params.flatfield_gw;

app.ShackHartmannCheckBox.Value = ~isempty(HD.params.ShackHartmannCorrection);
if ~isempty(HD.params.ShackHartmannCorrection)
    app.ZernikeProjectionCheckBox.Value = HD.params.ShackHartmannCorrection.ZernikeProjection;
    app.shackhartmannzernikeranksEditField.Value = HD.params.ShackHartmannCorrection.zernikeranks;
    app.subapnumpositionsEditField.Value = HD.params.ShackHartmannCorrection.subapnumpositions;
    app.imagesubapsizeratioEditField.Value = HD.params.ShackHartmannCorrection.imagesubapsizeratio;
    app.subaperturemarginEditField.Value = HD.params.ShackHartmannCorrection.subaperturemargin;
    app.referenceimageDropDown.Value = HD.params.ShackHartmannCorrection.referenceimage;
end
end