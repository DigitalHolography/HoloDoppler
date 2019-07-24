function [ HRES, wb, satCnt ] = PhMeasureCineWB( CH, imagePoint, squareSide, imgRng)

imagePoint = libstruct('tagPOINT',imagePoint);
imgRng = libstruct('tagIMRANGE',imgRng);
wbIn = libstruct('tagWBGAIN');
[HRES, dummyCH, dummyPoint, dummyImgRNG, wb, satCnt] = calllib('phfile','PhMeasureCineWB',CH, imagePoint, squareSide, imgRng, wbIn, 0);
OutputError(HRES);

end

