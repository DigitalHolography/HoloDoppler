function prettyPrintNormalizationData(y,y_name,figure_name,output_dirpath,output_dirname)
%UNTITLED3 Summary of this function goes here
%   Detailed explanation goes here
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
axis tight;

print('-f','-dpng',fullfile(output_dirpath,'png',strcat(output_dirname,sprintf("_%s.png",figure_name))));
hold off
close(f)
end