function [new_constraint] = stretch_constraint(constraint, optimum, stretch_factor)
% Reduces constraints interval based on a found optimum.
% The current constraint interval is centered the the optimum and has its
% bounds reduced by the stretch factor.
%
% constraint: a 2xn array of min/max constraints as :
%  [a1_min a2_min ... an_min]
%  [a1_max a2_max ... an_max]
%
% optimum: an 1xn array containing the optimum (must be inside the constraints)
%
% stretch_factor: a value between 0 and 1 indicating by how much the
% constraint will be stretched

offsets = (constraint(1, :) + constraint(2, :)) / 2;
% shift intervals to center
new_constraint = constraint - offsets;
% stretch constraint
new_constraint = new_constraint * (1 - stretch_factor);
% shift intervals to be centered on new_optimum
new_constraint = new_constraint + optimum;
end