HoloDoppler. www.holodoppler.com

collection of Matlab routines for time fluctuation analysis of holographic images.

standalone graphical user interface, executable file made with Matlab runtime environment.

## Dependencies & Requirements

- A valid MATLAB license is required to run HoloDoppler.
- A very performant computer is required to run HoloDoppler. 
- Parallel Computing Toolbox
- Curve Fitting Toolbox
- Signal Processing Toolbox
- Image Processing Toolbox

## Different types of output

- power Doppler : moment 0 image of the SH fluctuation spectrum with gaussian flatfield applied
- moments 0, 1 and 2 : raw moments of the SH fluctuation spectrum needed for the eyeflow retinal analysis

## How to use Batch processing (v2.3)

1. Load a first file .holo or .cine and look at the rendering of the first frame in the preview
2. If you are satisfied with the result you can use folder management to process multiple files
3. In folder management you can select individual files or all the files from a folder
4. You can save the current config to all the files displayed in the folder management window by checking "apply to all files". In .holo rendering you leave "keep z distance" unchecked.
   ( You can check "keep z" if you want in case of .cine file rendering because they do not contain the z (focus) distance )
5. In . cine mode you should do the previous step for all measurement having different z propagation distance but in .holo it will use the one saved in the .holo file.
6. Once all the files you want have a specific json config file. Select them all in the Folder management and hit Render.
