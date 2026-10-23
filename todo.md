# Things to do for repo architecture :

- Change code basse structure : 
    move holodoppler/ to src/

- code base structure wanted : 
    execution/ -> runner.py  and context.py (progress bar) and backend.py -> cupy numpy switch depending on what is available on the machine (done)
    saving/ -> saving format and writer functions (done)
    config/ -> config class 
    ui/
    logger.py -> init logger(done)
    get_version.py -> soft version and git version(done)

    pipelines/ -> pipeline definitions calling into core/ and saving/ and config/(done)

    __main__.py(done)
    __init__.py(done)

    readers/ unified FileReader class and sub HoloFileReader and CineFileReader classes (done)

- remove the sh_avg pipeline and spectrograms as they now fall into default (done)

- remove the parameters contrast everywhere (its not used)

- ui/ and logger
    merge the ui/ into the rest of the app especially for the logging system into Appdata (difficult)
    rename the appdata slug holodopplerpython to HoloDoppler
    fix ui jittering when switching between minimal and advanced panels

- default pipeline improvements:
    - always use parameters.get(...) defaults

    - add a plot image of the computed autofocus shifts and phase_map :)
