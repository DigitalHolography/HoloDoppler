function writeVideoOnDisc(data,filename,type)
% Writing function for videos to make use of parallel capacities 
% with parfeval
%  filename - - path to file and file name without extension
%  type     - - nothing for avi 'MPEG-4' for mp4
if nargin > 2
    w = VideoWriter(filename,type);
else
    w = VideoWriter(filename);
end
open(w)

if size(size(data)) == [1,3]
    data = reshape(data,size(data,1),size(data,2),1,size(data,3));
end

for jj = 1:size(data, 4)
    writeVideo(w, squeeze(data(:, :, :, jj)));
end

close(w);
end