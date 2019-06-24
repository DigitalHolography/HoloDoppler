function z_opt = autofocus(frame_batch, f1, f2, acquisition, z0, mask, gaussian_width, use_gpu)
algo_options = optimoptions(@patternsearch, 'Display', 'iter');
algo_options.MeshTolerance = 1e-2;
algo_options.Cache = 'on';
obj_fn = @(z)autofocus_objective_fn(z,frame_batch, f1, f2, acquisition, gaussian_width, mask, use_gpu);

[z_opt, ~] = patternsearch(obj_fn, z0, [], [], [], [], 0.10, 0.40, [], algo_options); 
end