
SH = h5read("D:\STAGE\AUZ_SH_CHOROID_LOG\260202_AUZ0752_test_UWF_OD3_OS4_1_HD_7\raw\260202_AUZ0752_test_UWF_OD3_OS4_1_HD_7_output.h5","/SH_Slices");
NAME = "trdhdrhrdrgrgrd";
[Nx,Ny,Nw,Nt] = size(SH);

image = squeeze(mean(SH,[3,4]));
SH = SH ./ imgaussfilt(squeeze(image), 50);
SH_ = reshape(SH,Nx*Ny,Nw*Nt);

n = min(Nx,Ny);
cx0 = (Nx+1)/2;
cy0 = (Ny+1)/2;
r0  = n/2;
[xg,yg] = ndgrid(1:Nx, 1:Ny);
mask = ((xg-cx0).^2 + (yg-cy0).^2) <= r0^2;
validPix = mask(:) & all(isfinite(SH_),2);
SH_ = SH_(validPix,:);

SH_ = double(SH_);
kmax = 6;
[U,S,V] = svds(SH_,kmax);
Uimg = zeros(Nx*Ny,kmax);
Uimg(validPix,:) = U;
Uimg = reshape(Uimg,Nx,Ny,kmax);

Vtw = reshape(V, Nw, Nt, kmax);

for j=1:kmax
    
    imwrite(rescalemask(inv * Uimg(:,:,j),mask),sprintf("%s mode %d lin ff.png",NAME,j));
    plotSig(inv*Vtw, j,sprintf("%s mode %d",NAME, j));
end




% Vtw = reshape(V(:,1:kmax), Nt, Nw, kmax);
% 
% a = zeros(Nt, kmax);
% for j = 1:kmax
%     a(:,j) = S(j,j) * sum(Vtw(:,:,j), 2);
% end
% 
% Xvt = U(:,1:kmax) * a.';   % [Npix_valid x Nt]
% 
% Xfull = nan(Nx*Ny, Nt);
% Xfull(validPix,:) = Xvt;
% 
% M0_video_kmax = reshape(Xfull, Nx, Ny, Nt);   % [Nx x Ny x Nt]