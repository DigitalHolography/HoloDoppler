function [fitObj, gof] = fit_spectrum(axis_x, signal, f1, f2, opt)
% Fit a spectrum to a model of the form:
%   y = a + b*log10((x-x0)^2 + g^2)
% where:
%   a = baseline level
%   b = slope of the log10 term
%   x0 = center frequency (in kHz)
%   g = width parameter (in kHz)

arguments
    axis_x (:, 1) {mustBeNumeric}
    signal (:, 1) {mustBeNumeric}
    f1 (1, 1) {mustBeNumeric, mustBePositive}
    f2 (1, 1) {mustBeNumeric, mustBePositive, mustBeGreaterThan(f2, f1)}
    opt.useSymmetricFit (1, 1) logical = false
    opt.annotation (1, 1) logical = true
end

% Model
x = double(axis_x(:));
y = double(signal(:));

fitMask = (abs(x) <= f2) & (abs(x) >= f1);
xf = x(fitMask);
yf = y(fitMask);

% Symmetric Fit
if opt.useSymmetricFit
    xp = abs(xf);
    % average points with same |x| (requires gridded axis; works well if axis_x is symmetric)
    [xu, ~, ic] = unique(xp);
    yu = accumarray(ic, yf, [], @mean);
    xf_fit = xu;
    yf_fit = yu;
    % In symmetric mode we set x0 = 0 in the model.
    fix_x0_to_zero = true;
else
    xf_fit = xf;
    yf_fit = yf;
    fix_x0_to_zero = false;
end

% Define fit type
if fix_x0_to_zero
    ft = fittype('a + b*log10((x).^2 + g^2)', ...
        'independent', 'x', 'coefficients', {'a', 'b', 'g'});
else
    ft = fittype('a + b*log10((x-x0).^2 + g^2)', ...
        'independent', 'x', 'coefficients', {'a', 'b', 'x0', 'g'});
end

% Initial guesses
% a ~ min(y), b ~ (max-min)/log10(range^2/g^2)
a0 = min(yf_fit);
g0 = max((f1 + eps) * 0.25, (f2 + eps) * 0.02); % width guess in kHz
b0 = 1; % slope guess

if fix_x0_to_zero
    start = [a0, b0, g0];
else
    x00 = 0;
    start = [a0, b0, x00, g0];
end

% Bounds (helps prevent nonsense fits)
if fix_x0_to_zero
    lb = [-Inf, -Inf, 0];
    ub = [Inf, Inf, Inf];
else
    lb = [-Inf, -Inf, -f1, 0]; % x0 near center; relax if needed
    ub = [Inf, Inf, f1, Inf];
end

opts = fitoptions(ft);
opts.StartPoint = start;
opts.Lower = lb;
opts.Upper = ub;
opts.Robust = 'Bisquare'; % robust to spikes/outliers
opts.MaxIter = 2000;

% Fit
[fitObj, gof] = fit(xf_fit, yf_fit, ft, opts);

% Evaluate fit over full axis for overlay
xx = linspace(min(x), max(x), 2000).';

if fix_x0_to_zero
    yy = fitObj.a + fitObj.b * log10((xx) .^ 2 + fitObj.g ^ 2);
    x0_est = 0;
else
    yy = fitObj.a + fitObj.b * log10((xx - fitObj.x0) .^ 2 + fitObj.g ^ 2);
    x0_est = fitObj.x0;
end

% Plot overlay
p_fit = plot(xx, yy, 'r--', 'LineWidth', 1.5, 'DisplayName', 'Fit: a+b log10((x-x0)^2+g^2)');

% Report parameters in command window and optionally on plot
g_est = fitObj.g; % gamma in kHz (in your axis units)

if fix_x0_to_zero
    txt = sprintf('Fit: a=%.3g, b=%.3g,\ng=%.3g kHz | R^2=%.4f', fitObj.a, fitObj.b, g_est, gof.rsquare);
else
    txt = sprintf('Fit: a=%.3g, b=%.3g,\nx0=%.3g kHz,\ng=%.3g kHz | R^2=%.4f', fitObj.a, fitObj.b, x0_est, g_est, gof.rsquare);
end

disp(txt);

% Put a small annotation in the corner
if opt.annotation
    yl = ylim;
    xl = xlim;
    text(xl(1) + 0.02 * range(xl), yl(2) - 0.2 * range(yl), txt, ...
        'FontSize', 9, 'Color', 'r', 'Interpreter', 'none');
    uistack(p_fit, 'top');
end

end
