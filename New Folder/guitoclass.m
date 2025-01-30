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
    HD.params.image_types = app.image_types.Value;

    HD.params.frame_position = app.frame_position.Value;
    HD.params.frame_position = app.positioninfileSlider.Value;
    HD.file.num_frames = app.positioninfileSlider.Limits(2);
    HD.params.image_registration = app.image_registration.Value;

    % Spatial filtering parameters
    HD.params.spatial_filter = app.spatial_filter.Value;
    HD.params.spatial_filter_range = [app.spatial_filter_range1.Value, app.spatial_filter_range2.Value];
    HD.params.spatial_transformation = app.spatial_transformation.Value;
    HD.params.spatial_propagation = app.spatial_propagation.Value;

    % SVD parameters
    HD.params.svd_filter = app.svd_filter.Value;
    HD.params.svdx_filter = app.svdx_filter.Value;
    HD.params.svd_threshold = app.svd_threshold.Value;

    % Time transformation parameters
    HD.params.time_transform = app.time_transform.Value;
    HD.params.time_range = [app.time_range1.Value, app.time_range2.Value];

    % Flatfield correction
    HD.params.flatfield_gw = app.flatfield_gw.Value;

    % Show image type
    HD.params.image_types{1} = app.show_image_type.Value;

end
