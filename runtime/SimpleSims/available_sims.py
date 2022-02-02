# list of sim name and paths for SimInterface platform controller
# sim module is the name of the python module defining the desired Sim class
# a jpg file with the same name as the module will be displayed when selected 

default_sim = 5 # combo box will be set the this value at startup
Desktop = r"C:/Users/memar/Desktop/Vr/" # location of startup icons (usually C:/Users/name/Desktop/ )
print(Desktop)

available_sims = [  #   display name, sim module name, full path to execute to load sim
                    [ "Microsoft fs2020", "fs2020", "M:/MSFS SDK/Tools/bin/fsdevmodelauncher.exe"],
                    ["X-Plane 11", "xplane", Desktop + "X-Plane.lnk"] ,                        
                    ["Space Coaster", "spacecoaster", Desktop + "SpaceCoaster.lnk"],
                    ["NoLimits2 Coaster", "nolimits2", Desktop + "NoLimits 2.lnk"],
                    ["DCS", "dcs", Desktop + "DCS World.lnk"],
                    ["Test Sim", "TestSim", None]
                    # add another sim here
                    ]