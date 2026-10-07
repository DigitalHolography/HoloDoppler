# Things to do for repo architecture :

- Change code basse structure : 
    move holodoppler/ to src/

- rework the build installer

- code base structure wanted : 
    core/ -> core operations useful functions
    execution/ -> runner.py  and context.py (progress bar) and backend.py -> cupy numpy switch depending on what is available on the machine
    saving/ -> saving format and writer functions
    config/ -> config class 
    ui/
    logger.py
    get_version.py -> soft version and git version

    pipelines/ -> pipeline definitions calling into core/ ans saving/ and config/

    cli/

    __main__.py
    __init__.py

    readers/ unified FileReader class and sub HoloFileReader and CineFileReader classes

