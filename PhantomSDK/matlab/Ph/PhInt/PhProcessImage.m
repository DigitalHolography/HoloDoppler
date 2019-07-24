function [HRES, pixels, ih] = PhProcessImage(pixels, ih, procID, procParams)

pPixels = libpointer('voidPtr', pixels);
[HRES, dummyPixels, pixels, ih, dummyOpt] = calllib('phint','PhProcessImage', pPixels, pPixels, ih, procID, procParams);
OutputError(HRES);

end