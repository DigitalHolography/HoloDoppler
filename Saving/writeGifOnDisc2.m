function writeGifOnDisc2(data, filepath, Hertz, Duration)
% Writing function for gif to make use of parallel capacities


if size(size(data)) == [1, 3]
    data = reshape(data, size(data, 1), size(data, 2), 1, size(data, 3));
end
numX=size(data,1);
numY=size(data,2);
numT=size(data,4);
numC=size(data,3);

NewNumFrames = floor(Hertz * Duration);

for col = 1:numC
    images_interp(:, :, col, :) = imresize3(squeeze(data(:, :, col, :)),[numX,numY,NewNumFrames]);
end
images_interp(images_interp < 0) = 0;
images_interp(images_interp > 256) = 256;
for tt = 1:NewNumFrames
    if numC == 3
        [A, map] = rgb2ind(images_interp(:, :, :, tt), 256);
    else
        [A, map] = gray2ind(images_interp(:, :, :, tt), 256);
    end
    if tt == 1
        imwrite(A, map, filepath, "gif", "LoopCount", Inf, "DelayTime", 1/Hertz);
    else
        imwrite(A, map, filepath, "gif", "WriteMode", "append", "DelayTime", 1/Hertz);
    end
end
end
