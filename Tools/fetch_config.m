function config = fetch_config(filepath, filename)
    config = [];
    [~, filename, ~] = fileparts(filename);
    filename = sprintf("%s-config", filename);
    [file_name, suffix] = get_last_file_name(filepath, filename, 'mat');
    if (suffix > -1)
        config = load(sprintf("%s%s_%d.mat", filepath, file_name, suffix));
        config = config.config;
    end
end