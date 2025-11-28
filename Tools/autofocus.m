function z_opti = autofocus(rend,Params)
    f = waitbar(0, 'Autofocus in progress. Please wait...');

    

    zmin = Params.autofocus_range(1);
    zmax = Params.autofocus_range(2);

    function c = clamp(c,z,zmin,zmax)
        fprintf("Evaluating at z = %.6f c = %.6f \n", z, c);
        if (z<zmin || z>zmax)
            c = 1e12;
        end
    end

    cost = @(z) clamp(cost_function(rend,Params,z),z,zmin,zmax);

    z00 = Params.spatial_propagation;
    % 
    % zmin = z0 - 0.05;
    % zmax = z0 + 0.05;

    

    % N=15;
    % 
    % zvals = linspace(zmin,zmax,N);
    % cvals = zeros(1,N);
    % for k=1:N
    %     cvals(k) = cost(zvals(k));
    % end
    % 
    % [~,idx] = min(cvals);
    % 
    % z_opti = zvals(idx);
    % 
    % figure;
    % plot(zvals,cvals);

    




    options = optimset('TolX',1e-2,'Display','off','MaxFunEvals',30,'OutputFcn',@(x,optimValues,state) waitbar_update(x,optimValues,state,f));

    obj = @(z) (z<zmin || z>zmax) * 1e12 + cost(z);
    
    z0 = (zmin + zmax)/2;
    
    [zopti, fval, exitflag, output] = fminsearch(obj, z0, options);

    if exitflag ~=1
        fprintf("Autofocus did not converge. Using keeping value z = %.6f\n", z0);
        z_opti = z00;
    else
        fprintf("Autofocus converged in %d iterations. Optimal z = %.6f with cost = %.6f\n", output.iterations, zopti, fval);
        z_opti = zopti;
    end
    
    close(f);
end

function v = cost_2(I)
G = edge(I,'sobel');


% Gx = [-1 0 1; -2 0 2; -1 0 1];
% Gy = [-1 -2 -1; 0 0 0; 1 2 1];
% 
% Ix = conv2(I, Gx, 'same');
% Iy = conv2(I, Gy, 'same');
% 
% G = sqrt(Ix.^2 + Iy.^2);

disk = diskMask(size(I,2),size(I,1),0.35);
v = -mean(G(disk));
end

function v = cost_3(I)
disk = diskMask(size(I,2),size(I,1),0.35);
vals = I(disk);

G = edge(I,'sobel');
edges = G(disk);

contrast = std(double(vals));
edgeStrength = mean(edges);

v = -contrast - edgeStrength;
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
    
    c = cost_2(img);
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

