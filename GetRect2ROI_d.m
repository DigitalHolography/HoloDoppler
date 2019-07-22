function ROI = GetRect2ROI_d(img, ROI_n)
% if (exist('ROI_n') == 0)
%     ROI_n = [1 Nx, 1 Ny];
% end
ROINumber = size(ROI_n, 2);

figure; 
imshow(abs(imadjust(mat2gray(img))),[])
frame_h = get(handle(gcf),'JavaFrame');
set(frame_h,'Maximized',1);

% fig = figure; imshow(abs(((img))),[])
% fig.WindowState = 'maximized';
for ii = 1:ROINumber
    if (ROI_n(3,ii) ~= 0)
    text(ROI_n(3,ii)-12,ROI_n(1,ii)-12,num2str(ii),'Color',[1 1 0],'FontSize',20);
    DrawRect(ROI_n(:,ii),'b',1.5);
    end
end
GR = getrect;
GR = round(GR);
ROI(:,1) = GR(2);
ROI(:,2) = GR(2)+GR(4)-1;
ROI(:,3) = GR(1);
ROI(:,4) = GR(1)+GR(3)-1;
close;
end