function [ result, fileName ] = PhGetOpenCineName()

strIn = char(ones(32768,1,'int8'));%allocate buffer string at maximum size possible
%While allocating do not use zeros for string because it will crash

%Option is 0 for single selection or OFN_MULTISELECT for multiple selection
[result, fileName] = calllib('phfile','PhGetOpenCineName',strIn, uint32(0));

end

