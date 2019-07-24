function [img, unshiftedImage] = ConstructMatlabImage(imPixels,imSizeX,imSizeY,samplespp,bps)
%CONSTRUCTMATLABIMAGE Construct a matlab img from pixels values returned by
%PhGetImage C function

%PARAMETERS:
%samplespp = samples per pixel (1 or 3)
%bps = bits per sample (8,10,12,14)

%RETRUNS:
% img - 1D Gray/3D RGB matrix. For 16bpp images the pixel values are alligned to 16bits
% unshiftedIm - 1D Gray/3D RGB matrix with image pixel values unshifted

imPixels=imPixels';
img=reshape(imPixels,imSizeY,samplespp,imSizeX);
unshiftedImage = zeros(imSizeY,imSizeX,samplespp,class(img));
for i=1:samplespp
    p = flipud(reshape(img(:,i,:),imSizeY,imSizeX));
    unshiftedImage(:,:,samplespp-i+1) = p;
end
if (bps>8 && bps<16)
    img = bitshift(unshiftedImage,16-bps);
else
    img = unshiftedImage;
end

end

