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

- remove the sh_avg pipeline and spectrograms as the now fall into default

- remove the parameters contrast everywhere (its not used)

- ui/ and logger
    merge the ui/ into the rest of the app especially for the logging system into Appdata (difficult)
    rename the appdata slug holodopplerpython to HoloDoppler
    fix ui jittering when switching between minimal and advanced panels

- default pipeline improvements:
    - always use parameters.get(...) defaults

    - add a plot image of the computed autofocus shifts and phase_map :)
