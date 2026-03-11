function moment1 = moment1(SH, f1, f2, fs, batch_size, gw)

arguments
    SH
    f1
    f2
    fs
    batch_size
    gw = 0
end

% Calculate the first moment of the spectrum
SH = abs(SH);

% Create frequency weights for the first moment calculation
f = fftfreq(batch_size, 1/fs);
weights = f;
weights(abs(weights) > f2) = 0;
weights(abs(weights) < f1) = 0;

% Compute the first moment by summing the weighted spectrum across frequencies
moment1 = sum(SH .* reshape(weights, 1, 1, []), 3);

if gw ~= 0
    moment1 = flat_field_correction(moment1, gw);
end

end
