classdef GuiCache
% A parameter cache to store parameters from GUI
% so that during computations, values are fetched from cache instead of GUI
% so that the user can modify the values in the GUI without messing
% everything up
properties (Access = public)

    nb_cpu_cores
    batch_size
    ref_batch_size
    batch_stride
    spatialTransformation
    z
    z_retina
    z_iris
    z_switch
    time_transform  % object with : type of transformation, f1, f2
    blur
    imageChoice
    wavelength
    Fs
    pix_width
    pix_height
    registration
    temporal_filter_flag
    temporal_filter
    parallelism
    
    registration_via_phase
    iterative_registration
    aberration_compensation
    notes
    DX
    DY
    position_in_file
    output_videos
    low_memory
    rephasing
    OCTdata
    SVD
    save_raw
    
    % color image parameters
    color_f1
    color_f2
    color_f3
    low_frequency

    % dark field parameters
    xystride
    num_unit_cells_x
    r1
    
    % iterative optimization parameters
    iterative_aberration_compensation
    optimization_zernike_ranks
    mask_num_iter
    zernikes_tol
    max_constraint
    
    % shack-hartmann parameters
    shack_hartmann_aberration_compensation
    shack_hartmann_zernike_ranks
    image_subapertures_size_ratio
    num_subapertures_positions
    subaperture_margin
    SubAp_PCA;
    minSubAp_PCA;
    maxSubAp_PCA;
    zernike_projection;
    shack_hartmann_ref_image

    %masks
    artery_mask;

    % OCT parameters
    OCT_range_y
    OCT_range_z
end
methods (Access = public)
    function obj = GuiCache(app)
        obj.nb_cpu_cores = app.numworkersSpinner.Value;
            obj.batch_size = app.batchsizeEditField.Value;
            obj.ref_batch_size = app.refbatchsizeEditField.Value;
            obj.batch_stride = app.batchstrideEditField.Value;
            obj.spatialTransformation = app.spatialTransformationDropDown.Value;% Fresnel or angular spectrum...&obj.
            obj.z_switch = app.Switch.Value;
            obj.z_retina = app.zretinaEditField.Value;
            obj.z_iris = app.zirisEditField.Value;
            obj.time_transform = app.time_transform;
            obj.blur = app.blurEditField.Value;
            obj.imageChoice = strrep(app.ImageChoiceDropDown.Value, ' ', '_');
            obj.wavelength = app.wavelengthEditField.Value;
            obj.Fs = app.Fs;
            obj.pix_width = app.pix_width;
            obj.pix_height = app.pix_height;
            obj.registration = app.imageregistrationCheckBox.Value;
            obj.temporal_filter_flag = app.temporalfilterCheckBox.Value;
            obj.temporal_filter = app.temporalfilterEditField.Value;
            obj.parallelism = app.ParallelismDropDown.Value;
            obj.registration_via_phase = app.phaseregistrationCheckBox.Value;
            obj.aberration_compensation = app.IterativeoptimizationCheckBox.Value;
            obj.OCTdata = app.OCTdata;
            obj.SVD = app.SVDCheckBox.Value;

            obj.notes = app.NotesTextArea.Value;
            obj.DX = app.DX;
            obj.DY = app.DY;
            obj.position_in_file = app.positioninfileSlider.Value;
            obj.output_videos = (strrep(app.outputvideoDropDown.Value, ' ', '_'));
            obj.low_memory = app.lowmemoryCheckBox.Value;
            obj.rephasing = app.rephasingCheckBox.Value;
            obj.save_raw = app.saverawvideosCheckBox.Value;

            obj.color_f1 = app.compositef1EditField.Value;
            obj.color_f2 = app.compositef2EditField.Value;
            obj.color_f3 = app.compositef3EditField.Value;
            obj.low_frequency = app.lowfrequencyCheckBox.Value;

            % dark field parameters
            obj.xystride = app.xystrideEditField.Value;
            obj.num_unit_cells_x = app.unitcellsinlatticeEditField.Value;
            obj.r1 = app.r1EditField.Value;

            % iterative optimization parameters
            obj.iterative_aberration_compensation = app.IterativeoptimizationCheckBox.Value;
            obj.optimization_zernike_ranks = app.optimizationzernikeranksEditField.Value;
            obj.mask_num_iter = app.masknumiterEditField.Value;
            obj.zernikes_tol = app.zernikestolEditField.Value;
            obj.max_constraint = app.maxconstraintEditField.Value;
            obj.iterative_registration = app.iterativeregistrationCheckBox.Value;

            % shack-hartmann parameters
            obj.shack_hartmann_aberration_compensation = app.ShackHartmannCheckBox.Value;
            obj.shack_hartmann_zernike_ranks = app.shackhartmannzernikeranksEditField.Value;
            obj.image_subapertures_size_ratio = app.imagesubapsizeratioEditField.Value;
            obj.num_subapertures_positions = app.subapnumpositionsEditField.Value;
            obj.subaperture_margin = app.subaperturemarginEditField.Value;
            obj.SubAp_PCA = app.SubAp_PCACheckBox.Value;
            obj.minSubAp_PCA = app.minSubAp_PCAEditField_2.Value;
            obj.maxSubAp_PCA = app.maxSubAp_PCAEditField_2.Value;
            obj.zernike_projection = app.ZernikeProjectionCheckBox.Value;
            obj.shack_hartmann_ref_image = app.referenceimageDropDown.Value;

            % OCT parameters
            obj.OCT_range_y = app.OCTdata.range_y;
            obj.OCT_range_z = app.OCTdata.range_z;
    end
end
end