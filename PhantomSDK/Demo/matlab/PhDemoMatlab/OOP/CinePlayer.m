classdef CinePlayer < handle
    %Class manages image acquisition and displaying of the current cine
    
    properties(Access = private)
        CurrentCine = [];
        CurrentImageBufferSize = 0;
        CurrentImgHeader = [];
    end
    
    properties(SetAccess = private)
        CurrentImagePixels = [];
    end
    
    properties(SetAccess = private, SetObservable, AbortSet)
        FirstIm;
        LastIm;
        IsPlaying;
        
        IsColorImage;
        Is16bppImage;
    end
    
     properties(SetObservable, AbortSet)
        CurrentFrame;
     end

    %% Constructor
    methods
        function cinePlayerObj = CinePlayer()
        end
    end
    
    %% Methods
    methods (Access = private)
        function SetPlayRange(this, first, last)
            this.FirstIm = first;
            this.LastIm = last;
        end
        
        function InitPlayRange(this, first, last)
            this.StopPlay();
            
            this.SetPlayRange(first, last);
            this.CurrentFrame = first;
        end
        
        function NextFrame(this)
            if(isempty(this.CurrentCine) || this.CurrentCine.IsLive)
                return;
            end
            
            crtFrame = this.FirstIm;
            if (this.CurrentFrame ~= this.LastIm)
                crtFrame = this.CurrentFrame+1;
            end
            this.CurrentFrame = crtFrame;
        end

        function SetImageBufferSize(this, imgSizeInBytes)
            %alocate image buffer as needed
            if ((imgSizeInBytes ~= this.CurrentImageBufferSize))
                %free old buffer
                if (~isempty(this.CurrentImagePixels))
                    this.CurrentImagePixels = [];
                end
                this.CurrentImageBufferSize = imgSizeInBytes;
            end
        end
    end
    
    methods
        function SetCurrentCine(this, cine)
            this.CurrentCine = cine;
            if (~isempty(this.CurrentCine))
                if (this.CurrentCine.IsLive)
                    this.InitPlayRange(0, 0);%live cine has no image range, always take image 0
                    this.StartPlay();%always show live images
                else
                    this.InitPlayRange(this.CurrentCine.GetFirstImageNumber(), this.CurrentCine.GetLastImageNumber());
                end
                
                %GetCineImage image flip is inhibated.
                this.CurrentCine.SetVFlipView(false);
                this.RefreshImageBuffer();
            else
                this.StopPlay();
            end
        end
        
        function StartPlay(this)
            this.IsPlaying = true;
        end
        
        function StopPlay(this)
            this.IsPlaying = false;
        end
        
        function PlayNextImage(this)
            if(this.IsPlaying)
                this.RefreshImageBuffer();
                this.NextFrame();
            end
        end
        
        function RefreshImageBuffer(this)
            %get the image from camera and updates the displayed image buffer
            if (isempty(this.CurrentCine))
                return;
            end
            
            imgRange = get(libstruct('tagIMRANGE'));
            imgRange.First = this.CurrentFrame;
            imgRange.Cnt = 1;
            %get cine image buffer size
            imgSizeInBytes = this.CurrentCine.GetMaxImageSizeInBytes();
            
            this.SetImageBufferSize(imgSizeInBytes);
            
            %read cine image into the buffer
            [HRES, this.CurrentImagePixels, imgHeader] = this.CurrentCine.GetCineImage(imgRange, imgSizeInBytes);
            
            %transform image pixels to be disaplyed in MATLAB figure
            if (HRES >= 0)
                [this.CurrentImagePixels] = ExtractImageMatrixFromImageBuffer( this.CurrentImagePixels, imgHeader );
                this.IsColorImage = IsColorHeader(imgHeader);
                this.Is16bppImage = Is16BitHeader(imgHeader);
                if (this.IsColorImage)
                    samplespp = 3;
                else
                    samplespp = 1;
                end
                bps = GetEffectiveBitsFromIH(imgHeader);
                [this.CurrentImagePixels, unshiftedImg] = ConstructMatlabImage(this.CurrentImagePixels, imgHeader.biWidth, imgHeader.biHeight, samplespp, bps);
            end
        end
    end
end

