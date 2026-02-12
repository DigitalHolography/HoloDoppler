
SH = h5read("D:\STAGE\260202_AUZ0752_test_UWF_OD3_OS4_2_HD_2_output.h5","/SH_Slices");
[Nx,Ny,Nw,Nt] = size(SH);
SH_ = reshape(SH,Nx*Ny,Nw*Nt);
SH_ = double(SH_);
[U,S,V] = svds(SH_,20);
M=U*S;
M = reshape(M,Nx,Ny,20);
figure, implay(rescale(M))
figure, imagesc(M(:,:,1))
figure, imagesc(M(:,:,2))
figure, imagesc(M(:,:,3))
figure, imagesc(M(:,:,4))
figure, imagesc(M(:,:,5))
figure, imagesc(M(:,:,6))
figure, imagesc(M(:,:,7))
figure, imagesc(M(:,:,8))
figure, imagesc(M(:,:,9))
figure, imagesc(M(:,:,10))
figure, imagesc(M(:,:,11))
figure, imagesc(M(:,:,12))
figure, imagesc(M(:,:,13))
figure, imagesc(M(:,:,14))
figure, imagesc(M(:,:,15))
figure, imagesc(M(:,:,16))
figure, imagesc(M(:,:,17))
figure, imagesc(M(:,:,18))
figure, imagesc(M(:,:,19))
figure, imagesc(M(:,:,20))

N = S*V';
N = reshape(N,Nw,Nt);

N = reshape(N,Nw,Nt,20);
figure, imagesc(N(:,:,1))
