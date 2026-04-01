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
    timeTransform struct % object with : type of transformation, f1, f2
    blur double
    imageChoice char
    wavelength double
    Fs double
    pix_width double
    pix_height double
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
    registrationDisk logical
    registrationDiskRatio double

    % color image parameters
    color_f1 double
    color_f2 double
    color_f3 double

    num_Freq double
    svdStride double

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
        obj.timeTransform = app.timeTransform;
        obj.blur = app.blur.Value;
        obj.imageChoice = strrep(app.ImageChoiceDropDown.Value, ' ', '_');
        obj.wavelength = app.wavelength.Value;
        obj.Fs = app.Fs;
        obj.pix_width = app.pix_width;
        obj.pix_height = app.pix_height;
        obj.registration = app.imageregistrationCheckBox.Value;
        obj.registration_via_phase = app.phaseregistrationCheckBox.Value;

        obj.DX = app.DX;
        obj.DY = app.DY;
        obj.position_in_file = app.positioninfileSlider.Value;
        obj.output_videos = (strrep(app.outputvideoDropDown.Value, ' ', '_'));
        obj.rephasing = app.rephasingCheckBox.Value;
        obj.registrationDisk = app.registrationdiskCheckBox.Value;
        obj.registrationDiskRatio = app.regDiscRatio.Value;

        obj.color_f1 = app.compositef1.Value;
        obj.color_f2 = app.compositef2.Value;
        obj.color_f3 = app.compositef3.Value;

        obj.num_Freq = app.numFreq.Value;
        obj.svdStride = app.svdStride.Value;

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
            app.timeTransform = loadGUIVariable(obj.timeTransform);
            app.blur.Value = loadGUIVariable(obj.blur);
            app.ImageChoiceDropDown.Value = loadGUIVariable(strrep(obj.imageChoice, '_', ' '));
            app.timetransformDropDown.Value = loadGUIVariable(obj.timeTransform.type);
            app.f1.Value = loadGUIVariable(obj.timeTransform.f1);
            app.f2.Value = loadGUIVariable(obj.timeTransform.f2);
            app.min_PCA.Value = loadGUIVariable(obj.timeTransform.min_PCA);
            app.max_PCA.Value = loadGUIVariable(obj.timeTransform.max_PCA);
            app.imageregistrationCheckBox.Value = loadGUIVariable(obj.registration);
            app.iterativeregistrationCheckBox.Value = loadGUIVariable(obj.iterative_registration);
            app.wavelength.Value = loadGUIVariable(obj.wavelength);
            app.outputvideoDropDown.Value = loadGUIVariable(strrep(obj.output_videos, '_', ' '));
            app.rephasingCheckBox.Value = loadGUIVariable(obj.rephasing);
            app.positioninfileSlider.Value = loadGUIVariable(obj.position_in_file);
            app.compositef1.Value = loadGUIVariable(obj.color_f1);
            app.compositef2.Value = loadGUIVariable(obj.color_f2);
            app.compositef3.Value = loadGUIVariable(obj.color_f3);
            app.saverawvideosCheckBox.Value = loadGUIVariable(obj.save_raw);
            app.numFreq.Value = loadGUIVariable(obj.num_Freq);
            app.svdStride.Value = loadGUIVariable(obj.svdStride);

        catch ME
            MEdisp(ME);
            fprintf('Error loading parameters from cache to GUI: %s\n', ME.message);
        end

    end

end

end
