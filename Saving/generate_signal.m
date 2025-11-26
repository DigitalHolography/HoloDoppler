function generate_signal(video, output_path, name)
% Saves a raw signal array to a h5 file, 

arguments
    video
    output_path
    name
end

[~, output_dirname] = fileparts(output_path);
output_filename_h5 = sprintf('%s_%s.h5', output_dirname, 'output');
export_h5_signal(fullfile(output_path, 'raw', output_filename_h5), name, (video));

end

function export_h5_signal(filename, name, signal)
h5create(filename,sprintf("/%s",name),size(signal),Datatype="single");
h5write(filename,sprintf("/%s",name),single(signal));
end

