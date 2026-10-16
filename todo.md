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

- big next step : decompose the processing of batchs into sub batchs on which we can compute pca (or svd) and filter from thes small time windows filters
: but also perform a more general sliding and averaging of the computations


- write some more documentation

- saving.py 
    - option to write ouput in a certain path
    - add the name of the aquisition in the output files names
    - add the names option to save from the dict output into the h5
    - simply remove fps for now just use a default value parametrizable
    - make code options
    - make .mp4 .avi ouput otions

- ref option pour sh et reg

- Feat : use the holo timings of each frames to compensate camera jitter during the time fft (camera jitter noise reduction)

- Make an option to have multiple passes (for example calc registration and shack hartmann on the first then apply a sub batch registration and or correction of phase 

Add a Franhaufer only transform
Feature add accumulation in a reasonable way 
Maybe push to the accumulation different for each queue
Feature test to do SVD filter after the frequency filtering by ifft (with zeros where frequency is filtered) then svd filter then fft back and fft filter again)
Add option in the shack_hartmann : fft or PCA and the frequency of filtering 
Add possibility to do not every cross correlation in graph_laplacian
Add possibility to calculate the local zernike coeffs (map)

Feat parameter for legendre polynomials
Add a complete logger to log every action and a DEBUG mode of the logger

Profiling in all cases into a profile_log.txt

Add an option to do different pipelines for full field oct for example or for iterative calculations
USE FFMPEG FOR THE VIDEO SAVINGS THAT SHOULD BE WAY FASTER and DIB (uncompressed)  codec
Handle the output arrays differently if they are images or coeffs arrays or pixel or registration etc. do this through a class and for images habdle if they are average of a video gray or color need to be rescaled / resized to square or not need to undergo a special post processing step etc…

