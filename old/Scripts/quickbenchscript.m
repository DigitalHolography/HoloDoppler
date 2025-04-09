HR = HoloReader("X:\240828_FIY0713\240828_FIY0713_od.holo");
frame_batch = HR.read_frame_batch(512,0);
kernel = propagation_kernelFresnel(HR.frame_width, HR.frame_height, double(HR.footer.compute_settings.image_rendering.propagation_distance), double(HR.footer.compute_settings.image_rendering.lambda), double(HR.footer.info.pixel_pitch.x) * 1e-6, double(HR.footer.info.pixel_pitch.x) * 1e-6, 0);
tic,ri(frame_batch,'Fresnel',kernel,1,0,0,0,0);toc; %1.0s
tic,rifsf(frame_batch,kernel,50);toc;%0.70s
frame_batch_gpu = gpuArray(frame_batch);
kernel_gpu = gpuArray(kernel);
tic,rifsf(frame_batch_gpu,kernel_gpu,50);toc;% first time 1.17s next 0.4s