function read_aberration_maps(filename)
parameters = readmatrix(filename,  'Range' ,  '1:1');
data = readmatrix(filename,  'Range' ,  '2:52');
size_data = [parameters(1) parameters(2)];
subimage_size = parameters(3);
subimage_stride = parameters(4);
% %FIXME
coef = size(data,1)/parameters(2);
size_data = [17 17];

for i = 1 : coef
    map = data(size_data(1)*(i-1) + 1 : size_data(1)*(i-1) + size_data(1),  1 : size_data(2));
    figure
    imagesc(map);
end

% figure(2)
% imagesc(B);
% 
% figure(3)
% imagesc(C);


end