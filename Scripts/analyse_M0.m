function analyse_M0(h5_path)
% h5_path
SH = h5read(h5_path,"/SH_Slices");

[h5folder,name,~] = fileparts(h5_path);

if ~isfolder(fullfile(h5folder,name))
    mkdir(fullfile(h5folder,name));
end

NAME = name;
[Nx,Ny,Nw,Nt] = size(SH); 

M0=mean(SH(:,:,1:8,:)+SH(:,:,25:32,:),3);
M0_ = reshape(M0,Nx*Ny,Nt);
kmax = 20;
[U,S,V] = svds(double(M0_),kmax);
Uimg = reshape(U,Nx,Ny,kmax);

for j=1:kmax
    figure,imagesc(Uimg(:,:,j));
end

figure,plot(V(:,:))

end