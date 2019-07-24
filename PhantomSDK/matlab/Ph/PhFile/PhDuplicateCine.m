function [ HRES, ch_dest ] = PhDuplicateCine( ch_source )

pChDest = libpointer('voidPtrPtr');
[HRES, dummyAll] = calllib('phfile','PhDuplicateCine', pChDest, ch_source);
OutputError(HRES);
ch_dest = pChDest.Value;

end

