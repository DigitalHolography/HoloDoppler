function [ HRES, cameraCnt] = PhGetCameraCount( )

pCameraCnt = libpointer('uint32Ptr',0);
[HRES, cameraCnt] = calllib('phcon','PhGetCameraCount',pCameraCnt);
OutputError(HRES);

end

