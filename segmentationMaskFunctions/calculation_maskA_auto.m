function [maskA,maskA_NotBinary] = calculation_maskA_auto(S)
% calculation_maskA_auto calculates a binary and a not binary masks.
% USAGE: [maskA,maskA_NotBinary] = calculation_maskA_auto(S,m,n,name)
%
% INPUT: 
%   S: (m x n x NumberFrames) matrix containing standart deviation for all the frames
%   m,n: Size of the images in the video
%
% OUPUT:
%   maskA: Binary mask of arteries
%   maskA_NotBinary: Non-binary mask of arteries
%
% Authors: 05/2021 Salim BENNANI & Malek AZAIZ


m = size(S,1);
n = size(S,2);

maskA = zeros(m,n);
maskA_NotBinary = zeros(m,n);

%automatic calculation of threshold

moy = mean(S,"all");


%FIXME
if moy > 12
    threshold=2*moy-2*std(reshape(S,1,[]));
    %reshape(S,1,[]) === S(:)
else
    threshold=3*moy;
end
    

for i=1:m
    for j=1:n
        x = S(i,j);
        if (x >= threshold)
            maskA(i,j) = 1;
            maskA_NotBinary(i,j) = x;
        else
            maskA(i,j)=0;
            maskA_NotBinary(i,j) = 0;
        end
    end %j
end %i
%TRY THIS
% maskA = S > (threshold);


%maskA=imdilate(imerode(maskA,strel('rectangle',[2,2])),strel('rectangle',[2,2]));

end