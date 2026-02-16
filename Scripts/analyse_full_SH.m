function analyse_full_SH(h5_path)
% h5_path
SH = h5read(h5_path,"/SH_Slices");

[h5folder,name,~] = fileparts(h5_path);

if ~isfolder(name)
    mkdir(name);
end

NAME = name;
[Nx,Ny,Nw,Nt] = size(SH);

% SH = 10.^SH;

% one beat
SH = fftshift(SH,3);

art_sig=mean(SH(:,:,1:8,:),[1,2,3]);
[sys_idx_list, ~, ~, ~] = find_systole_index_choroid(art_sig);
Nbeat = length(sys_idx_list) - 1;
sz = size(SH);
Ninterp = 64;
sz(4) = Ninterp;
SHbeat = zeros(sz,'single');
for i = 1:Nbeat
    i1 = sys_idx_list(i);
    i2 = sys_idx_list(i+1)-1;
    SHbeat = SHbeat + interpft(SH(:,:,:,i1:i2),Ninterp,4);
end
SHbeat = SHbeat / Nbeat;

image = squeeze(mean(SHbeat,[3,4]));
SHbeat = SHbeat ./ imgaussfilt(squeeze(image), 50);

Nt = Ninterp; % when using one beat interpolated
SH_ = reshape(SHbeat,Nx*Ny,Nw*Nt);

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
    inv = 1;
    
    imwrite(rescalemask(inv * Uimg(:,:,j),mask),fullfile(h5folder,name,sprintf("%s mode %d lin ff.png",NAME,j)));
    imwrite(rescalemask(inv * Vtw(:,:,j),mask),fullfile(h5folder,name,sprintf("%s mode %d spectrogram.png",NAME,j)));
    plotSig(inv *S(j)* Vtw, j,fullfile(h5folder,name,sprintf("%s mode %d",NAME, j)));
end

end