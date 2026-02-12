SH = h5read("D:\STAGE\AUZ_SH_CHOROID_LOG\260202_AUZ0752_test_UWF_OD5_OS6_2_HD_4\raw\260202_AUZ0752_test_UWF_OD5_OS6_2_HD_4_output.h5","/SH_Slices");
[Nx,Ny,Nw,Nt] = size(SH);

SH = 10.^SH;

art_sig=mean(SH(:,:,1:8,:),[1,2,3]);
[sys_idx_list, pulse_artery_filtered, sys_max_list, sys_min_list] = find_systole_index_choroid(art_sig);
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

sz = size(SHbeat);
sz(3) = sz(3)/2;
c = zeros(sz,'single');
c(:,:,1:(Nw/2),:) = cumsum(flip(SHbeat(:,:,1:Nw/2,:),3),3) + cumsum(SHbeat(:,:,(Nw/2+1):Nw,:),3);


c = permute(c,[1,2,4,3]);

image = squeeze(mean(c,[3,4]));

% ms = sum(c, [1 2]);
c = c ./ imgaussfilt(squeeze(image), 50);
% ms2 = sum(c, [1 2]);
% c = (ms / ms2) .* c;

