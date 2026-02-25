function export_h5_video(filename, name, video)
dataset_path = sprintf('/%s', name);
if isfile(filename)
    info = h5info(filename);
    dataset_exists = any(strcmp({info.Datasets.Name}, name));
else
    dataset_exists = false;
end
if ~dataset_exists
    h5create(filename, dataset_path, size(video), 'Datatype', 'single');
end
h5write(filename, dataset_path, video);
end