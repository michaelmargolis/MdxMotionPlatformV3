# Platform Software Overview

### Software architecture:
![Architecture v3](https://github.com/michaelmargolis/MdxMotionPlatformV3/blob/master/Docs/Software_architecture.png)
*   The system consists of one or more Vr PCs running a motion simulator, each network connected to a controller computer running the platform software.
*   Vr pcs run an ‘Agent’ that represents the sim to the controller by converting sim specific commands, telemetry and state events to the system defined msg format.
*   After an Agent and its sim have been started, the controller converts the telemetry received from the agent into real world platform coordinates for controller the platform orientation.
*   Motion sims are expected to remain in sync for duration of ‘ride’ but currently this is not enforced.

### Control flow:
![Control flow](https://github.com/michaelmargolis/MdxMotionPlatformV3/blob/master/Docs/platform_flow.animation.gif)
 
### Typical agent detail (space_coaster):
![agent example v3](https://github.com/michaelmargolis/MdxMotionPlatformV3/blob/master/Docs/Example_agent.png)


### Software file overview:
* runtime directory
  * platform_controller.py - This script exectutes the runtime code on the controller PCs
    * system_config.py - Contains platform selection (suspended chair or sliding actuator) and network address defines  
  * agent_startup.py - This script must be run on each PC supporting a motion sim and associated agent
  * PlatformTest.py - A utility to move the platform to check operatiodnal status

* agents directory
  * nolimits_coaster directory - files for running the NoLimits2 roller coaster simulator
  * space_coaster directory- files for the space coaster ride’
  * test_agent directory - a GUI tester for directly driving the platforms translations and rotations
  * core agent class definitions
    * agent_base.py - Base class for all agents
    * agent_gui_base.py - Base class for all agent GUIs
    * ride_state.py - Represents the high level state of the motion sim, each sim maps its internal ride state to these
    * agent_select_dialog - a GUI used by the platform_controller to select the sim to run
      * agent_config.py - contains the agent details used by the select dialog
    * agent_proxy.py - Provides the interface between controller the the agents running on remote PCs
    
* kinematics directory
  * kinematicsV2.py - Inverse kinematics for the Mdx motion platforms
  * dynamics.py - Code to adjust dynamic range and washout 
  * cfg_SuspendedChair.py - kinematic defines for the suspended chair
  * cfg_SlidingActuators.py - kinematic defines for the sliding actualtor platform
  
* output directory
  * muscle_output.py - Converts kinematic requests to pressure values for driving the platform actuators
    * d_to_p.py - code to intrepolate table of distance to pressure values for the platforms range of loads
    * DtoP.csv - distance to pressure data tables used by the above
    * festo_itf.py - interface to the Festo PLC (uses code in fstlib directory)
    
* common directory
  * various low level files for interfacing with network and serial components
  
* SimpleSims directory
  * SimInterface.py - A simpler controller for testing integration with new motion sims