function [HRES] = PhSetCameraName(CN, camName)

pCamName = libpointer('cstring',camName);
[HRES dummy] = calllib('phcon','PhSetCameraName',CN, pCamName);
OutputError(HRES);

end

