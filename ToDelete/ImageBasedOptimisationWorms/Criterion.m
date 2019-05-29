function [J] =  Criterion(FH,z,c,f1,f2,fS,MaskM0,delta_x,delta_y,gw);
% z : Zernike polynomials used for the phase correction 
% c : current coefficients of the Zernike polynomials
% f1,f2 : low, high frequency of Doppler spectrum calculation
% fS : sampling frequency, in the same units as f1 and f2
% MaskM0 : mask for low pass spatial filtering
% delta_x : horizontal image shift
% delta_y : vertical image shift
% gw : size of the gaussian win 
Nt = size(FH,3);
nGPU = 0;%gpuDeviceCount; %check if GPU is present
%global M0Corrected
n1 = round(f1*Nt/fS);% a verifier
n2 = round(f2*Nt/fS);
% Correction Phase Calculation // no GPU
PhaseCorrection = zeros(size(z,1),size(z,2));
for k = 1:numel(c)
    PhaseCorrection = PhaseCorrection + c(k)*z(:,:,k);%phi = \sum ai*zi
end
FHCorrected = bsxfun(@times,FH,exp(-1i*PhaseCorrection));% apply correction phase estimate in the reciprocal plane
HCorrected= ifft2(FHCorrected);% original plane
SHCorrected = fft(HCorrected,[],3); % Doppler spectrum
SHCorrected = abs(SHCorrected).^2;
SHCorrected= permute(SHCorrected, [2 1 3]);
SHCorrected = circshift(SHCorrected,[delta_x, delta_y, 0]);
if (size(FH,3)==1)
    M0Corrected = SHCorrected;
else
    M0Corrected = squeeze(sum(abs(SHCorrected(:,:,n1:n2)),3)); % power Doppler
    M0Corrected = M0Corrected./imgaussfilt(M0Corrected,gw);% flat-field Correction
end
M0Corrected_f = mat2gray(abs(ifft2(fft2(M0Corrected) .* fftshift(MaskM0))));

    % J = entropy(M0Corrected_f);
% J = entropy(M0Corrected_f)/norm(stdfilt(M0Corrected_f).^2);
J = entropy(M0Corrected_f(50:450,50:450))/norm(stdfilt(M0Corrected_f(50:450,50:450)).^2);
% J = entropy(M0Corrected_f(50:450,50:450))/norm(stdfilt(M0Corrected_f(50:450,50:450)))./mean2(M0Corrected_f(50:450,50:450));
% J = entropy(M0Corrected_f)./std2(M0Corrected_f);
% J = -norm(imgradient(M0Corrected_f));
% J = -norm(conv2(M0Corrected_f, ones(3)/9));
% J = entropy(M0Corrected_f)/norm(imgradient(M0Corrected_f));
% J=-norm(imgradient(M0Corrected_f))*norm(conv2(M0Corrected_f, ones(3)/9));
% J=-norm(imgradient(M0Corrected_f))-norm(conv2(M0Corrected_f, ones(3)/9));

% if isequal(nGPU,0)
%     PhaseCorrection = zeros(size(z,1),size(z,2));
%     for k = 1:numel(c)
%         PhaseCorrection = PhaseCorrection + c(k)*z(:,:,k);%phi = \sum ai*zi
%     end
%     FHCorrected = bsxfun(@times,FH,exp(-1i*PhaseCorrection));% apply correction phase estimate in the reciprocal plane
%     HCorrected= ifft2(FHCorrected);% original plane
%     SHCorrected = fft(HCorrected,[],3); % Doppler spectrum
%     SHCorrected = abs(SHCorrected).^2;
%     SHCorrected= permute(SHCorrected, [2 1 3]);
%     SHCorrected = circshift(SHCorrected,[delta_x, delta_y, 0]);
%     M0Corrected = squeeze(sum(abs(SHCorrected(:,:,n1:n2)),3)); % power Doppler
%     M0Corrected = M0Corrected./imgaussfilt(M0Corrected,gw);% flat-field Correction
%     M0Corrected_f = mat2gray(abs(ifft2(fft2(M0Corrected) .* fftshift(MaskM0))));
%     J = entropy(M0Corrected_f);
% else %nGPU>0
%     PhaseCorrection = gpuArray(zeros(size(z,1),size(z,2)));
%     c = gpuArray(c);
%     z = gpuArray(z);
%     FH = gpuArray(FH);
%     for k = 1:numel(c)
%         PhaseCorrection = PhaseCorrection + c(k)*z(:,:,k);%phi = \sum ai*zi
%     end
%     FHCorrected = bsxfun(@times,FH,exp(-1i*PhaseCorrection));% apply correction phase estimate in the reciprocal plane
%     HCorrected= ifft2(FHCorrected);% original plane
%     SHCorrected = fft(HCorrected,[],3); % Doppler spectrum
%     SHCorrected = abs(SHCorrected).^2;
%     SHCorrected = permute(SHCorrected, [2 1 3]);
%     SHCorrected = circshift(SHCorrected,[delta_x, delta_y, 0]);
%     M0Corrected = squeeze(sum(abs(SHCorrected(:,:,n1:n2)),3)); % power Doppler
%     M0Corrected = M0Corrected./imgaussfilt(M0Corrected,gw);% flat-field Correction    
%     M0Corrected_f = mat2gray(abs(ifft2(fft2(M0Corrected) .* fftshift(MaskM0))));
%     M0Corrected = gather(M0Corrected);
%     J = gather(entropy(M0Corrected_f));
% end %nGPU

end%function Criterion
