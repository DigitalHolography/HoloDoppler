function [] =  print_zernike()
Nx = 6000;
X = 1:Nx;
%mask = meshgrid(X);
%for i = 1:Nx
%    for j = 1:Nx
%        if sqrt(i^2+j^2)<= 1
%           mask(i,j) = 0;
%       else
%           mask(i,j) = 1;
%        end
%   end
%end
        
path = 'C:\Users\Michael\Desktop\' ;
mkdir(fullfile(path, 'Zernike'));
path = 'C:\Users\Michael\Desktop\Zernike' ;
mode_max = 13;
mode_min = 11;
my_map = customcolormap_preset('red-white-blue');
Imgmin = 0;
Imgmax = 0;

for i = mode_min:mode_max 

    file_name = sprintf('%s_%s.%s', 'Zernike', int2str(i) , 'png');  
    [~,phi] = zernike_phase(i, Nx, Nx);
    im_phase = mat2gray(phi);
    Numcolor = size(my_map, 1);
    Imgmin = min(im_phase(:)) ;
    Imgmax = max(im_phase(:)) ;
    im_phase = uint8( (im_phase-Imgmin)./(Imgmax-Imgmin).* (Numcolor-1) ) ;
    imwrite(im_phase,my_map,fullfile(path, file_name))
end


