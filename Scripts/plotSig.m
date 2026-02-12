function plotSig(Vtw, j, outPrefix)
% plotSig  Plot summed-frequency signal for mode j and export EPS+PNG.
%
% Uses y = -sum(Vtw(:,:,j),1) convention (sum over dimension 1).
% Vtw is expected to be [Nt x Nw x kmax] or [something x something x kmax].

if nargin < 3 || isempty(outPrefix)
    outPrefix = sprintf("mode_%d", j);
end

fs = 78000/512;   % Hz
dt = 1/fs;

% y: sum over dim=1, then squeeze -> column vector (typically length Nw)
y = squeeze(sum(Vtw(:,:,j), 1));   % -> [Nw x 1] (or [1 x Nw] -> squeeze fixes it)
y = y(:);                           % force column

t = (0:numel(y)-1) * dt;            % seconds (index -> seconds)

f = figure('Visible','off','Color','w');
ax = axes(f); hold(ax,'on'); box(ax,'on');

plot(ax, t, y, 'k-', 'LineWidth', 2);   % black line

xlabel(ax, 'time (s)', 'FontSize', 14);
ylabel(ax, 'u.a.',     'FontSize', 14);
set(ax, 'LineWidth', 2, 'FontSize', 14, 'TickDir','out');
pbaspect(ax, [2.5 1 1]);

axis(ax,'tight');
axT = axis(ax);
padx = 0.02 * (axT(2)-axT(1) + eps);
pady = 0.05 * (axT(4)-axT(3) + eps);
axis(ax, [axT(1)-padx axT(2)+padx axT(3)-pady axT(4)+pady]);

% Export
print(f, outPrefix + ".eps", "-depsc2", "-r300");
exportgraphics(f, outPrefix + ".png", "Resolution", 100);

close(f);
end
