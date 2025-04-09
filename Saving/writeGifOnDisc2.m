function writeGifOnDisc2(data, filepath, timePeriodMin, numFramesFixed)
% Writing function for gif to make use of parallel capacities
% with parfeval
%  filename - - path to file and file name with '.gif' extension

arguments
    data
    filepath
    timePeriodMin = NaN
    numFramesFixed = NaN
end

if size(size(data)) == [1, 3]
    data = reshape(data, size(data, 1), size(data, 2), 1, size(data, 3));
end

numFrames = size(data, 4);

gifWriter = GifWriter2(filepath, numFrames, ...
    timePeriodMin, numFramesFixed);

for frameIdx = 1:numFrames
    gifWriter.write(data(:, :, :, frameIdx), frameIdx);
end

gifWriter.generate();
gifWriter.delete();
end
