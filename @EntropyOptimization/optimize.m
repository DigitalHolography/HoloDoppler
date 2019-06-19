function opt = optimize(obj, FH, f1, f2, acquisition, gaussian_width, retract, use_gpu)
zernike_eval = evaluate_zernikes(obj.n, obj.m, acquisition.Nx, acquisition.Ny);
current_optimum = obj.initial_guess;
current_constraint = [obj.min_constraint; obj.max_constraint];
for r = obj.mask_radiuses
    mask = construct_mask(0, r, acquisition.Nx, acquisition.Ny);
    objective_fn = @(coefs)objective2(FH, coefs, zernike_eval, f1, f2, mask, acquisition, gaussian_width, use_gpu);
    
    algo_options = optimoptions(@patternsearch, 'Display', 'iter');
    algo_options.MeshTolerance = 1e-2;
    algo_options.Cache = 'on';
%     algo_options.PlotFcn('psplotmeshsize');
%     algo_options.PollMethod = 'GPSPositiveBasisNp1';
    [current_optimum, ~] = patternsearch(objective_fn, obj.initial_guess, [], [], [], [], current_constraint(1,:), current_constraint(2,:), algo_options); 

%     algo_options = optimoptions('surrogateopt', 'Display', 'iter', 'MaxFunctionEvaluations', 20);
%     [current_optimum, ~] = surrogateopt(objective_fn, current_constraint(1,:), current_constraint(2,:), algo_options);
    current_constraint = stretch_constraint(current_constraint, current_optimum, retract);
end

opt = current_optimum;
end