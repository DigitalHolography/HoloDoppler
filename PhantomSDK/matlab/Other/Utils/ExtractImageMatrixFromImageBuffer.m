function [ pixels ] = ExtractImageMatrixFromImageBuffer( pixels, IH )

%extract image from image buffer pPixels
imgSizeInBytes = (IH.biBitCount/8)*IH.biWidth*IH.biHeight;
pixels = pixels(1:imgSizeInBytes);
imWidthInBytes = (IH.biBitCount/8)*IH.biWidth;
if (Is16BitHeader(IH))
    pixels = typecast(pixels, 'uint16');
    imDataWidth = imWidthInBytes/2;
else
    imDataWidth = imWidthInBytes;
end
%reshape as a matrix
pixels = reshape(pixels, imDataWidth, IH.biHeight);

end

