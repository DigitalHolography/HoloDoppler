classdef GuiCache
    % A parameter cache to store parameters from GUI
    % so that during computations, values are fetched from cache instead of GUI
    % so that the user can modify the values in the GUI without messing
    % everything up
    properties (Access = public)

        z double
        wavelength double
        Fs double
        pix_width double
        pix_height double

        num_Freq double

    end

    methods (Access = public)

        function obj = GuiCache(app)

            obj.wavelength = app.wavelengthEditField.Value;
            obj.Fs = app.Fs;
            obj.pix_width = app.pix_width;
            obj.pix_height = app.pix_height;

            obj.num_Freq = app.numFreqEditField.Value;

            % bufferize (and lock during computation) current paremeter values from front end
        end

        function load2Gui(obj, app)
            % set gui parameters from cache
            try
            app.ppx.Value = loadGUIVariable(obj.pix_width);
            app.ppy.Value = loadGUIVariable(obj.pix_height);
            app.max_PCAEditField.Limits = loadGUIVariable([0 double(app.batchsizeEditField.Value)]);
            app.wavelengthEditField.Value = loadGUIVariable(obj.wavelength);
            app.numFreqEditField.Value = loadGUIVariable(obj.num_Freq);
            
            end

        end

    end

end
