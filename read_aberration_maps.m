function read_aberration_maps(filename)

%{ 
FIXME
data = readmatrix(filename);
parameters = readmatrix(filename,  'Range' ,  '1:1');

size_data = [parameters(1) parameters(2)];
subimage_size = parameters(3);
subimage_stride = parameters(4);

path = 'C:\Users\Michael\Documents\191107_RIJ0023' ;


coef = size(data,1)/parameters(2);

astyg_g = zeros(size_data(1));
defocus = zeros(size_data(1));
astyg_d = zeros(size_data(1));
my_map = customcolormap_preset('red-white-blue');

%Fixme : le foutre dans une matrice 512x512 et mettre une interpolation
%avec un mini filtre qui moyenne sur les voisins


for i = 1 : coef
    map = data(size_data(1)*(i-1) + 1 : size_data(1)*(i-1) + size_data(1),  1 : size_data(2));
    map(abs(map)>25) = 0;
    map = mat2gray(map);

    file_name = sprintf('%s_%s.%s', 'Coef', int2str(i) , 'png');

    %change of color
    Numcolor = size(my_map, 1);
    Imgmin = min(map(:)) ;
    Imgmax = max(map(:)) ;
    map = uint8((map-Imgmin)./(Imgmax-Imgmin).* (Numcolor-1)) ;
    imwrite(map,my_map,fullfile(path, file_name));

%}


data = readmatrix(filename);
parameters = readmatrix(filename,  'Range' ,  '1:1');

% read parameteres from first line of the data
size_data = [parameters(1) parameters(2)];
subimage_size = parameters(3);
subimage_stride = parameters(4);

% %FIXME
coef = size(data,1)/parameters(2);

[filepath,name,ext] = fileparts(filename);


for i = 1 : coef
    map = data(size_data(1)*(i-1) + 1 : size_data(1)*(i-1) + size_data(1),  1 : size_data(2));
    centerx = ceil(size(map, 1)/2);
    centery = ceil(size(map, 2)/2);
    %% remove outliers
    window_size = floor(0.5 * size(map, 1));
    corrected_map = map;
    blurred_map = imgaussfilt(map, floor(size(map,1)/4));
    s = std(map ,[], "all");
    threshold = 1;
    for id_x = 0 : 1 : (size(map, 1) - window_size)
        for id_y = 0 : 1 :(size(map, 1) - window_size)
            window = map(id_x + 1 : id_x + window_size, id_y + 1 : id_y + window_size);
            blurred_window = blurred_map(id_x + 1 : id_x + window_size, id_y + 1 : id_y + window_size);
            window(abs(window - mean(window, "all")) > threshold*s) = blurred_window(abs(window - mean(window, "all")) > threshold*s);
            corrected_map(id_x + 1 : id_x + window_size, id_y + 1 : id_y + window_size) = window;
        end
    end
%     map = corrected_map;
%     map = rmoutliers(map, "mean");

    %% remove offset and normalize
    ref = (abs(map)>10);

    norm_map = sqrt(sum(map .* map, "all"));
    map = map ./ norm_map;
    
    m = sort(map(:), 'ascend');
    minim = mean(m(1:4));
    map = map - minim;
    map(ref) = 0;

%%  project on the zernike functions
    projection = zeros(3, 1);
    [ ~ , zern ] = zernike_phase([1 2 4], floor(size(map,1)*sqrt(2)), floor(size(map, 2).*sqrt(2)));
    NNx = round((size(map,1))*(sqrt(2)-1)/2);
    zern = circshift(zern, -NNx, 1);
    zern = circshift(zern, -NNx, 2);
    zern = zern(1 : size(map,1), 1 : size(map,1), :);
    
    for j = 1 : 3
          projection(j) = sum(zern(:,:,j) .* map, "all")/nnz(~ref);
    end
    

    %% display and save
    disp(projection);
    map = imresize(map, [512 512], 'nearest');
    figure
    imagesc(map);
    axis square;
    axis off;
%     fig = append('-f', int2str(i));
%     print(fig,'-dpng', fullfile('C:\Users\Novokuznetsk\Pictures\zernike_coefficient_maps', append('220524_SVJ0547', int2str(2+i)))) ;
%     imwrite(mat2gray(map), sprintf('%s.png', fullfile('C:\Users\Bronxville\Pictures\221123', append(name, int2str(2+i)))));
end
end