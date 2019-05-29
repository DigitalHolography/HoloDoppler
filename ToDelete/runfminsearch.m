function [optim history] = runfminsearch(c0,objfun,amin,amax)

global M0Corrected M0Aberrated
% Set up shared variables with OUTFUN
history.x = [];
history.fval = [];
% call optimization
%option_p = optimoptions(options,'UseParallel',true);
%xsol = fmincon(@expensive_objfun,startPoint,[],[],[],[],[],[],@expensive_confun,option_p);
options = optimset('PlotFcns',{@optimplotx,@optimplotfval});
options.Display = 'iter';
options.MaxFunctionEvals = 30;%100
options.TolX = 1.5e-4;%1e-4;
options.TolFun = 1.5e-4;%1e-4;
options.OutputFcn = [{@outfun,@plotcorrection}];
options.UseParallel = true;

[optim,fval,eflag,output] = fminsearch(objfun,c0,options);
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
    function stop = plotcorrection(x,optimValues,state)
        global corr
        stop = false;
        switch state
            case 'init'
                figure(1)
                subplot(1,2,1)
                aberr = imshow(mat2gray(M0Aberrated));
                subplot(1,2,2)
                corr = imshow(mat2gray(M0Corrected));
            case 'iter'
                corr.CData = mat2gray(M0Corrected);
            case 'done'
            otherwise
        end
    end

end % runfminsearch