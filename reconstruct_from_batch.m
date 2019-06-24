function hologram = reconstruct_from_batch(frame_batch, f1, f2, ac, z, gaussian_width, use_gpu)
kernel = propagation_kernel(double(ac.Nx), double(ac.Ny), z, ac.lambda, ac.x_step, ac.y_step, false);
if use_gpu
    FH = gpuArray(fftshift(fft2(frame_batch)) .* kernel);
else
    FH = fftshift(fft2(frame_batch)) .* kernel;
end
hologram = reconstruct_hologram(FH, f1, f2, ac, gaussian_width, use_gpu);
end