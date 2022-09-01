function read_aberration_maps(filename)
data = readmatrix(filename);
parameters = readmatrix(filename,  'Range' ,  '1:1');
% parameters = data(1, :);
% data = readmatrix(filename,  'Range' ,  '2:');
% data = data(2:end, :);
size_data = [parameters(1) parameters(2)];
subimage_size = parameters(3);
subimage_stride = parameters(4);
% %FIXME
coef = size(data,1)/parameters(2);
% size_data = [17 17];

for i = 1 : coef
    map = data(size_data(1)*(i-1) + 1 : size_data(1)*(i-1) + size_data(1),  1 : size_data(2));
    disp(sum(map .* (abs(map) < 10), "all")/nnz(abs(map) < 10));
    figure
    imagesc(map);
    clim([-15 15]);
    axis square;
    axis off;
    fig = append('-f', int2str(i));
    print(fig,'-depsc', fullfile('C:\Users\Novokuznetsk\Pictures\zernike_coefficient_maps', append('SVJ0547_coef_', int2str(2+i)))) ;
end

% zernike_indices = [3 4 5 6 7 8 9];
% [~,Zern] = zernike_phase(zernike_indices, floor(512* sqrt(2)), floor(512* sqrt(2)));
% zern = Zern(floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256, floor(512* sqrt(2))/2 - 255 : floor(512* sqrt(2))/2 + 256, : );
% % figure(1)
% % imagesc(zern(:,:,3));
% 
% for i = zernike_indices
%     figure
%     imagesc(-zern(:,:,i-2));
%     axis square;
%     axis off;
%     fig = append('-f', int2str(i-2));
%     print(fig,'-depsc', fullfile('C:\Users\Novokuznetsk\Pictures\zernike_coefficient_maps', append('coef_', int2str(i)))) ;
% end

end