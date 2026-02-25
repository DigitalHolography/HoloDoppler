function analyse_M0_(h5_path)
% h5_path
moment0 = h5read(h5_path,"/moment0");
moment0 = squeeze(moment0);

[h5folder,name,~] = fileparts(h5_path);

output_folder_path_name = fullfile(h5folder,name,"full_time_modes_decomp");

if ~isfolder(output_folder_path_name)
    mkdir(output_folder_path_name);
end

[Nx,Ny,Nt] = size(moment0); 

% moment0_img = mean(moment0,3);
% M0 = moment0 / imgaussfilt(moment0_img,35);
M0 = moment0;



M0_ = reshape(M0,Nx*Ny,Nt);
kmax = 8;
[U,S,V] = svds(double(M0_),kmax);
Uimg = reshape(U,Nx,Ny,kmax);
Vt = reshape(V, Nt, kmax);


fs = 37000;
subfs = fs/256;


for j=1:kmax
    inv = 1;
    imwrite(rescale(inv * Uimg(:,:,j)),fullfile(output_folder_path_name,sprintf("%s mode %d lin ff.png",name,j)));
    time = linspace(0,Nt*1/subfs,Nt);
    f=figure("Visible","off"); plot(time,inv *S(j,j)* Vt(:,j));
    xlabel("time (s)","FontSize",11);
    ax = gca;
    ax.FontSize = 11; 
    saveas(f,fullfile(output_folder_path_name,sprintf("%s mode %d signal.png",name,j)));
    close(f);
end

export_h5_video(fullfile(output_folder_path_name,'raw.h5'),"Uimg",single(Uimg));
export_h5_video(fullfile(output_folder_path_name,'raw.h5'),"Vt",single(Vt * S));

end