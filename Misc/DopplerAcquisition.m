classdef DopplerAcquisition
    properties
        numX      % number of pix horizontally
        numY      % number of pix vertically
        fs      % sampling frequency
        z       % reconstruction distance
        z_retina % reconstruction distance for retina
        z_iris  %reconstruction distance for iris
        lambda  % laser wavelength
        x_step  % horizontal distance between two pix
        y_step  % vertaical distance between two pix
    end
    methods
        % constructor
        function obj = DopplerAcquisition(numX, numY, fs, z, z_retina, z_iris, lambda, x_step, y_step)
            obj.numX = numX;
            obj.numY = numY;
            obj.fs = fs;
            obj.z = z;
            obj.z_retina = z_retina;
            obj.z_iris = z_iris;
            obj.lambda = lambda;
            obj.x_step = x_step;
            obj.y_step = y_step;
        end
    end
end