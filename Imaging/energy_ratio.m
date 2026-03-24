function [energy_ratio] = energy_ratio(SH, f1, f2, fi1, fi2, fs, batchSize)

arguments
    SH
    f1
    f2
    fi1
    fi2
    fs
    batchSize
end

SH = abs(SH);

% Weights
f = fftfreq(batchSize, 1 / fs);
weights = f;
abs_weights = abs(weights);
weights(abs_weights > f2) = 0;
weights(abs_weights < f1) = 0;

% Low Frequency Weights
weightsLF = weights;
weightsLF(abs_weights > fi1) = 0;
weightsLF(weightsLF ~= 0) = 1;

% High Frequency Weights
weightsHF = weights;
weightsHF(abs_weights < fi2) = 0;
weightsHF(weightsHF ~= 0) = 1;

% Energies
LF_psd_avg = mean(SH .* reshape(weightsLF, 1, 1, []), 3);
HF_psd_avg = mean(SH .* reshape(weightsHF, 1, 1, []), 3);

% energy ratio
high_low_ratio = HF_psd_avg ./ LF_psd_avg;

energy_ratio = gather(high_low_ratio);

end
