function [HRES, CH] = PhNewCineFromCamera( cameraNumber, cineNumber )

pCH = libpointer('voidPtrPtr');
[HRES, CH] = calllib('phfile','PhNewCineFromCamera', cameraNumber, cineNumber, pCH);
OutputError(HRES);

end

