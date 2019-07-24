function [HRES] = PhSendSoftwareTrigger(CN)

HRES = calllib('phcon','PhSendSoftwareTrigger',CN);
OutputError(HRES);

end

