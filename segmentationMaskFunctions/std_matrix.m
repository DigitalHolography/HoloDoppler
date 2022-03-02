function S = std_matrix(I,NumberFrames,m,n)
% std_matrix returns  the standard deviation of every pixel in a (m x n)
% matrix M (in a "std_+name"  file)
% USE: std_matrix(I,NumberFrames,m,n)
% 
% INPUT: 
%   NumberFrames: Number of frames in  the video (can choose integer or whole)
%   m,n: Size of the images in the video
%
% OUPUT:
%   S: (m x n x NumberFrames) matrix containing standart deviation for all the frames
%
% Authors: 05/2021 Salim BENNANI & Malek AZAIZ

S=zeros(m,n);

for i=1:m
    for j=1:n
        V=data_pixel(I,NumberFrames,[j,i]); % temporal variation of the pixel
        S(i,j)=sqrt(var(V(:)));             % standard deviation 
                     
    end
end

end