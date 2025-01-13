function GPUpreview = check_GPU(app, parfor_arg)

arguments
    app
    parfor_arg = 6
end
GPUpreview = true; % by default
% FIXME: handle and select best GPU if many available
gpuDevice(1);
available_mem = gpuDevice(1).AvailableMemory;
% FIXME: find or make single/double precision flag

predicted_FH_size = app.numX * app.numY * app.batchsizeEditField.Value * 8 * parfor_arg; % 8/16 for single/double complex scalars and 6 is empiral measurement
% FIXME: 0.7
if predicted_FH_size > 0.9 * available_mem
    GPUpreview = false;
end

% FIXME : else : launch GPU cores for compute
% parpool
end
