# list of sim name and paths for SimInterface platform controller
# sim module is the name of the python module defining the desired Sim class
# a jpg file with the same name as the module will be displayed when selected 

default_sim = 4 # combo box will be set the this value at startup

available_sims = [  #   display name, sim module
                    [ "Microsoft fs2020", "fs2020"],
                    ["X-Plane 11", "xplane"],                        
                    ["Space Coaster", "spacecoaster"],
                    ["NoLimits2 Coaster", "nolimits2"],
                    ["DCS", "dcs"]
                    # add another sim here
                    ]