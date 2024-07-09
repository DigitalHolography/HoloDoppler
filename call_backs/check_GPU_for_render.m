function GPUpreview = check_GPU_for_render(app,parfor_arg)
GPUpreview = true; % by default
% FIXME: handle and select best GPU if many available
gpuDevice(1);
available_mem = gpuDevice(1).AvailableMemory;
% FIXME: find or make single/double precision flag
predicted_FH_size = size(app.frame_batch, 1) * size(app.frame_batch, 2) * size(app.frame_batch, 3) * 8 * parfor_arg; % in bytes with single complex FH

if predicted_FH_size > 0.5 * available_mem
    GPUpreview = false;
end
% FIXME : else : launch GPU cores for compute
% parpool
end

