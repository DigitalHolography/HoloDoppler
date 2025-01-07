function FH = register_FH(FH, shifts, reg_batch_size, size_factor)
% apply registration to FH
%
% FH: an interferogram stack in the Fourier plan
%
% shifts: a 2D array of size 2 x size(FH,3) containing dx and
% dy shifts for registration
%
% reg_batch_size: the size of an interferogram batch used when
% computing the shifts (N.B. ~= size(FH,3) because here size(FH,3) == batch_size * size_factor)
%
% size_factor: the factor between the registration batch size
% and the current batch size (optional, defaults to 1)

if ~exist('size_factor', 'var')
    size_factor = 1;
end

Nx = size(FH, 1);
Ny = size(FH, 2);
magic_number = 710; % This is the magic number
zernikes = evaluate_zernikes([1 1], [1 -1], Nx, Ny);

for i = 1:size_factor
    zernike_coefs = shifts(:, i);
    zernike_coefs(1) = zernike_coefs(1) * magic_number * 2 / Nx;
    zernike_coefs(2) = zernike_coefs(2) * magic_number * 2 / Ny;
    tilts = zernike_coefs(1) .* zernikes(:,:,1) + zernike_coefs(2) .* zernikes(:,:,2);
    phase = exp(-1i * tilts);
    FH(:,:,(i-1)*reg_batch_size + 1:i*reg_batch_size) = FH(:,:,(i-1)*reg_batch_size + 1:i*reg_batch_size) .* phase;
end
end