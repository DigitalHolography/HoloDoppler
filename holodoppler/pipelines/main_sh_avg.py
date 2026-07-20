from holodoppler.saving import save_preview_images, _get_default_output_path, _save_videos, _save_h5_2, _create_directories, _save_pngs, _save_metadata
from holodoppler.propagation import fresnel_transform, fresnel_transform_with_phase, angular_spectrum_transform, angular_spectrum_transform_with_phase
from holodoppler.shack_hartmann import construct_subapertures_fresnel, construct_subapertures_angular, calculate_displacements, calculate_displacements_graph_laplacian
from holodoppler.zernike import fit_zernike_fresnel, fit_zernike_angular_spectrum
from holodoppler.utils import gaussian_flatfield, update_from_footer, normalize_to_uint8, square_cupy, stretchlim, imadjust, temporal_gaussian
from holodoppler.filtering import svd_filter, frequency_symmetric_filtering, fourier_time_transform, corner_compensation
from holodoppler.moments import moment
from holodoppler.registration import register_images_shifts, apply_register_images_shifts
from holodoppler.file_reader import FileReaderFactory

import cupy as cp
from cupyx.scipy.ndimage import gaussian_filter
from tqdm import tqdm
from pathlib import Path
from collections import defaultdict
import time

def _process_batch(parameters, frames, phase_term = None, output_dict = None):
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

    if output_dict is None:
        output_dict = {}

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

    output_dict["psd"] = psd

    if parameters.get("corner_compensation", False):
        psd = corner_compensation(xp, psd)

    # Moments
    output_dict["M0"] = moment(xp, psd[idxs], freqs, 0)
    output_dict["M0ff"] = gaussian_flatfield(output_dict["M0"], parameters.get("registration_flatfield_gw", 1.0), gaussian_filter)


def _process_shack_hartmann(parameters, frames, output_dict = None):
    fft = cp.fft
    nt, ny, nx = frames.shape
    prop_method = parameters["spatial_propagation"]
    
    if prop_method == "Fresnel":
        U = construct_subapertures_fresnel(
            cp, fft, frames, parameters["wavelength"], parameters["z"], parameters["pixel_pitch"],
            parameters["low_freq"], parameters.get("high_freq"), parameters["sampling_freq"],
            frames.shape[0], parameters["shack_hartmann_nx_subap"], parameters["shack_hartmann_ny_subap"],
            parameters["shack_hartmann_svd_threshold"]
        )
    elif prop_method == "AngularSpectrum":
        U = construct_subapertures_angular(
            cp, fft, frames, parameters["wavelength"],
            parameters["z"], parameters["pixel_pitch"], parameters["low_freq"], parameters.get("high_freq"),
            parameters["sampling_freq"], frames.shape[0], parameters["shack_hartmann_nx_subap"],
            parameters["shack_hartmann_ny_subap"], parameters["shack_hartmann_svd_threshold"]
        )

    # Displacement estimation
    if parameters.get("shack_hartmann_graph_laplacian", False): 
        shifts_y, shifts_x = calculate_displacements_graph_laplacian(
            cp, fft, U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
            shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0)
        )
    else: 
        shifts_y, shifts_x = calculate_displacements(
            cp, fft, U,
            pupil_threshold=parameters.get("shack_hartmann_pupil_threshold", 1.0),
            deviation_threshold=parameters.get("shack_hartmann_deviation_threshold", 3.0),
            shifts_range=parameters.get("shack_hartmann_shifts_pixel_range_threshold", 20.0)
        )

    if output_dict is not None:
        sy, sx, numy, numx = U.shape
        U = cp.transpose(U, axes=(0,2,1,3))
        output_dict["shack_hartmann_sub_images"] = cp.reshape(U,(numy*sy,numx*sx))

    del U, frames  # Memory footprint reduction

    # Phase reconstruction
    phase = None
    if parameters.get("shack_hartmann_zernike_fit", True):
        if prop_method == "Fresnel":
            coefs, phase = fit_zernike_fresnel(
                cp, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )
        elif prop_method == "AngularSpectrum":
            coefs, phase = fit_zernike_angular_spectrum(
                cp, ny, nx, parameters["pixel_pitch"][0], parameters["pixel_pitch"][1],
                parameters["wavelength"], parameters["z"], shifts_y, shifts_x, parameters.get("shack_hartmann_zernike_fit_modes")
            )
        if output_dict is not None:
            output_dict["shack_hartmann_zernike_coefs"] = coefs
            output_dict["shack_hartmann_wavefront_phase"] = phase

    # Phase correction term
    phase_term = None
    if phase is not None:
        phase_term = cp.exp(-1j * phase)
        phase_term = cp.nan_to_num(phase_term, nan=0.0)

    return phase_term


def preview(file_path, parameters):
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
    
    frames = cp.array(frames, dtype=cp.float32)
    res = {}
    phase_term = None
    if parameters.get("shack_hartmann", False):
        phase_term = _process_shack_hartmann(parameters, frames, output_dict=res)

    _process_batch(parameters, frames = frames, phase_term = phase_term, output_dict=res)
    res_np = {k: cp.asnumpy(v) for k, v in res.items()}

    del res
    cp.get_default_memory_pool().free_all_blocks()

    target_dir = _get_default_output_path(file_reader.file_path) / "preview" / "SH_AVG"
    (target_dir / "h5").mkdir(parents=True, exist_ok=True)
    save_preview_images(res_np, target_dir, square=parameters["square"])
    _save_h5_2(target_dir, res_np, parameters)


