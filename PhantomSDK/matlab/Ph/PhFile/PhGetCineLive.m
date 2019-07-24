function [HRES, CH] = PhGetCineLive( cameraNumber )

pCH = libpointer('voidPtrPtr');
[HRES, CH] = calllib('phfile','PhGetCineLive', cameraNumber, pCH);
OutputError(HRES);

end

