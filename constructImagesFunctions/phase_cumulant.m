function [phi] = phase_cumulant(A, idxspan1, idxspan2,  gw)
%% integration interval
% A : 3D array x,y,omega
% idxspan1 = index vector (positive freqs)
% idxspan2 = index vector (negative freqs)

moment = squeeze(sum(A(:, :, idxspan1(1):idxspan2(1)), 3));
for i = 2 : length(idxspan1)
    moment = moment + squeeze(sum(A(:, :, idxspan1(i):idxspan2(i)), 3));
end
phi = gather(moment);
end