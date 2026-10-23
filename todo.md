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

- remove the parameters contrast everywhere (its not used)

- ui/ and logger
    fix ui jittering when switching between minimal and advanced panels

- default pipeline improvements:
    make autofocus faster in numpy only mode (single thread for the shack hartmann is really slow)
    make a registration more relyable based on sub batches of 64 frames accumulated (goal better registration on edge cases)
    make an averaging pipeline implementing a sliding average for all the outputs (goal less rendered image noise)
    implement a welch option to estimate the psd more relyably working on sub batches with optionnal widowing with less frequency resolution

    in general work on execution speed and memory efficiency

- improve the shack hartmann pipeline with more parameters espcecially work on an efficient sliding shack hartmann sub apertures implementation.
