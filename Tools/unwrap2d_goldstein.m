function phi_unwrapped = unwrap2d_goldstein(phi_wrapped, opts)
% unwrap2d_goldstein  - 2D phase unwrapping using Goldstein branch-cut algorithm
%
% phi_unwrapped = unwrap2d_goldstein(phi_wrapped, opts)
%
% Optional parameters in opts:
%   .residue_connect_radius   (default = 5)
%   .max_residue_pairs        (default = 2000)
%   .use_quality_map          (default = false)
%   .smooth_phase             (default = false)
%   .sigma                    (default = 1.5)
%   .flood_order              (default = 'row')
%
% Written for clarity and experimentation, not maximum performance.

if nargin < 2 || isempty(opts)
    opts = struct();
end

if ~isfield(opts, 'residue_connect_radius'); opts.residue_connect_radius = 5; end
if ~isfield(opts, 'max_residue_pairs'); opts.max_residue_pairs = 2000; end
if ~isfield(opts, 'use_quality_map'); opts.use_quality_map = false; end
if ~isfield(opts, 'sigma'); opts.sigma = 1.5; end
if ~isfield(opts, 'flood_order'); opts.flood_order = 'row'; end

wrap2pi = @(x) mod(x + pi, 2 * pi) - pi;
[M, N] = size(phi_wrapped);

% Compute residues
residue = zeros(M - 1, N - 1);

for i = 1:M - 1

    for j = 1:N - 1
        d1 = wrap2pi(phi_wrapped(i, j + 1) - phi_wrapped(i, j));
        d2 = wrap2pi(phi_wrapped(i + 1, j + 1) - phi_wrapped(i, j + 1));
        d3 = wrap2pi(phi_wrapped(i + 1, j) - phi_wrapped(i + 1, j + 1));
        d4 = wrap2pi(phi_wrapped(i, j) - phi_wrapped(i + 1, j));
        residue(i, j) = round((d1 + d2 + d3 + d4) / (2 * pi));
    end

end

% Find residues
[posY, posX] = find(residue == 1);
[negY, negX] = find(residue == -1);

branchCuts = false(M, N);
numPairs = 0;

for k = 1:length(posY)
    dists = hypot(negY - posY(k), negX - posX(k));
    [mn, idx] = min(dists);

    if ~isempty(mn) && mn <= opts.residue_connect_radius && numPairs < opts.max_residue_pairs
        [yy, xx] = bresenham_line(posY(k), posX(k), negY(idx), negX(idx));

        for t = 1:numel(xx)

            if yy(t) > 0 && yy(t) <= M && xx(t) > 0 && xx(t) <= N
                branchCuts(yy(t), xx(t)) = true;
            end

        end

        negY(idx) = []; negX(idx) = [];
        numPairs = numPairs + 1;
    end

end

% Flood-fill unwrapping
phi_unwrapped = nan(M, N);
phi_unwrapped(1, 1) = phi_wrapped(1, 1);

switch opts.flood_order
    case 'row'

        for i = 1:M

            for j = 1:N

                if j > 1 && ~isnan(phi_unwrapped(i, j - 1)) && ~branchCuts(i, j)
                    d = wrap2pi(phi_wrapped(i, j) - phi_wrapped(i, j - 1));
                    phi_unwrapped(i, j) = phi_unwrapped(i, j - 1) + d;
                elseif i > 1 && ~isnan(phi_unwrapped(i - 1, j)) && ~branchCuts(i, j)
                    d = wrap2pi(phi_wrapped(i, j) - phi_wrapped(i - 1, j));
                    phi_unwrapped(i, j) = phi_unwrapped(i - 1, j) + d;
                end

            end

        end

    case 'quality'
        visited = false(M, N);
        visited(1, 1) = true;

        % Precompute quality map
        qmap = imgradient(abs(phi_wrapped));

        % List of candidates (row, col, quality)
        candidates = [1, 1, qmap(1, 1)];

        while ~isempty(candidates)
            % Pick highest-quality pixel
            [~, idx] = max(candidates(:, 3));
            i = candidates(idx, 1);
            j = candidates(idx, 2);
            candidates(idx, :) = [];

            % Explore 4-neighbors
            neighbors = [i - 1, j; i + 1, j; i, j - 1; i, j + 1];

            for k = 1:size(neighbors, 1)
                ni = neighbors(k, 1); nj = neighbors(k, 2);

                if ni >= 1 && ni <= M && nj >= 1 && nj <= N && ~visited(ni, nj) && ~branchCuts(ni, nj)
                    % Unwrap relative to (i,j)
                    d = wrapToPi(phi_wrapped(ni, nj) - phi_wrapped(i, j));
                    phi_unwrapped(ni, nj) = phi_unwrapped(i, j) + d;
                    visited(ni, nj) = true;
                    % Add to candidate list
                    candidates = [candidates; ni, nj, qmap(ni, nj)];
                end

            end

        end

end

phi_unwrapped = phi_unwrapped - mean(phi_unwrapped(:), "omitnan");
end

function [y, x] = bresenham_line(y1, x1, y2, x2)
% simple Bresenham line algorithm
dx = abs(x2 - x1);
dy = abs(y2 - y1);
sx = sign(x2 - x1);
sy = sign(y2 - y1);
err = dx - dy;
x = x1; y = y1;
ptsx = []; ptsy = [];

while true
    ptsx(end + 1) = x; ptsy(end + 1) = y;
    if x == x2 && y == y2, break; end
    e2 = 2 * err;
    if e2 > -dy, err = err - dy; x = x + sx; end
    if e2 < dx, err = err + dx; y = y + sy; end
end

x = ptsx; y = ptsy;
end
