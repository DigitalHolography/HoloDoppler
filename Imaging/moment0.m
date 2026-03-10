function moment0 = moment0(SH, f1, f2, fs, batch_size, gw)

arguments
    SH
    f1
    f2
    fs
    batch_size
    gw = 0
end

% Calculate the zeroth moment of the spectrum
SH = abs(SH);

% Create frequency weights for the zeroth moment calculation
weights = linspace(-fs / 2, fs / 2, batch_size);
weights(abs(weights) > f2) = 0;
weights(abs(weights) < f1) = 0;
weights(weights ~= 0) = 1; % Set non-zero weights to 1 for the zeroth moment

% Compute the zeroth moment by summing the weighted spectrum across frequencies
moment0 = sum(SH .* reshape(weights, 1, 1, []), 3);

if gw ~= 0
    moment0 = flat_field_correction(moment0, gw);
end

end
