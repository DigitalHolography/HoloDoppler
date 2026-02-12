



SH = h5read("E:\2026AUZ SH\260202_AUZ0752_test_UWF_OD3_OS4_2_HD_2_output.h5","/SH_Slices");

% S is Nx x Ny x Nt x Nw
epsv = 1e-6;
% S = log(abs(S).^2 + epsv); 
Nx = size(SH,3);
Ny = size(SH,4);
Nt = size(SH,1);
Nw = size(SH,2);

SH = permute(SH,[3 4 1 2]);



% SH_cumsum = cumsum(SH,4);

SH = reshape(SH, Nx*Ny, Nt*Nw);
% mu = mean(X,2);Xc = X - mu; % a voir; pas forcement necessaire
% sig = std(Xc,0,2) + 1e-6;
% Xc = Xc ./ sig;
% [U,S,V] = svd(X,'econ');

% k = 20;
% [U,S,V] = svds(X,k);

k = 3;
Uk_img = reshape(U(:,k), Nx, Ny);
Vk_tf = reshape(V(:,k), Nt, Nw);