def process(file_path, parameters):
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
    M0_reg = None

    # Create CUDA streams
    h2d_stream = cp.cuda.Stream(non_blocking=True)
    compute_stream = cp.cuda.Stream(non_blocking=True)
    
    processed_batches = 0
    d_current = None
    d_next = None
    h2d_event_current = None
    h2d_event_next = None
    psd_tot = None
    
    for i in tqdm(range(num_batch + 1)):
        # 1. Chargement asynchrone du lot SUIVANT
        if i < num_batch:
            with h2d_stream:
                frames = file_reader.read_frames(first_frame = first_frame + i * batch_stride, batch_size = batch_size)
                d_next = cp.asarray(frames)
                h2d_event_next = cp.cuda.Event()
                h2d_event_next.record(h2d_stream)
        else:
            d_next = None
            h2d_event_next = None
        
        # 2. Calcul du lot COURANT
        if d_current is not None:
            h2d_event_current.synchronize()
            
            with compute_stream:
                res = {}
                phase_term = None
                if parameters.get("shack_hartmann", False):
                    phase_term = _process_shack_hartmann(parameters, d_current, output_dict=res)

                _process_batch(parameters, d_current, phase_term=phase_term, output_dict=res)

                if M0_reg is None and parameters["image_registration"]:
                    M0_reg = res["M0ff"]
                
                if M0_reg is not None:
                    shift_y, shift_x = register_images_shifts(cp, cp.fft, M0_reg, res["M0ff"], radius=0.8, gaussian_sigma=3, gaussian_filter=gaussian_filter)
                    
                for k, v in res.items():
                    if k in ["M0ff","M0","M1","M2", "psd"] or "band_" in k :
                        res[k] = apply_register_images_shifts(cp, v, shift_y, shift_x)

                res["registration"] = cp.stack([cp.array(shift_y), cp.array(shift_x)])

                if psd_tot is None:
                    psd_tot = res["psd"]
                else: 
                    psd_tot += res["psd"]

                del res["psd"]  # Évite la saturation mémoire GPU

                compute_event = cp.cuda.Event()
                compute_event.record(compute_stream)
            
            compute_event.synchronize()
            
            if res is None:
                break
            
            for k, v in res.items():
                output[k].append(v)
            
            del res
            processed_batches += 1
        
        # Avancement dans le pipeline double-buffer
        d_current = d_next
        h2d_event_current = h2d_event_next

    output = {k: cp.stack(v, axis=0) for k, v in output.items()}
    output["psd"] = psd_tot

    if parameters.get("square", False):
        output = {k: square_cupy(v) if v.ndim >=3 else v for k, v in output.items()}

    output_np = {k: cp.asnumpy(v) for k, v in output.items()}
    del output
    cp.get_default_memory_pool().free_all_blocks()

    target_dir = _get_default_output_path(file_reader.file_path) / "SH_AVG"
    if "saving_to_folder" in parameters:
        target_dir = Path(parameters["saving_to_folder"])

    _create_directories(target_dir, "FULL")
    _save_h5_2(target_dir, output_np, parameters)

    start_time = time.time()

    # CORRECTION : On identifie uniquement les clés qui contiennent de vraies images/spectres
    image_keys = [k for k in output_np.keys() if k in ["M0", "M0ff", "M1", "M2", "psd"] or "band_" in k]

    if parameters.get("smoothing_gaussian", False):
        smoothing_gaussian_size =  parameters.get("smoothing_gaussian_size", 2)
        for k in image_keys: # <--- Uniquement sur de vraies images
            output_np[k] = temporal_gaussian(output_np[k], sigma=smoothing_gaussian_size)

    elapsed = time.time() - start_time
    print(f"smoothing_gaussian in {elapsed:.1f} seconds")

    start_time = time.time()
    
    if parameters.get("contrast", False):
        low_pct, high_pct = parameters.get("contrast_low_max_percent", (1.0,99.0))
        gamma = parameters.get("contrast_gamma", 1.0)
        for k in image_keys: # <--- Uniquement sur de vraies images
            low, high = stretchlim(output_np[k], low_pct, high_pct)
            output_np[k] = imadjust(output_np[k], low, high, gamma)
            output_np[k] = normalize_to_uint8(output_np[k])
    else:
        for k in image_keys: # <--- Uniquement sur de vraies images
            output_np[k] = normalize_to_uint8(output_np[k])
    
    elapsed = time.time() - start_time
    print(f"contrast in {elapsed:.1f} seconds")
    
    _save_videos(target_dir, output_np, 30)
    _save_pngs(target_dir, output_np)
    _save_metadata(target_dir, file_reader, parameters)

    # Zone Analysis automatique réintégrée et corrigée
    print('test "analyse_zone_points":', "analyse_zone_points" in parameters and parameters["analyse_zone_points"], parameters.get("analyse_zone_points"))
    if "analyse_zone_points" in parameters and parameters["analyse_zone_points"]:
        print("\n[Zone Analysis] Début du calcul du PSD moyen automatique...")
        try:
            import h5py
            import numpy as np
            from matplotlib.path import Path as MPath
            
            h5_files = list(target_dir.rglob("*.h5"))
            
            if not h5_files:
                print("[Zone Analysis] ⚠️ Aucun fichier .h5 trouvé dans", target_dir)
            else:
                chemin_h5 = h5_files[0]
                mes_4_points = parameters["analyse_zone_points"]
                print(f"[Zone Analysis] Fichier détecté : {chemin_h5.name}")
                
                with h5py.File(chemin_h5, 'a') as f:
                    nom_matrice_ref = None
                    # CORRECTION : On cherche M0 ou psd en premier (pas sh_avg qui est une chaîne texte)
                    for cle in ['M0', 'M0ff', 'psd', 'M1', 'M2', 'Projection', 'Projectionff']:
                        if cle in f:
                            nom_matrice_ref = cle
                            break
                    
                    if nom_matrice_ref is None:
                        cles_dispo = list(f.keys())
                        nom_matrice_ref = cles_dispo[0] if cles_dispo else None
                    
                    if not nom_matrice_ref:
                        print("[Zone Analysis] ⚠️ Impossible de déterminer la géométrie du fichier H5.")
                    else:
                        ref_data = f[nom_matrice_ref][:]
                        image_2d = np.mean(ref_data, axis=0) if ref_data.ndim == 3 else ref_data
                        ny, nx = image_2d.shape
                        
                        x, y = np.meshgrid(np.arange(nx), np.arange(ny))
                        pixels_np = np.vstack((x.flatten(), y.flatten())).T
                        chemin_polygone = MPath(mes_4_points)
                        masque_np = chemin_polygone.contains_points(pixels_np).reshape((ny, nx))
                        
                        nom_matrice_psd = None
                        # CORRECTION : Priorité absolue à 'psd' (en minuscules)
                        candidates = ['psd', 'PSD', 'Spectrum', 'spectrum', 'STFT', 'stft', 'Spectrum3D']
                        for cle in candidates:
                            if cle in f:
                                nom_matrice_psd = cle
                                break
                        
                        if nom_matrice_psd is None:
                            for cle in f.keys():
                                if 'psd' in cle.lower() or 'spec' in cle.lower() or 'stft' in cle.lower() or 'avg' in cle.lower():
                                    nom_matrice_psd = cle
                                    break
                        
                        if nom_matrice_psd is None:
                            print(f"[Zone Analysis] ⚠️ Matrice de PSD non trouvée. Clés dispo : {list(f.keys())}")
                        else:
                            print(f"[Zone Analysis] Matrice de PSD détectée : '{nom_matrice_psd}'")
                            psd_data = f[nom_matrice_psd][:]
                            
                            if psd_data.ndim == 3:
                                if psd_data.shape[1] == ny and psd_data.shape[2] == nx:
                                    pixels_dans_zone = psd_data[:, masque_np]
                                    psd_moyen = np.mean(pixels_dans_zone, axis=1)
                                elif psd_data.shape[0] == ny and psd_data.shape[1] == nx:
                                    pixels_dans_zone = psd_data[masque_np, :]
                                    psd_moyen = np.mean(pixels_dans_zone, axis=0)
                                else:
                                    print(f"[Zone Analysis] ❌ Taille PSD {psd_data.shape} incompatible avec l'image {ny}x{nx}")
                                    psd_moyen = None
                            elif psd_data.ndim == 2:
                                psd_moyen = np.mean(psd_data[masque_np])
                                print(f"[Zone Analysis] Note : Le PSD est en 2D, calcul d'une moyenne scalaire.")
                            else:
                                print(f"[Zone Analysis] ❌ Dimension de PSD non supportée ({psd_data.ndim}D)")
                                psd_moyen = None
                            
                            if psd_moyen is not None:
                                grp = f.require_group("Analyses_Zones")
                                
                                nom_masque = "Zone_1_Masque"
                                if nom_masque in grp: del grp[nom_masque]
                                grp.create_dataset(nom_masque, data=masque_np.astype(np.uint8))
                                
                                nom_psd_dataset = "Zone_1_PSD_Moyen"
                                if nom_psd_dataset in grp: del grp[nom_psd_dataset]
                                dataset_psd = grp.create_dataset(nom_psd_dataset, data=psd_moyen)
                                
                                dataset_psd.attrs["coordonnees_points"] = str(mes_4_points)
                                dataset_psd.attrs["source_calcul"] = nom_matrice_psd
                                dataset_psd.attrs["description"] = "Courbe 1D de la densite spectrale de puissance moyenne (PSD) dans la zone"
                                
                                print(f"[Zone Analysis] ✅ PSD Moyen injecté avec succès ('{nom_psd_dataset}') dans {chemin_h5.name} !")
                                
        except Exception as e:
            print(f"[Zone Analysis] ❌ Erreur lors du calcul du PSD : {e}")