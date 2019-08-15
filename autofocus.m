function z_opt = autofocus(frame_batch, f1, f2, acquisition, z0, mask, gaussian_width, use_gpu)
% Find an optimal reconstruction distance for a given interferogram stack
%
% frame_batch: a 3D frame stack from which the optimal z will be computed
% f1, f2: integration frequency bounds used for generating an image from
%         which the autofocus quality is assessed
% aqcuisition: a DopplerAcquisition struct containing data related to the
%              experimental setup
% z0: initial reconstruction distance guess
% mask: 2D spatial mask used for smoothin an image for the optimizer
% gaussian_width: size of the guassian filter

algo_options = optimoptions(@patternsearch, 'Display', 'iter');
algo_options.MeshTolerance = 1e-2;
algo_options.Cache = 'on';
obj_fn = @(z)autofocus_objective_fn(z,frame_batch, f1, f2, acquisition, gaussian_width, mask, use_gpu);

% we constrain z between 0.10 and 0.40. usually it will be around 0.22
[z_opt, ~] = patternsearch(obj_fn, z0, [], [], [], [], 0.10, 0.40, [], algo_options); 
end