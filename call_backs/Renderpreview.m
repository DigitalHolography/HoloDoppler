function Renderpreview(app)
if ~app.file_loaded
    return
end
app.renderLamp.Color = [1, 0, 0];
drawnow;
GPUpreview = 1;%check_GPU_for_preview(app); forcing to save time
if GPUpreview 
    disp("Using GPU.")
else 
    disp("Not using GPU.")
end
compute_FH(app,GPUpreview);
if app.ShackHartmannCheckBox.Value
    compute_ShackHartmann(app,false)
end
if strcmp(app.setUpDropDown.Value, 'Doppler')
    compute_hologram(app,GPUpreview);
    show_hologram(app);
end
end