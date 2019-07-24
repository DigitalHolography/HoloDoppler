classdef CineSaver < handle
    %Manages the saving of a cine
    
    properties(Access = private)
        AttachedCine = [];
    end
    
    properties(SetAccess = private, SetObservable, AbortSet)
        Started;
        SaveProgress;
    end
    
    methods
        function cineSaveObj = CineSaver(cine)
            %A cine used for save should be used just in that context. The cine is cloned.
            cineSaveObj.AttachedCine = Cine(cine);
            cineSaveObj.Started = false;
            cineSaveObj.SaveProgress = 0;
        end
        
        function delete(this)
            if(~isempty(this.AttachedCine))
                this.AttachedCine.delete();
            end
        end
    end
    
    methods
        function result = ShowGetCineNameDialog(this)
            %Show dialog to select save cine path.
            %Updates internal cine handle buffer for file path and other various options.
            if (this.AttachedCine.IsLive)
                result = false;
            else
                %return true on OK button press.
                result = this.AttachedCine.GetSaveCineName();
            end
        end
        
        function result = StartSaveCine(this)
            if (this.Started || this.AttachedCine.IsLive)%Live cine cannot be saved.
                result = false;
                return;
            end
            
            this.Started = true;
            %set the usecase for save
            this.AttachedCine.SetUseCase(PhFileConst.UC_SAVE);
            this.AttachedCine.StartSaveCineAsync();
            result = true;
        end
        
        function StopSave(this)
            this.AttachedCine.StopSaveCineAsync();
        end
        
        function UpdateSaveStatus(this)
            %Updates the cine save status. Call this on a timer.
            if(this.Started)
                [HRES this.SaveProgress] = this.AttachedCine.GetSaveCineFileProgress();
                if (this.SaveProgress == 100 || HRES<0)
                    this.Started = false;
                end
            end
        end
    end
    
end

