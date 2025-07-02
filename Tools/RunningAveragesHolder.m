classdef RunningAveragesHolder < handle
    properties
        running_averages
    end
    methods
        function obj = RunningAveragesHolder()
            obj.running_averages = [];
        end
        function update(obj, view, params)
            for i=1:numel(params.image_types)
                if ismember(params.image_types{i}, {'SH_avg'})
                    SH_PSD = abs(view.SH).^2;
                    M0 = view.Output.power_Doppler.image;
                    if isempty(obj.running_averages)
                        obj.running_averages.SH = SH_PSD;
                        obj.running_averages.M0_ref = M0;
                    else
                        [Ny,Nx] = size(M0);
                        disc = diskMask(Nx,Ny,params.registration_disc_ratio/2);
                        M0_tmp = (M0.*disc-mean(M0(disc)))/max(abs(M0(disc)));
                        M0ref_tmp = (obj.running_averages.M0_ref.*disc-mean(obj.running_averages.M0_ref(disc)))/max(abs(obj.running_averages.M0_ref(disc)));
                        [~,shift] = registerImagesCrossCorrelation(M0_tmp,M0ref_tmp);
                        for j = 1:size(SH_PSD,3) % each frequency
                            SH_PSD(:,:,j) = circshift(SH_PSD(:,:,j), floor(shift));
                        end
                        obj.running_averages.SH = obj.running_averages.SH + SH_PSD;
                    end
                end
            end
        end
    end
end
