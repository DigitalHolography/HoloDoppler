function [ isOffline ] = PhOffline(CN)

[isOffline] = calllib('phcon', 'PhOffline', CN);

end

