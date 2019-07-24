function [ HRES progress ] = PhGetWriteCineFileProgress( CH )

[HRES, dummy, progress] = calllib('phfile', 'PhGetWriteCineFileProgress', CH, 0);

end

