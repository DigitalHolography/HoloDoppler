function J = autofocus_objective_fn(z,frame_batch, f1, f2, acquisition, gaussian_width, mask, use_gpu)
moment = reconstruct_from_batch(frame_batch, f1, f2, acquisition, z, gaussian_width, use_gpu);
moment = mat2gray(abs(ifft2(fft2(moment) .* fftshift(mask))));
J = gather(entropy(moment));
end