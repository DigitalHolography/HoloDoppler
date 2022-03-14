function [config, found] = fetch_config(filepath, filename)
    config = [];
    found = false;
    [file_name, suffix] = get_last_file_name(filepath, filename, 'mat');
    if (suffix > -1)
        config = load(sprintf("%s%s_%d.mat", filepath, file_name, suffix));
        config = config.config;
        found = true;
    end
end