function C = phase_fluctuation(H)

C = H .* conj(circshift(H, 1, 3)); %create a matrix with phase difference

end
