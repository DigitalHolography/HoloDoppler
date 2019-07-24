function [ HRES ] = PhNotifyDeviceChangeCB()

[HRES, dummy] = calllib('phcon','PhNotifyDeviceChangeCB', libpointer);
OutputError(HRES);

end

