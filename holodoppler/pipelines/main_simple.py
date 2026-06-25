from holodoppler.saving import save_preview_images, _get_default_output_path, save_outputs, _save_videos
from holodoppler.propagation import fresnel_transform, fresnel_transform_with_phase, angular_spectrum_transform, angular_spectrum_transform_with_phase
from holodoppler.shack_hartmann import construct_subapertures_fresnel, construct_subapertures_angular, calculate_displacements, calculate_displacements_graph_laplacian
from holodoppler.zernike import fit_zernike_fresnel, fit_zernike_angular_spectrum, southwell_phase_integration
from holodoppler.utils import resize_slicewise, zoom_slicewise_fast, pad_array_centrally, gaussian_flatfield, update_from_footer, normalize_to_uint8
from holodoppler.filtering import svd_filter, frequency_symmetric_filtering, fourier_time_transform, corner_compensation
from holodoppler.moments import moment
from holodoppler.registration import register_trs, apply_registration, apply_registration3D
from holodoppler.plotting import DebugPlotterManager
from holodoppler.backend import BackendManager
from holodoppler.file_reader import FileReaderFactory, CineFileReader, HoloFileReader


import cupy as cp
from cupyx.scipy.ndimage import gaussian_filter
from tqdm import tqdm

from collections import defaultdict

def _process_batch(parameters, frames, phase_term = None):
    xp = cp
    fft = cp.fft
    nt_sub = frames.shape[0]
    prop_method = parameters["spatial_propagation"]

    # Propagation
    if phase_term is not None:
        if prop_method == "Fresnel":
            holograms = fresnel_transform_with_phase(
                xp, fft, frames, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                phase_term, use_output_kernel=parameters["Fresnel_use_ouput_kernel"]
            )
        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform_with_phase(
                xp, fft, frames, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                phase_term
            )
    else:
        if prop_method == "Fresnel":
            holograms = fresnel_transform(
                xp, fft, frames, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
                use_output_kernel=parameters["Fresnel_use_ouput_kernel"]
            )
        elif prop_method == "AngularSpectrum":
            holograms = angular_spectrum_transform(
                xp, fft, frames, parameters["z"], parameters["pixel_pitch"], parameters["wavelength"],
            )

    # SVD filtering
    holograms_f = svd_filter(xp, holograms, parameters["svd_threshold"], filter_mode = parameters["svd_filter_mode"], remove_dc = parameters["svd_remove_dc"])

    del holograms  # Free memory early 

    d = {}

    # Temporal transform
    if parameters.get("temporal_transformation") == "FourierTransform":
        spectrum_f = fourier_time_transform(xp, fft, holograms_f)

    else:
        spectrum_f = holograms_f

    # Frequency selection
    idxs, freqs = frequency_symmetric_filtering(
        xp, fft, nt_sub, parameters["sampling_freq"], parameters["low_freq"], parameters.get("high_freq")
    )
    psd = xp.abs(spectrum_f) ** 2

    # psd_angle = xp.abs(spectrum_f_angle) ** 2

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

    # Moments
    d["M0"] = moment(xp, psd[idxs], freqs, 0)
    d["M1"] = moment(xp, psd[idxs], freqs, 1)
    d["M2"] = moment(xp, psd[idxs], freqs, 2)
    d["M0ff"] = gaussian_flatfield(d["M0"], parameters.get("registration_flatfield_gw", 1.0), gaussian_filter)

    # Frequency bands
    for k, (f1, f2) in enumerate(parameters.get("frequency_bands", [])):
        idxs_band, _ = frequency_symmetric_filtering(xp, fft, nt_sub, parameters["sampling_freq"], f1, f2)
        band = xp.mean(psd[idxs_band], axis=0)
        d[f"band_{k}_{f1}_{f2}"] = band

    return d

def preview_simple(file_path, parameters):
    file_reader = FileReaderFactory.create(file_path)
    
    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)
    print("parameters : ", parameters)
    
    batch_size = parameters["batch_size"]
    first_frame = parameters["first_frame"]
    frames = file_reader.read_frames(first_frame=first_frame, batch_size=batch_size)
    
    # transfer to gpu
    frames = cp.array(frames)

    # calc on gpu
    res = _process_batch(parameters, frames=frames)

    # transfer to cpu
    res_np = {k: cp.asnumpy(v) for k, v in res.items()}

    # free gpu ram
    del res
    cp.get_default_memory_pool().free_all_blocks()

    save_preview_images(res_np, _get_default_output_path(file_reader.file_path) / "preview")



def process_simple(file_path, parameters):
    file_reader = FileReaderFactory.create(file_path)
    
    if file_reader.ext == ".holo":
        print("file header :", file_reader.file_header)
        parameters = update_from_footer(parameters, file_reader.file_footer)

    if file_reader.ext == ".cine":
        print("file header :", file_reader.metadata)

    print("parameters : ", parameters)

    batch_size = parameters["batch_size"]
    batch_stride = parameters["batch_stride"]
    first_frame = parameters["first_frame"]
    end_frame = parameters.get("end_frame", 0)
    if end_frame <= 0:
        end_frame = file_reader.file_header.num_frames if file_reader.ext == ".holo" else file_reader.TotalImageCount

    if batch_stride >= (end_frame - first_frame):
        num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
    else:
        num_batch = int((end_frame - first_frame) / batch_stride)
    if num_batch <= 0:
        return None

    output = defaultdict(list)

    # Create CUDA streams
    h2d_stream = cp.cuda.Stream(non_blocking=True)
    d2h_stream = cp.cuda.Stream(non_blocking=True)
    compute_stream = cp.cuda.Stream(non_blocking=True)
    
    processed_batches = 0
    
    # Use simple double-buffering with explicit state
    d_current = None
    d_next = None
    h2d_event_current = None
    h2d_event_next = None
    
    # Start reading frames
    for i, frames in enumerate(tqdm(file_reader.iter_frames(
        first_frame=first_frame,
        end_frame = end_frame,
        batch_size=batch_size,
        batch_stride=batch_stride
    ), total=num_batch)):
        
        # Start async H2D transfer for this batch
        with h2d_stream:
            d_next = cp.asarray(frames)
            h2d_event_next = cp.cuda.Event()
            h2d_event_next.record(h2d_stream)
        
        # If we have a previous batch, wait for its H2D and compute it
        if d_current is not None:
            # Wait for H2D of current batch to complete
            h2d_event_current.synchronize()
            
            # Compute current batch on compute stream
            with compute_stream:
                res = _process_batch(parameters, d_current)
                compute_event = cp.cuda.Event()
                compute_event.record(compute_stream)
            
            # Wait for compute to finish
            compute_event.synchronize()
            
            if res is None:
                break
            
            for k, v in res.items():
                output[k].append(v)
            
            processed_batches += 1
        
        # Advance: next becomes current
        d_current = d_next
        h2d_event_current = h2d_event_next

    output = {k: cp.stack(v, axis=0) for k, v in output.items()}

    # transfer to cpu
    output_np = {k: cp.asnumpy(v) for k, v in output.items()}

    del output
    cp.get_default_memory_pool().free_all_blocks()

    output_np = {k: normalize_to_uint8(v) for k, v in output_np.items()}

    _save_videos( _get_default_output_path(file_reader.file_path) / "process", output_np, 30)
    
    