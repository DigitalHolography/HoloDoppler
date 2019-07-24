function [ HRES, aqParams, bmi] = PhGetCineParams(CN, cineNumber)

aqp = libstruct('tagACQUIPARAMS',[]);
pAQP = libpointer('tagACQUIPARAMS',aqp);
pbmi = libpointer('tagBITMAPINFO',libstruct('tagBITMAPINFO',[])); 
[HRES, aqParams, bmi] = calllib('phcon','PhGetCineParams',CN,cineNumber,pAQP,pbmi);
OutputError(HRES);

end

