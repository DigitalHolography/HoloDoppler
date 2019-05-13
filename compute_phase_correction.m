function [phase] = compute_phase_correction(coefs, zernike_values)
% compute a phase correction given base combination coefficients
%
% coefs: scalar array, coordinates of the phase correction in the zernike
% base
%
% zernike_values: zernike base evaluated on a grid
%
% phase: phase correction evaluated on a grid
phase = 0;
for k = 1:numel(coefs)
    phase = phase + coefs(k) * zernike_values(:, :, k);
end
end