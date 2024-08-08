function zChanged(app)
%UNTITLED Summary of this function goes here
%   Detailed explanation goes here
if ~app.file_loaded
    return
end

app.z_retina = app.zretinaEditField.Value;

if app.Switch.Value == "z_retina"
    app.z_reconstruction = app.zretinaEditField.Value;
    app.compute_kernel(false);
end

app.z_iris = app.zirisEditField.Value;
if app.Switch.Value == "z_iris"
    app.z_reconstruction = app.zirisEditField.Value;
    app.compute_kernel(false);
end

end