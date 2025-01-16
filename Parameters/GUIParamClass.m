classdef GUIParamClass
    %GUIParameters Summary of this class goes here
    %   Detailed explanation goes here

    properties
        param
    end

    methods
        function obj = GUIParamClass()
        end

        function obj = setParametersJSON(obj, jsonPath)
            if exist(jsonPath, 'file')
                jsonData = fileread(jsonPath);
                obj.param = jsondecode(jsonData);
            else
                error('The json file could not be found.');
            end
        end

        function obj = setParametersGUI(obj, app)
            % Parallel Parameters
            obj.param.Parallel.NbCPUCores = app.numworkersSpinner.Value;
            obj.param.Parallel.Parallelism = app.ParallelismDropDown.Value;

            % Holographic Propagation Parameters
            obj.param.Propagation.Transform = app.spatialTransformationDropDown.Value;
            obj.param.Propagation.z_retina = app.zretinaEditField.Value;
            obj.param.Propagation.z_iris = app.zirisEditField.Value;
            obj.param.Propagation.flagRetinal = app.Switch.Value;

            % Spatial Filters Parameters
            obj.param.Spatial.gaussian_blur = app.blurEditField.Value;
            obj.param.Spatial.low_pass = app.spatialfilterratio.Value;
            obj.param.Spatial.high_pass = app.spatialfilterratiohigh.Value;

            % Temporal Transforms Parameters
            obj.param.Temporal.Transform = app.time_transform.Value;
            obj.param.Temporal.batch_size = app.batchsizeEditField.Value;
            obj.param.Temporal.f_low = app.f1EditField.Value;
            obj.param.Temporal.f_high = app.f2EditField.Value;
            obj.param.Temporal.PCA_min = app.spatialfilterratiohigh.Value;
            obj.param.Temporal.PCA_max = app.spatialfilterratiohigh.Value;

            % Advanced Parameters
            obj.param.Advanced.flagSVD = app.SVDCheckBox.Value;
            obj.param.Advanced.flagSVDx = app.SVDxCheckBox.Value;
            obj.param.Advanced.SVDx_SubAp_num = app.SVDx_SubApEditField.Value;
            obj.param.Advanced.flagSVDThreshold = app.SVDThresholdCheckBox.Value;
            obj.param.Advanced.SVDThresholdValue = app.SVDThresholdEditField.Value;
            obj.param.Advanced.SVDStride = app.SVDStrideEditField.Value;

            % Registration Parameters
            obj.param.Registration.flagRegistration = app.ImageRegistrationCheckBox.Value;
            obj.param.Registration.refBatchSize = app.refbatchsizeEditField.Value;
            obj.param.Registration.refPosition = app.positioninfileSlider.Value;
            obj.param.Registration.flagRegistrationDisk = app.registrationdiskratioCheckBox.Value;
            obj.param.Registration.registrationDiskRatio = app.regDiskRatioEditField.Value;
            obj.param.Registration.flagRephasing = app.UseRephasingDataCheckBox.Value;
            obj.param.Registration.flagPhase = app.PhaseRegistrationCheckBox.Value;
            obj.param.Registration.flagIterative = app.IterativeRegistrationCheckBox.Value;

            % Video Parameters
            obj.param.Video.Choice = (strrep(app.OutputVideoDropDown.Value, ' ', '_'));
            obj.param.Video.batch_stride = app.batchstrideEditField.Value;
            obj.param.Video.flagTemporalFilter = app.temporalfilterEditField.Value;
            obj.param.Video.temporalFilter = app.f2EditField.Value;

            % Images Parameters
            obj.param.Images.Choice = strrep(app.ImageChoiceDropDown.Value, ' ', '_');
            obj.param.Images.color_f1 = app.compositef1EditField.Value;
            obj.param.Images.color_f2 = app.compositef2EditField.Value;
            obj.param.Images.color_f3 = app.compositef3EditField.Value;

            % Compensation Parameters
            obj.param.Compensation.flagShackHartmann = app.ShackHartmannCheckBox.Value;
            obj.param.Compensation.flagZernike = app.ZernikeProjectionCheckBox.Value;
            obj.param.Compensation.flagSubApPCA = app.SubAp_PCACheckBox.Value;

            % Iterative Optimization Parameters
            obj.param.IterativeOpti.flagIterative_aberration_compensation = app.IterativeoptimizationCheckBox.Value;
            obj.param.IterativeOpti.optimization_zernike_ranks = app.optimizationzernikeranksEditField.Value;
            obj.param.IterativeOpti.mask_num_iter = app.masknumiterEditField.Value;
            obj.param.IterativeOpti.zernikes_tol = app.zernikestolEditField.Value;
            obj.param.IterativeOpti.max_constraint = app.maxconstraintEditField.Value;

            % Shack Hartmann Parameters
            obj.param.ShackHartmann.shack_hartmann_zernike_ranks = app.optimizationzernikeranksEditField.Value;
            obj.param.ShackHartmann.image_subapertures_size_ratio = app.subaperturesizeratioEditField.Value;
            obj.param.ShackHartmann.num_subapertures_positions = app.numsubaperturespositionsEditField.Value;
            obj.param.ShackHartmann.subaperture_margin = app.subaperturemarginEditField.Value;
            obj.param.ShackHartmann.minSubAp_PCA = app.minsubapPCAEditField.Value;
            obj.param.ShackHartmann.maxSubAp_PCA = app.maxsubapPCAEditField.Value;
            obj.param.ShackHartmann.shack_hartmann_ref_image = app.shackHartmannRefImageDropDown.Value;

            % Dark Field Parameters
            obj.param.DarkField.xystride = app.xystrideEditField.Value;
            obj.param.DarkField.num_unit_cells_x = app.unitcellsinlatticeEditField.Value;
            obj.param.DarkField.r1 = app.r1EditField.Value;
        end

        function obj = updateGUIFromJSON(obj, app, jsonPath)
            % This method will read parameters from the provided JSON file and update the GUI
            jsonClass = GUIParamClass();
            jsonClass = jsonClass.setParametersJSON(obj, jsonPath);
            jsonClass.updateGUI(app);
        end

        function obj = updateGUI(obj, app)
            % This method will update the GUI components based on the current class parameters (obj.param)

            % Update GUI components with the values from obj.param
            app.numworkersSpinner.Value = obj.param.Parallel.NbCPUCores;
            app.ParallelismDropDown.Value = obj.param.Parallel.Parallelism;
            app.spatialTransformationDropDown.Value = obj.param.Propagation.Transform;
            app.zretinaEditField.Value = obj.param.Propagation.z_retina;
            app.zirisEditField.Value = obj.param.Propagation.z_iris;
            app.Switch.Value = obj.param.Propagation.flagRetinal;

            app.blurEditField.Value = obj.param.Spatial.gaussian_blur;
            app.spatialfilterratio.Value = obj.param.Spatial.low_pass;
            app.spatialfilterratiohigh.Value = obj.param.Spatial.high_pass;

            app.time_transform.Value = obj.param.Temporal.Transform;
            app.batchsizeEditField.Value = obj.param.Temporal.batch_size;
            app.f1EditField.Value = obj.param.Temporal.f_low;
            app.f2EditField.Value = obj.param.Temporal.f_high;
            app.spatialfilterratiohigh.Value = obj.param.Temporal.PCA_min;
            app.spatialfilterratiohigh.Value = obj.param.Temporal.PCA_max;

            app.SVDCheckBox.Value = obj.param.Advanced.flagSVD;
            app.SVDxCheckBox.Value = obj.param.Advanced.flagSVDx;
            app.SVDx_SubApEditField.Value = obj.param.Advanced.SVDx_SubAp_num;
            app.SVDThresholdCheckBox.Value = obj.param.Advanced.flagSVDThreshold;
            app.SVDThresholdEditField.Value = obj.param.Advanced.SVDThresholdValue;
            app.SVDStrideEditField.Value = obj.param.Advanced.SVDStride;

            app.ImageRegistrationCheckBox.Value = obj.param.Registration.flagRegistration;
            app.refbatchsizeEditField.Value = obj.param.Registration.refBatchSize;
            app.positioninfileSlider.Value = obj.param.Registration.refPosition;
            app.registrationdiskratioCheckBox.Value = obj.param.Registration.flagRegistrationDisk;
            app.regDiskRatioEditField.Value = obj.param.Registration.registrationDiskRatio;
            app.UseRephasingDataCheckBox.Value = obj.param.Registration.flagRephasing;
            app.PhaseRegistrationCheckBox.Value = obj.param.Registration.flagPhase;
            app.IterativeRegistrationCheckBox.Value = obj.param.Registration.flagIterative;

            app.OutputVideoDropDown.Value = strrep(obj.param.Video.Choice, '_', ' ');
            app.batchstrideEditField.Value = obj.param.Video.batch_stride;
            app.temporalfilterEditField.Value = obj.param.Video.flagTemporalFilter;
            app.f2EditField.Value = obj.param.Video.temporalFilter;

            app.ImageChoiceDropDown.Value = strrep(obj.param.Images.Choice, '_', ' ');
            app.compositef1EditField.Value = obj.param.Images.color_f1;
            app.compositef2EditField.Value = obj.param.Images.color_f2;
            app.compositef3EditField.Value = obj.param.Images.color_f3;

            app.ShackHartmannCheckBox.Value = obj.param.Compensation.flagShackHartmann;
            app.ZernikeProjectionCheckBox.Value = obj.param.Compensation.flagZernike;
            app.SubAp_PCACheckBox.Value = obj.param.Compensation.flagSubApPCA;

            app.IterativeoptimizationCheckBox.Value = obj.param.IterativeOpti.flagIterative_aberration_compensation;
            app.optimizationzernikeranksEditField.Value = obj.param.IterativeOpti.optimization_zernike_ranks;
            app.masknumiterEditField.Value = obj.param.IterativeOpti.mask_num_iter;
            app.zernikestolEditField.Value = obj.param.IterativeOpti.zernikes_tol;
            app.maxconstraintEditField.Value = obj.param.IterativeOpti.max_constraint;

            app.xystrideEditField.Value = obj.param.DarkField.xystride;
            app.unitcellsinlatticeEditField.Value = obj.param.DarkField.num_unit_cells_x;
            app.r1EditField.Value = obj.param.DarkField.r1;
        end

    end
end
