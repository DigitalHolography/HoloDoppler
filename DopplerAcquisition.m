classdef DopplerAcquisition
    properties
        Nx      % number of pix horizontally
        Ny      % number of pix vertically
        fs      % sampling frequency
        z       % reconstruction distance
        z_retina % reconstruction distance for retina
        z_iris  %reconstruction distance for iris
        lambda  % laser wavelength
        delta_x % required x circshift
        delta_y % required y circshift
        x_step  % horizontal distance between two pix
        y_step  % vertaical distance between two pix
    end
    methods
        % constructor
        function obj = DopplerAcquisition(Nx, Ny, fs, z, z_retina, z_iris, lambda, delta_x, ...
                                          delta_y, x_step, y_step)
            obj.Nx = Nx;
            obj.Ny = Ny;
            obj.fs = fs;
            obj.z = z;
            obj.z_retina = z_retina;
            obj.z_iris = z_iris;
            obj.lambda = lambda;
            obj.delta_x = delta_x;
            obj.delta_y = delta_y;
            obj.x_step = x_step;
            obj.y_step = y_step;
        end
    end
end