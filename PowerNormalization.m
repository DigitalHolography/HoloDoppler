classdef PowerNormalization
    %UNTITLED Summary of this class goes here
    %   Detailed explanation goes here

    properties
        Nx
        Ny
        Nt
        reference_wave
        reference_wave_power
        reference_wave_power_std
        beating_wave_variance
        beating_wave_variance_power
        beating_wave_variance_power_std
    end

    methods
        function obj = PowerNormalization(reference_wave, reference_wave_power, reference_wave_power_std, beating_wave_variance, beating_wave_variance_power, beating_wave_variance_power_std)
            obj.reference_wave = fliplr(rot90(reference_wave,3));
            obj.reference_wave_power = reference_wave_power;
            obj.reference_wave_power_std = reference_wave_power_std;
            obj.beating_wave_variance = fliplr(rot90(beating_wave_variance));
            obj.beating_wave_variance_power = beating_wave_variance_power;
            obj.beating_wave_variance_power_std = beating_wave_variance_power_std;
            [obj.Nx, obj.Ny, ~, obj.Nt] = size(reference_wave);
        end

        function printFigures(obj,output_dirpath,output_dirname)
            % Prints the figures of the power normalization data
            curves = {obj.reference_wave_power, obj.reference_wave_power_std, obj.beating_wave_variance_power, obj.beating_wave_variance_power_std};
            titles = {"Reference Wave Power AVG","Reference Wave Power STD","Beating Wave Variance Power AVG","eating Wave Variance Power STD"};
            figure_names = {'reference_wave_power','reference_wave_power_std','beating_wave_variance_power','beating_wave_variance_power_std'};
            for ii = 1:4
                y = curves{ii};
                y_name = titles{ii};
                figure_name = figure_names{ii};
                f = figure();
                hold on, box on
                plot(y,'k','Linewidth',2)
                yline(mean(y),'--k','LineWidth',2)
                gravstr = sprintf('Mean : %5.0f ',round(mean(y)));
                legend(y_name,gravstr);
                fontsize(gca,12,"points")
                strXlabel = sprintf("Frame"); 
                strYlabel = sprintf("%s in AU",y_name); 
                xlabel(strXlabel,'Fontsize',14);
                ylabel(strYlabel,'Fontsize',14);
                pbaspect([1.618 1 1]);
                set(gca,'Linewidth',2);
                title(y_name)
                axis tight;
                
                print('-f','-dpng',fullfile(output_dirpath,'png',strcat(output_dirname,sprintf("_%s.png",figure_name))));
                print('-f','-deps','-tiff',fullfile(output_dirpath,'eps',strcat(output_dirname,sprintf("_%s.eps",figure_name))));
                hold off
                close(f)
            end
        end

        function generateVideos(obj, output_dirpath, gif_period)

            generate_video(obj.reference_wave, output_dirpath, 'reference_wave', [], [], false, false, false, gif_period, true);
            generate_video(obj.beating_wave_variance, output_dirpath, 'beating_wave_variance', [], [], false, false, false, gif_period, true); 
        end

        function obj = resize(obj, var_bin)
        % Power normalization
        obj.reference_wave = imresize3(squeeze(obj.reference_wave), [ceil(obj.Nx/var_bin) ceil(obj.Ny/var_bin) obj.Nt]);
        obj.beating_wave_variance = imresize3(squeeze(obj.beating_wave_variance), [ceil(obj.Nx/var_bin) ceil(obj.Ny/var_bin) obj.Nt]);
        end
    end
end