            % update cache parameters
            % save all gui parameters to a struct.
            % The current computation will fetch every parameter
            % from the cache and not from the gui.
            % The purpose of this is to prevent gui interactions
            % to mess up the parameters while a computation is ongoing.
            app.create_cache();