function history = runfmincon(x0,objfun,amin,amax)

% Set up shared variables with OUTFUN
history.x = [];
history.fval = [];

% call optimization
% x0 = c0;% coeffs zernike
problem = createOptimProblem('fmincon','x0',x0,'objective',objfun,'lb',amin,'ub',amax);
problem.options.Algorithm = 'interior-point';
problem.options.CheckGradients = false;
problem.options.ConstraintTolerance = 1.0000e-01;
problem.options.Display = 'final';
problem.options.FiniteDifferenceType = 'forward';
problem.options.HessianApproximation = 'bfgs';
problem.options.HessianFcn = [];
problem.options.HessianMultiplyFcn = [];
problem.options.Display = 'iter';
problem.options.MaxFunctionEvaluations = 100;
problem.options.MaxIterations = 30;
problem.options.ObjectiveLimit = -1.0000e+20;
problem.options.OptimalityTolerance = 0.4e-01;
problem.options.OutputFcn = [@outfun];
problem.options.PlotFcn = {@optimplotx,@optimplotfval,@optimplotfirstorderopt};
problem.options.SpecifyConstraintGradient = false;
problem.options.SpecifyObjectiveGradient = false;
problem.options.StepTolerance = 2e-1;
problem.options.SubproblemAlgorithm = 'factorization';
problem.options.UseParallel = 0;

[x,fval,eflag,output] = fmincon(problem); 

function stop = outfun(x,optimValues,state)
     stop = false;
     switch state
         case 'init'
             hold on
         case 'iter'
         % Concatenate current point and objective function
         % value with history. x must be a row vector.
           history.fval = [history.fval; optimValues.fval];
           history.x = [history.x; x];
         % Concatenate current search direction with 
         % searchdir.
         % Label points with iteration number and add title.
         % Add .15 to x(1) to separate label from plotted 'o'
         case 'done'
             hold off
         otherwise
     end
end

end