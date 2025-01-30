function classtogui(HD,app)

% handles all command transfer from HD to app

app.fs.Value = HD.params.fs;
app.lambda.Value = HD.params.lambda;
app.ppx.Value = HD.params.ppx;
app.ppy.Value = HD.params.ppy;
app.parfor_arg.Value = HD.params.parfor_arg;
app.batch_size.Value = HD.params.batch_size;
app.batch_size_registration.Value = HD.params.batch_size_registration;

app.batch_stride.Value = HD.params.batch_stride;
app.frame_position.Value = HD.params.frame_position;
app.registration_disc_ratio.Value = HD.params.registration_disc_ratio;
app.image_types.Items = properties(ImageTypeList2);
app.image_types.Value = HD.params.image_types;
app.frame_position.Value = HD.params.frame_position;
app.positioninfileSlider.Value = HD.params.frame_position;
app.positioninfileSlider.Limits = [1 HD.file.num_frames];
app.image_registration.Value = HD.params.image_registration;


app.spatial_filter.Value = HD.params.spatial_filter;
app.spatial_filter_range1.Value = HD.params.spatial_filter(1);
app.spatial_filter_range2.Value = HD.params.spatial_filter(2);
app.spatial_transformation.Items = {"Fresnel","angular spectrum","None"};
app.spatial_transformation.Value = HD.params.spatial_transformation;
app.spatial_propagation.Value = HD.params.spatial_propagation;
app.svd_filter.Value = HD.params.svd_filter;
app.svdx_filter.Value = HD.params.svdx_filter;
app.svd_threshold.Value = HD.params.svd_threshold;
app.time_transform.Items = {"FFT", "PCA", "ICA", "None"}; 
app.time_transform.Value = HD.params.time_transform;
app.time_range1.Value = HD.params.time_range(1);
app.time_range2.Value = HD.params.time_range(2);
app.flatfield_gw.Value = HD.params.flatfield_gw;




app.show_image_type.Items = properties(ImageTypeList2);
app.show_image_type.Value = HD.params.image_types{1}; %default to the first


end