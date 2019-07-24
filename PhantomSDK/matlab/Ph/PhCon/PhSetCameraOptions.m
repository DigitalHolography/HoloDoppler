function [HRES] = PhSetCameraOptions(CN ,CO)

[HRES, dummyCO] = calllib('phcon','PhSetCameraOptions', CN, CO);
OutputError(HRES);

end

