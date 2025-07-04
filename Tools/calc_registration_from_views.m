function [SH_PSD] = calc_registration_from_views(view,view_ref,params)
SH_PSD = [];
for i=1:numel(params.image_types)
    if ismember(params.image_types{i}, {'SH_avg'})
        SH_PSD = abs(view.SH).^2;
        M0 = view.Output.power_Doppler.image;
        M0_ref = view_ref.Output.power_Doppler.image;
        [Ny,Nx] = size(M0);
        disc = diskMask(Nx,Ny,params.registration_disc_ratio/2);
        M0_tmp = (M0.*disc-mean(M0(disc)))/max(abs(M0(disc)));
        M0ref_tmp = (M0_ref.*disc-mean(M0_ref(disc)))/max(abs(M0_ref(disc)));
        [~,shift] = registerImagesCrossCorrelation(M0_tmp,M0ref_tmp);
        for j = 1:size(SH_PSD,3) % each frequency
            SH_PSD(:,:,j) = circshift(SH_PSD(:,:,j), floor(shift));
        end
    end
end
end