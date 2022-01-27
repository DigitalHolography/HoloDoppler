function [conf, found] = fetch_conf(filepath, filename)
    [~, filename, ~] = fileparts(filename);
    try
        conf = load(sprintf("%s%s.mat", filepath, filename));
        conf = conf.conf;
        found = true;
    catch
        conf = [];
        found = false;
    end
end