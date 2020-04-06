function J = autofocus_objective_fn(z,frame_batch, f1, f2, acquisition, gaussian_width, mask, use_gpu)
% this is quite similar from the objective function used in objective.m
% except that we start from frame_batch instead of FH so we have to
% recompute FH each time this function is called
ac = acquisition;
kernel = propagation_kernel(ac.Nx, ac.Ny, z, ac.lambda, ac.x_step, ac.y_step, false);
FH = fftshift(fft2(frame_batch)) .* kernel;
moment = reconstruct_hologram(FH, f1, f2, acquisition, gaussian_width, use_gpu, true);
moment = mat2gray(abs(ifft2(fft2(moment) .* fftshift(mask))));
J = gather(entropy(moment) ./ norm(stdfilt(moment).^2));
end