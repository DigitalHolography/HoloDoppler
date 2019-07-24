function [ HRES, serial, cameraName ] = PhGetCameraID(CN)

pSerial = libpointer('uint32Ptr',0);
pCameraName = libpointer('cstring',blanks(PhIntConst.MAXSTDSTRSZ));
[HRES, serial, cameraName] = calllib('phcon','PhGetCameraID', CN, pSerial, pCameraName);
OutputError(HRES);

end