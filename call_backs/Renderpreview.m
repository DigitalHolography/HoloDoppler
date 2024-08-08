function Renderpreview(app)
if ~app.file_loaded
    return
end
app.renderLamp.Color = [1, 0, 0];
drawnow;

GPUpreview = check_GPU_for_preview(app); 

preview_cache = GuiCache(app);
app.var_ImageTypeList = ImageTypeList(); %the preview image type list

switch preview_cache.time_transform.type
    case 'FFT'
        type = preview_cache.preview_choice;
    case 'PCA'
        type = 'pure_PCA';
end

app.var_ImageTypeList.(type).select();

app.var_ImageTypeList.construct_images(app.frame_batch,preview_cache,GPUpreview,repha)


% 
% compute_FH(app,GPUpreview);
% if app.ShackHartmannCheckBox.Value
%     compute_ShackHartmann(app,false)
% end
% if strcmp(app.setUpDropDown.Value, 'Doppler')
%     compute_hologram(app,GPUpreview);
%     show_hologram(app);
% end
reset(gpuDevice(1)); % free gpu memory to avoid overflowing
end