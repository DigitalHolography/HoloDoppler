function opt = optimize(obj, FH, f1, f2, acquisition, gaussian_width, mesh_tol, mask_num_iter, retract, use_gpu)
[~, zernike_eval] = zernike_phase(obj.p, acquisition.Nx, acquisition.Ny);
current_optimum = obj.initial_guess;
current_constraint = [obj.min_constraint; obj.max_constraint];
mask_radiuses = floor(((0:mask_num_iter-1) .* (35 * 0.50)) + 35);
for r = mask_radiuses
    mask = construct_mask(0, r, acquisition.Nx, acquisition.Ny);
    objective_fn = @(coefs)objective(FH, coefs, zernike_eval, f1, f2, mask, acquisition, gaussian_width, use_gpu);
    
%     algo_options = optimoptions(@patternsearch, 'Display', 'iter');
    algo_options = optimoptions(@patternsearch);
%     algo_options.MeshTolerance = 1e-2;
    algo_options.MeshTolerance = mesh_tol;
    algo_options.Cache = 'on';
%     algo_options.PlotFcn('psplotmeshsize');
    [current_optimum, ~] = patternsearch(objective_fn, obj.initial_guess, [], [], [], [], current_constraint(1,:), current_constraint(2,:), algo_options); 
    current_constraint = stretch_constraint(current_constraint, current_optimum, retract);
end

opt = current_optimum;
end