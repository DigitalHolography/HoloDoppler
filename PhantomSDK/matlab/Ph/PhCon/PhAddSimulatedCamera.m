function [HRES] = PhAddSimulatedCamera(camVer, serial)

HRES = calllib('phcon','PhAddSimulatedCamera',camVer, serial);
OutputError(HRES);

end

