function plot_columns_reg(video_M0_reg,image_ref,output_dirpath)
[~, output_dirname] = fileparts(output_dirpath);
output_filename = sprintf('%s_%s.%s', output_dirname, 'registration_columns', 'avi');
v = VideoWriter(fullfile(output_dirpath,'avi',output_filename));
open(v)
figure(56);
aa = [1,size(video_M0_reg,1),min(mean(video_M0_reg(:,:,:),1),[],'all'),max(mean(video_M0_reg(:,:,:),1),[],'all')];

for i=1:size(video_M0_reg,4)
    
    plot(1:size(video_M0_reg,2),mean(video_M0_reg(:,:,i),1),'k-','LineWidth', 2);
    hold on;
    plot(1:size(video_M0_reg,2),mean(image_ref(:,:),1),'b-','LineWidth', 2);
    hold off;
    
    legend('original','reference');
    fontsize(gca, 14, "points");
    xlabel("x", 'FontSize', 14);
    ylabel("mean of columns", 'FontSize', 14);
    pbaspect([1.618 1 1]);
    set(gca, 'LineWidth', 2);
    axis(aa);

    % saving to a video
    ax = gca;
    ax.Units = 'pixels';
    pos = ax.Position;
    ti = ax.TightInset;
    rect = [-ti(1), -ti(2), pos(3)+ti(1)+ti(3), pos(4)+ti(2)+ti(4)];
    F = getframe(ax,rect);
    
    writeVideo(v,F);
end
close(v);
close(56);
end