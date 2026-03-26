classdef GuiCache
% A parameter cache to store parameters from GUI
% so that during computations, values are fetched from cache instead of GUI
% so that the user can modify the values in the GUI without messing
% everything up
properties (Access = public)

    nb_cpu_cores double
    batchSize double
    spatialTransformation char
    z double
    z_retina double
    z_iris double
    z_switch char
    time_transform struct % object with : type of transformation, f1, f2
    blur double
    imageChoice char
    wavelength double
    Fs double
    pix_width double
    pix_height double
    parallelism char

    aberration_compensation logical
    notes cell
    position_in_file double
    output_videos char
    SVD logical

    % video rendering

    ref_batch_size double
    batchStride double
    DX double
    DY double

    % video rendering logical checkboxes
    save_raw logical
    rephasing logical
    registration logical
    registration_via_phase logical
    iterative_registration logical
    temporalFilter_flag logical
    temporalFilter double
    registration_disc logical
    registration_disc_ratio double

    % color image parameters
    color_f1 double
    color_f2 double
    color_f3 double

    % dark field parameters
    xystride double
    num_unit_cells_x double
    r1 double

    % iterative optimization parameters
    iterative_aberration_compensation double
    optimization_zernike_ranks double
    mask_num_iter double
    zernikes_tol double
    max_constraint double

    % shack-hartmann parameters
    shack_hartmann_aberration_compensation double
    shack_hartmann_zernike_ranks double
    image_subapertures_size_ratio double
    num_subapertures_positions double
    subaperture_margin double
    SubAp_PCA double
    minSubAp_PCA double
    maxSubAp_PCA double
    zernike_projection double
    shack_hartmann_ref_image double

    num_Freq double
    SVD_Stride double
    isSVD_Stride logical

end

