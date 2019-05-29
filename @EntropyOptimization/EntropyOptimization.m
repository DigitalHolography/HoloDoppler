classdef EntropyOptimization
    properties
        f1
        f2
        n
        m
        min_constraint
        max_constraint
        initial_guess
        mask_radiuses
    end
    methods
        % constructor
        function obj = EntropyOptimization(f1, f2, n, m, min_constraint, ...
                                           max_constraint, initial_guess, ...
                                           mask_radiuses)
            obj.f1 = f1;
            obj.f2 = f2;
            obj.n = n;
            obj.m = m;
            obj.min_constraint = min_constraint;
            obj.max_constraint = max_constraint;
            obj.initial_guess = initial_guess;
            obj.mask_radiuses = mask_radiuses;
        end
        
        opt = optimize(obj, FH, f1, f2, acquisition, gaussian_width, retract, use_gpu)
    end
end