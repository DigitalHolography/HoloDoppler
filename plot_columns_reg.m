function plot_columns_reg(video_M0_reg,output_dirpath)
v = VideoWriter(fullfile(output_dirpath,'avi\registration_columns'));
open(v)
figure(56);
aa = [1,size(video_M0_reg,4),min(sum(video_M0_reg(:,:,:),1),[],'all'),max(sum(video_M0_reg(:,:,:),1),[],'all')];

for i=1:size(video_M0_reg,4)
    plot(1:size(video_M0_reg,2),sum(video_M0_reg(:,:,i),1),'k-','LineWidth', 2);
    axis(aa);
    fontsize(gca, 14, "points");
    xlabel("x", 'FontSize', 14);
    ylabel("sum of column", 'FontSize', 14);
    pbaspect([1.618 1 1]);
    set(gca, 'LineWidth', 2);
    axis tight;
    writeVideo(v,getframe)
end
close(v)
end