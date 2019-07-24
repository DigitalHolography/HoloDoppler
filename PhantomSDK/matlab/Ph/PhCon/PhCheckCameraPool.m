function [poolChanged] = PhCheckCameraPool()

[HRES, poolChanged] = calllib('phcon','PhCheckCameraPool', 0);
OutputError(HRES);

end

