function [p_fit, fitPhase] = fitSphericPhase(E, X, Y)
%FITSHIFTEDQUADRATICPHASE Fit a shifted quadratic phase to a complex field.
   

    if nargin < 3
        error('Usage: fitShiftedQuadraticPhase(E, X, Y)');
    end
    if ~isequal(size(E), size(X), size(Y))
        error('E, X, and Y must have the same size.');
    end

    % Ensure double precision
    E = double(E);
    X = double(X);
    Y = double(Y);

    phi = angle(E);

    phi = unwrap_phase(phi);

    phi = phi - min(phi(:));

    p0 = [300, 200, 0, 0, 0];

    % ----------------------------------------------------------
    % Cost function in complex domain
    % ----------------------------------------------------------
    costFun = @(p) sum(abs(phi(:) - ( sqrt(p(5) +p(1)*(X(:)-p(3)).^2 + p(2)*(Y(:)-p(4)).^2))).^2);

    % ----------------------------------------------------------
    % Optimize using Nelder–Mead (no toolbox required)
    % ----------------------------------------------------------
    opts = optimset('Display', 'iter', 'TolX', 1e-5, 'TolFun', 1*numel(E));
    p_fit = fminsearch(costFun, p0, opts);

    % Extract results

    fitPhase = sqrt(p_fit(1)*(X - p_fit(3)).^2 + p_fit(2)*(Y - p_fit(4)).^2 + p_fit(5)) ;
    % fitField = exp(1i * fitPhase);
end