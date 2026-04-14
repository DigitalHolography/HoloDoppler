h5_path = "D:\STAGE\AUZ_SH_CHOROID_LIN\260202_AUZ0752_test_UWF_OD3_OS4_1_HD_7\raw\260202_AUZ0752_test_UWF_OD3_OS4_1_HD_7_output.h5";

SH = h5read(h5_path,"/SH_Slices");

[~,name,~] = fileparts(h5_path);

if ~isfolder(name)
    mkdir(name);
end

NAME = name;
[Nx,Ny,Nw,Nt] = size(SH);

% SH = 10.^SH;

% flat field
image = squeeze(mean(SH,[3,4]));
SH = SH ./ imgaussfilt(squeeze(image), 50);

% mask
n = min(Nx,Ny);
cx0 = (Nx+1)/2;
cy0 = (Ny+1)/2;
r0  = n/2;
[xg,yg] = ndgrid(1:Nx, 1:Ny);
mask = ((xg-cx0).^2 + (yg-cy0).^2) <= r0^2;

% one beat
art_sig=mean((SH(:,:,1:8,:) + SH(:,:,end-7:end,:)).* mask,[1,2,3]);
[sys_idx_list, ~, ~, ~] = find_systole_index_choroid(art_sig);
disp(sys_idx_list)
Nbeat = length(sys_idx_list) - 1;
sz = size(SH);
Ninterp = 64;
sz(4) = Ninterp;
SHbeat = zeros(sz,'single');
for i = 1:Nbeat
    i1 = sys_idx_list(i);
    i2 = sys_idx_list(i+1)-1;
    SHbeat = SHbeat + interpft(SH(:,:,:,i1:i2) .* mask,Ninterp,4);
end
SHbeat = SHbeat / Nbeat;


SH_ = reshape(SH,Nx*Ny,Nw*Nt);
SH_ = double(SH_);
kmax = 20;
[U,S,V] = svds(SH_,kmax);
Uimg = zeros(Nx*Ny,kmax);
Uimg(validPix,:) = U;
Uimg = reshape(Uimg,Nx,Ny,kmax);
Vtw = reshape(V, Nw, Nt, kmax);

for j=1:kmax
    inv = 1;
    
    imwrite(rescalemask(inv * Uimg(:,:,j),mask),sprintf("%s mode %d lin ff.png",NAME,j));
    plotSig(inv*Vtw, j,sprintf("%s mode %d",NAME, j));
end