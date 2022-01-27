function [conf, found] = fetch_conf(filepath, filename)
    conf = [];
    found = false;
    [file_name, suffix] = get_last_config_file_name(filepath, filename);
    if (suffix > -1)
        conf = load(sprintf("%s%s_%d.mat", filepath, file_name, suffix));
        conf = conf.conf;
        found = true;
    end
end