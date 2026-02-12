function img = rescalemask(img,mask)
vmin = min(img(mask));
vmax = max(img(mask));
img(mask) = (img(mask) - vmin) / (vmax - vmin);
img(img>1) = 1;
img(img<0) = 0;

end