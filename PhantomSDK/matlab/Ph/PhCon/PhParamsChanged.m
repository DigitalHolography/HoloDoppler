function [HRES, changed] = PhParamsChanged( CN )

[HRES, changed] = calllib('phcon','PhParamsChanged', CN, 0);
OutputError(HRES);

end