methods (Access = public)

    function obj = GuiCache(app)
        obj.nb_cpu_cores = app.numworkersSpinner.Value;
        obj.batchSize = app.batchsize.Value;
        obj.ref_batch_size = app.refbatchsize.Value;
        obj.batchStride = app.batchstride.Value;
        obj.spatialTransformation = app.spatialTransformationDropDown.Value; % Fresnel or angular spectrum...&obj.
        obj.z_switch = app.Switch.Value;
        obj.z_retina = app.zretina.Value;
        obj.z_iris = app.ziris.Value;
        obj.time_transform = app.time_transform;
        obj.blur = app.blur.Value;
        obj.imageChoice = strrep(app.ImageChoiceDropDown.Value, ' ', '_');
        obj.wavelength = app.wavelength.Value;
        obj.Fs = app.Fs;
        obj.pix_width = app.pix_width;
        obj.pix_height = app.pix_height;
        obj.registration = app.imageregistrationCheckBox.Value;
        obj.temporalFilter = app.temporalfilter.Value;
        obj.parallelism = app.ParallelismDropDown.Value;
        obj.registration_via_phase = app.phaseregistrationCheckBox.Value;
        obj.aberration_compensation = app.IterativeoptimizationCheckBox.Value;
        obj.SVD = app.SVDCheckBox.Value;

        obj.notes = app.NotesTextArea.Value;
        obj.DX = app.DX;
        obj.DY = app.DY;
        obj.position_in_file = app.positioninfileSlider.Value;
        obj.output_videos = (strrep(app.outputvideoDropDown.Value, ' ', '_'));
        obj.rephasing = app.rephasingCheckBox.Value;
        obj.registration_disc = app.registrationdiscCheckBox.Value;
        obj.registration_disc_ratio = app.regDiscRatio.Value;

        obj.color_f1 = app.compositef1.Value;
        obj.color_f2 = app.compositef2.Value;
        obj.color_f3 = app.compositef3.Value;

        % dark field parameters
        obj.xystride = app.xystride.Value;
        obj.num_unit_cells_x = app.unitcellsinlattice.Value;
        obj.r1 = app.r1.Value;

        % iterative optimization parameters
        obj.iterative_aberration_compensation = app.IterativeoptimizationCheckBox.Value;
        obj.optimization_zernike_ranks = app.optimizationzernikeranks.Value;
        obj.mask_num_iter = app.masknumiter.Value;
        obj.zernikes_tol = app.zernikestol.Value;
        obj.max_constraint = app.maxconstraint.Value;
        obj.iterative_registration = app.iterativeregistrationCheckBox.Value;

        % shack-hartmann parameters
        obj.shack_hartmann_aberration_compensation = app.ShackHartmannCheckBox.Value;
        obj.shack_hartmann_zernike_ranks = app.shackhartmannzernikeranks.Value;
        obj.image_subapertures_size_ratio = app.imagesubapsizeratio.Value;
        obj.num_subapertures_positions = app.subapnumpositions.Value;
        obj.subaperture_margin = app.subaperturemargin.Value;
        obj.SubAp_PCA = app.SubAp_PCACheckBox.Value;
        obj.minSubAp_PCA = app.minSubAp_PCA.Value;
        obj.maxSubAp_PCA = app.maxSubAp_PCA.Value;
        obj.zernike_projection = app.ZernikeProjectionCheckBox.Value;
        obj.shack_hartmann_ref_image = app.referenceimageDropDown.Value;

        obj.num_Freq = app.numFreq.Value;
        obj.SVD_Stride = app.SVDStride.Value;
        obj.isSVD_Stride = app.SVDThresholdCheckBox.Value;

        % bufferize (and lock during computation) current paremeter values from front end
    end

    function load2Gui(obj, app)
        % set gui parameters from cache
        try
            app.ppx.Value = loadGUIVariable(obj.pix_width);
            app.ppy.Value = loadGUIVariable(obj.pix_height);
            app.batchsize.Value = loadGUIVariable(obj.batchSize);
            app.max_PCA.Limits = loadGUIVariable([0 double(app.batchsize.Value)]);
            app.spatialTransformationDropDown.Value = loadGUIVariable(obj.spatialTransformation);
            app.refbatchsize.Value = loadGUIVariable(obj.ref_batch_size);
            app.batchstride.Value = loadGUIVariable(obj.batchStride);
            app.Switch.Value = loadGUIVariable(obj.z_switch);
            app.zretina.Value = loadGUIVariable(obj.z_retina);
            app.ziris.Value = loadGUIVariable(obj.z_iris);
            app.time_transform = loadGUIVariable(obj.time_transform);
            app.blur.Value = loadGUIVariable(obj.blur);
            app.ImageChoiceDropDown.Value = loadGUIVariable(strrep(obj.imageChoice, '_', ' '));
            app.timetransformDropDown.Value = loadGUIVariable(obj.time_transform.type);
            app.SVDCheckBox.Value = loadGUIVariable(obj.SVD);
            app.f1.Value = loadGUIVariable(obj.time_transform.f1);
            app.f2.Value = loadGUIVariable(obj.time_transform.f2);
            app.min_PCA.Value = loadGUIVariable(obj.time_transform.min_PCA);
            app.max_PCA.Value = loadGUIVariable(obj.time_transform.max_PCA);
            app.imageregistrationCheckBox.Value = loadGUIVariable(obj.registration);
            app.iterativeregistrationCheckBox.Value = loadGUIVariable(obj.iterative_registration);
            app.wavelength.Value = loadGUIVariable(obj.wavelength);
            app.outputvideoDropDown.Value = loadGUIVariable(strrep(obj.output_videos, '_', ' '));
            app.rephasingCheckBox.Value = loadGUIVariable(obj.rephasing);
            app.NotesTextArea.Value = loadGUIVariable(obj.notes);
            app.positioninfileSlider.Value = loadGUIVariable(obj.position_in_file);
            app.IterativeoptimizationCheckBox.Value = loadGUIVariable(obj.iterative_aberration_compensation);
            app.masknumiter.Value = loadGUIVariable(obj.mask_num_iter);
            app.ShackHartmannCheckBox.Value = loadGUIVariable(obj.shack_hartmann_aberration_compensation);
            app.ZernikeProjectionCheckBox.Value = loadGUIVariable(obj.zernike_projection);
            app.referenceimageDropDown.Value = loadGUIVariable(obj.shack_hartmann_ref_image);
            app.shackhartmannzernikeranks.Value = loadGUIVariable(obj.shack_hartmann_zernike_ranks);
            app.imagesubapsizeratio.Value = loadGUIVariable(obj.image_subapertures_size_ratio);
            app.subapnumpositions.Value = loadGUIVariable(obj.num_subapertures_positions);
            app.subaperturemargin.Value = loadGUIVariable(obj.subaperture_margin);
            app.SubAp_PCACheckBox.Value = loadGUIVariable(obj.SubAp_PCA);
            app.minSubAp_PCA.Value = loadGUIVariable(obj.minSubAp_PCA);
            app.maxSubAp_PCA.Value = loadGUIVariable(obj.maxSubAp_PCA);
            app.compositef1.Value = loadGUIVariable(obj.color_f1);
            app.compositef2.Value = loadGUIVariable(obj.color_f2);
            app.compositef3.Value = loadGUIVariable(obj.color_f3);
            app.saverawvideosCheckBox.Value = loadGUIVariable(obj.save_raw);
            app.numFreq.Value = loadGUIVariable(obj.num_Freq);
            app.SVDStride.Value = loadGUIVariable(obj.SVD_Stride);
            app.SVDThresholdCheckBox.Value = loadGUIVariable(obj.isSVD_Stride);

        catch ME
            MEdisp(ME);
            fprintf('Error loading parameters from cache to GUI: %s\n', ME.message);
        end

    end

end

end
