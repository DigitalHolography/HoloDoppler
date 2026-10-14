from utils import *

holo_paths = [
    p for p in list_files(r"E:\261014_LSCI")
    if p.endswith(".holo")
]

hd_folders = find_hd_folders(holo_paths)

plot_holo_montage(
    holo_paths,
    pattern=r"spatial_lsci.png$",
    ncols=5,
    figsize_per_image=(3, 3),
    save_path="montage.png"
)