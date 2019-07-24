function [ HRES ] = PhStopWriteCineFileAsync( CH )

[HRES, dummy] = calllib('phfile', 'PhStopWriteCineFileAsync', CH);
OutputError(HRES);

end

