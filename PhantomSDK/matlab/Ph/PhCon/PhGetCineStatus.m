function [HRES,cineStatuses] = PhGetCineStatus(CN)

cs = get(libstruct('tagCINESTATUS'));
maxCineCnt = PhMaxCineCnt(CN);
for i=1:maxCineCnt
    csa(i) = cs;
end

csp = libpointer('tagCINESTATUS',csa);
[HRES, dummy] = calllib('phcon','PhGetCineStatus',CN,csp);
OutputError(HRES);

for i=1:maxCineCnt
    cineStatuses(i) = get(csp+(i-1),'Value');
end
end