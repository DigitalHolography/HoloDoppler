function [conf, found] = fetch_conf(filepath, filename)
    %conf = [];
    %found = false;
    try
        conf = load(fullfile(filepath, filename));
        conf = conf.conf;
        found = true;
    catch
        conf = [];
        found = false;
    end
end