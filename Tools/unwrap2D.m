function unwrapped = unwrap2D(phase)
% unwrap2D - basic 2D phase unwrapping using gradient integration
%
% INPUT:
%   phase - wrapped phase (radians)
%
% OUTPUT:
%   unwrapped - unwrapped phase map

    % Compute wrapped gradients
    dx = diff(phase, 1, 2);
    dy = diff(phase, 1, 1);

    % Unwrap gradients
    dx = unwrap(dx, [], 2);
    dy = unwrap(dy, [], 1);

    % Integrate unwrapped gradients
    unwrapped = cumsum([zeros(size(phase,1),1), dx], 2);
    unwrapped = cumsum([zeros(1,size(phase,2)); dy], 1);
end
