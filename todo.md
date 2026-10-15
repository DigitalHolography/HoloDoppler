# Things to do for repo architecture :

- Change code basse structure : 
    move holodoppler/ to src/

- code base structure wanted : 
    execution/ -> runner.py  and context.py (progress bar) and backend.py -> cupy numpy switch depending on what is available on the machine
    saving/ -> saving format and writer functions
    config/ -> config class 
    ui/
    logger.py -> init logger
    get_version.py -> soft version and git version

    pipelines/ -> pipeline definitions calling into core/ and saving/ and config/

    __main__.py
    __init__.py

    readers/ unified FileReader class and sub HoloFileReader and CineFileReader classes

- remove the direct calls from core.filtering and core.image_utils to backend (use xp and other modules in function signatures)

- remove the sh_avg pipeline and spectrograms as the now fall into default

- remove the parameters contrast everywhere (its not used)

- ui/ and logger
    merge the ui/ into the rest of the app especially for the logging system into Appdata (difficult)
    rename the appdata slug holodopplerpython to HoloDoppler
    fix ui jittering when switching between minimal and advanced panels

- default pipeline improvements:

    - Fix batch counting and boundary handling: num_batch = int(span / batch_stride) can be wrong and lead to incomplete batch (if batch_stride =/ batch size) this ead to read failures so avoid it. Use a single helper to calculate batch indices and validate batch_size, batch_stride, and frame boundaries.
    - defaultdict(list) followed by np.stack() temporarily duplicates output memory. Use preallocation when output shapes are known
    - avoid retaining intermediate arrays longer than necessary, particularly spectrum_f, psd, and propagated holograms
    - Unify _process_numpy, _process_numpy_parallel, and _process_cupy (difficult)
    - remove dead code (Fresnel_use_ouput_kernel and zero_padding)
    - always use parameters.get(...) defaults
    - define the pipeline parameters in a validate_parameters() function to check and fill with defaults values if needed.

    - add a plot image of the computed autofocus shifts and phase_map :)
    - add an autofocus batch_size parameter !