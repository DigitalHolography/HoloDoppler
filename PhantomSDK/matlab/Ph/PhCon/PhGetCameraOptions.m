function [HRES, cameraOptions] = PhGetCameraOptions(CN)

CO = libstruct('tagCAMERAOPTIONS',[]);
pCO = libpointer('tagCAMERAOPTIONS',CO);
[HRES, cameraOptions] = calllib('phcon','PhGetCameraOptions',CN,pCO);
OutputError(HRES);

end