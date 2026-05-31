from pathlib import Path
import os
import h5py
from tqdm import tqdm
import imageio as iio

from .utils import *
from .get_version import get_version

def save_outputs(file_reader, video_path=None, holodoppler_path=None, vid=None, 
                vid_debug=None, parameters=None, reg_list=None, 
                coefs_list=None, end_frame=None, first_frame=None, num_batch=None):
    """
    Main entry point for saving. 
    Determines priority: holodoppler_path > video_path > default
    """
    
    # 1. Path and Mode Resolution
    # Default path generation
    default_path = _get_default_output_path(file_reader)
    
    if holodoppler_path:
        if isinstance(holodoppler_path,bool):
            holodoppler_path = default_path
        target_dir = Path(holodoppler_path)
        save_mode = "FULL"
    elif video_path:
        if isinstance(video_path,bool):
            video_path = default_path
        target_dir = Path(video_path)
        save_mode = "LITE"
    else:
        target_dir = default_path
        save_mode = "FULL"

    # 2. Execute Save Bundle
    _save_bundle(
        file_reader,
        target_dir=target_dir,
        mode=save_mode,
        vid=vid,
        vid_debug=vid_debug,
        parameters=parameters,
        reg_list=reg_list,
        coefs_list=coefs_list,
        end_frame=end_frame,
        first_frame=first_frame,
        num_batch=num_batch
    )

def _get_default_output_path(file_reader):
    """Generates the standard Holodoppler directory structure"""
    base_name = Path(file_reader.file_path).stem
    return Path(file_reader.file_path).parent / base_name / f"{base_name}_HD"

def _save_bundle(file_reader, target_dir, mode, vid, vid_debug, parameters, 
                reg_list, coefs_list, end_frame, first_frame, num_batch):
    """
    Unified saving engine. 
    mode="FULL" -> Saves everything including H5.
    mode="LITE" -> Saves videos, pngs, json, txt.
    """
    # Create subdirectories
    subdirs = ["png", "mp4", "avi", "json"]
    if mode == "FULL":
        subdirs.append("h5")
        
    for sub in subdirs:
        (target_dir / sub).mkdir(parents=True, exist_ok=True)

    fps = min((num_batch / (end_frame - first_frame) * parameters["sampling_freq"]), 65)
    # vid = np.transpose(vid_t, axes=[0,1,3,2]) # flip x-y
    
    # vid = np.flip(vid, axis=2) # flip y

    # --- 1. Setup Data Map ---
    save_map = {
        "moment_0": vid[:,0,:,:],
        "moment_1": vid[:,1,:,:],
        "moment_2": vid[:,2,:,:],
        "moment_0_ff": vid[:,3,:,:],
        # "moment_0_flatfield": flatfield3D(vid_t[:,0,:,:], parameters["registration_flatfield_gw"]), sorry but too slow
    }
    
    for k, v in enumerate(parameters.get("frequency_bands", [])):
        save_map[f"band_{v[0]}_{v[1]}"] = vid[:,4+k,:,:]
    
    # Add debug videos to map
    for key, data in vid_debug.items():
        
        # Ensure debug videos are (T, H, W)
        if data.ndim == 3 and data.shape[-1] == num_batch:
            data = np.moveaxis(data, -1, 0)
            
        if parameters["square"] and key in ["M0ffnoreg", "M0notfixed", "montage", "montagenormalized"]:
            m = max(data.shape[-2], data.shape[-1])
            data = resize_slicewise(data, m, m)
        
        save_map[f"debug_{key}"] = data

    # --- 2. Save Visuals (MP4, AVI, PNG) ---
    for name, data in save_map.items():
        uint8_data = normalize_to_uint8(data)
        write_video_file(target_dir / "mp4" / f"{name}.mp4", uint8_data, fps, "mp4v")
        write_video_file(target_dir / "avi" / f"{name}.avi", uint8_data, fps, "MJPG")
        if uint8_data.ndim == 3:
            iio.imwrite(target_dir / "png" / f"{name}.png", normalize_to_uint8(np.mean(data, axis=0)))
            # plt.imsave(target_dir / "png" / f"{name}.png", np.mean(uint8_data, axis=0), cmap="gray")

    # --- 3. Save Metadata (JSON, TXT) ---
    save_metadata(target_dir, file_reader,  parameters)
    
    # --- 4. Save H5 (Only if mode is FULL) ---
    if mode == "FULL":
        save_h5(target_dir, vid, parameters, reg_list, coefs_list)

def save_metadata(target_dir, file_reader,  parameters):
    """Saves all configuration and versioning files"""
    # JSON Params
    with open(target_dir / "json" / "parameters_holodoppler.json", "w") as f:
        json.dump(parameters, f, indent=4)
    
    # Versioning/Info
    (target_dir / "version_holodoppler.txt").write_text(f"py{get_version()}")
    
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        (target_dir / "git_version.txt").write_text(f"Git commit: {commit}\n{info_text}")
    except:
        (target_dir / "git_version.txt").write_text("Git commit: Not Available")

    if file_reader.ext == ".holo":
        with open(target_dir / "json" / "holovibes_footer.json", "w") as f:
            json.dump(file_reader.file_footer, f, indent=4)
        with open(target_dir / "json" / "holovibes_header.json", "w") as f:
            json.dump(file_reader.file_header, f, indent=4)

def save_h5(target_dir, vid, parameters, reg_list, coefs_list):
    """Saves raw data to HDF5 with compression"""
    
    target_dir_name = target_dir.name if target_dir.name else "output"
    
    vid_t = np.flip(vid,axis=2) # flip y for doppler view
    with h5py.File(target_dir / "h5" / f"{target_dir_name}_output.h5", "w") as f:
        f.create_dataset("moment0", data=vid_t[:,0,:,:]) # compression="gzip"
        f.create_dataset("moment1", data=vid_t[:,1,:,:])
        f.create_dataset("moment2", data=vid_t[:,2,:,:])
        f.create_dataset("moment0ff", data=vid_t[:,3,:,:])
        for k, v in enumerate(parameters.get("frequency_bands", [])):
            f.create_dataset(f"band_{v[0]}_{v[1]}", data=vid_t[:,4+k,:,:])
        f.create_dataset("HD_parameters", data=json.dumps(parameters))
        info_text = f"py{get_version()}"
        f.create_dataset("HD_version", data=info_text)
        
        if parameters.get("image_registration") and reg_list:
            f.create_dataset("registration", data=np.array(reg_list, dtype=np.float32))
        
        if parameters.get("shack_hartmann") and coefs_list:
            f.create_dataset("zernike_coefs_radians", data=np.stack(coefs_list).astype(np.float32))