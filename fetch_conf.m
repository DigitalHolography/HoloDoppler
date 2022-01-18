function [conf, found] = fetch_conf(filename)
    conf = [];
    found = false;
    fd = fopen(filename, 'r');
    if (fd ~= -1)
        conf = jsondecode(fscanf(fd, "%s"));
        found = true;
    end
end