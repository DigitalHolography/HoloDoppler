function [] = plot_objective(objective_fn, dim, param1, param2, x_min, x_max, num_points)
% Creates a 1D plot of objective_fn while keeping constant parameters.
% objective_fn takes a 3 elements array as parameter (e.g. objective_fn([x1, x2, x3]))
% since objective_fn is very slow to evaluate, plotting a surface would
% take too long. This function plots alongside the axis specified by the
% `dim` parameter, the other cosntant parameters are specified with the
% `param1` and `param2` input.
%
% objective_fn: a function f: (x1, x2, x3) -> f(x1, x2, x3) to plot
%
% dim: the dimension alongside which the plot is performed, e.g. dim=2
% will plot the function x2 -> f(x1, x2, x3)
%
% param1, param2: the constant values of the other parameters (from left to
% right, e.g. if dim=2, param1 is x1 and param2 is x3)
%
% x_min, x_max: the bounds of the free variable
%
% num_points: number of points of the plot (important is the function is slow to evaluate)

X = linspace(x_min, x_max, num_points);
switch dim
    case 1
        objective_fn_1d = @(x)objective_fn([x, param1, param2]);
    case 2
        objective_fn_1d = @(x)objective_fn([param1, x, param2]);
    case 3
        objective_fn_1d = @(x)objective_fn([param1, param2, x]);
    otherwise
        error('wrong dim value')
end

Y = X;
for i = 1:size(X, 2)
    Y(i) = objective_fn_1d(X(i));
end
plot(X, Y)
title(sprintf('objective function with dim %d free, param1=%f param2=%f', dim, param1, param2))
end