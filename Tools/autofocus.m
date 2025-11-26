function z_opti = autofocus(rend,Params)
    f = waitbar(0, 'Autofocus in progress. Please wait...');

    cost = @(z) cost_function(rend,Params,z);

    % z0 = Params.spatial_propagation;

    zmin = 0.1;
    zmax = 1;

    options = optimset('TolX',1e-4,'Display','iter','OutputFcn',@(x,optimValues,state) waitbar_update(x,optimValues,state,f));

    z_opti = fminbnd(cost,zmin,zmax,options);

    close(f);
end

function stop = waitbar_update(x,optimValues,state,f)
    stop = false;
    if strcmp(state,'iter')
        waitbar(optimValues.iteration/50, f, sprintf('Autofocus iteration %d',optimValues.iteration));
    end
end

function img = renderM0(rend,Params,z)
    Params.spatial_propagation = z;
    rend.Render(Params, {"power_Doppler"}, cache_intermediate_results = false);
    img = rend.getImages({"power_Doppler"});
    img = img{1};
end

function c = cost_function(rend,Params,z)
    img = renderM0(rend,Params,z);
    Lx = abs(conv2(img, [1 -2 1], 'same'));
    Ly = abs(conv2(img, [1; -2; 1], 'same'));
    c = (mean(Lx(:)) + mean(Ly(:)));
    % c = entropy(img);
end

function z_best = newton_1d(costfun,z0,h,max_iter)

    z = z0;

    for k = 1:max_iter
        fprintf("Iteration %d: z = %.6f \n", k, z);
        f0 = costfun(z);
        f1 = costfun(z + h);
        f_1 = costfun(z - h);
        fprintf("Cost: %.6f, %.6f, %.6f \n", f0, f1, f_1);
        d1 = (f1 - f_1) / (2*h);
        d2 = (f1 - 2*f0 + f_1) / (h^2);

        z = z - d1/d2;
    end

    z_best = z;
end

