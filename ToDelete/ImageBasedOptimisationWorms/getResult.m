function [PhaseCorrection M0Corrected] = getResult(FH,z,c,f1,f2,fS,delta_x,delta_y,lambda,pasx,pasy,gw);
[Nx Ny Nt] = size(FH);    % max is 512, but might be too much for the computer's RAM
n1 = round(f1*Nt/fS);
n2 = round(f2*Nt/fS);
% Corrected Phase Calculation
PhaseCorrection = 0;
for k = 1:numel(c)
    PhaseCorrection = PhaseCorrection+c(k)*z(:,:,k);
end
FHCorrected=bsxfun(@times,FH,exp(-1i*PhaseCorrection));
% Propagation inverse
HCorrected= ifft(ifft(FHCorrected,[],1),[],2);
% Calculating Fourier transform on temporal dimension
SHCorrected = fft(HCorrected,[],3); 
SHCorrected = abs(SHCorrected).^2;
SHCorrected= permute(SHCorrected, [2 1 3]);
SHCorrected = circshift(SHCorrected,[delta_x, delta_y, 0]);
if (size(FH,3)==1)
    M0Corrected = SHCorrected;
else
    M0Corrected = squeeze(sum(abs(SHCorrected(:,:,n1:n2)),3));
    % Flat Field Correction
    M0Corrected = M0Corrected./imgaussfilt(M0Corrected,gw);
end
end
