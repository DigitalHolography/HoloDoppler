function FH = register_in_z_via_phase(FH, shift)
% INPUT: shift that should be in the range from 0 to size(FH)/2

trace = zeros(1, size(FH, 3));


if (shift == 0)
    return ;
else
    trace(mod((size(FH, 3) + shift), size(FH, 3))) = 1;
    phase_trace = fftshift(ifft(trace));

    for tt = 1 : size(FH, 3)
        FH(:,:, tt) = FH(:,:, tt) * phase_trace(tt);
    end
end
end