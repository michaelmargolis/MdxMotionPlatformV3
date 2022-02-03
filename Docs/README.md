# Platform Software Overview

### software architecture:
![Architecture v3](https://github.com/michaelmargolis/MdxMotionPlatformV3/blob/master/Docs/Software_architecture.png)
+   The system consists of one or more Vr PCs running a motion simulator, each network connected to a controller computer running the platform software.
+   Vr pcs run an ‘Agent’ that represents the sim to the controller by converting sim specific commands, telemetry and state events to the system defined msg format.
+   After an Agent and its sim have been started, the controller converts the telemetry received from the agent into real world platform coordinates for controller the platform orientation.
+   Motion sims are expected to remain in sync for duration of ‘ride’ but currently this is not enforced.

    
<p></p>
![agent example v3](https://github.com/michaelmargolis/MdxMotionPlatformV3/blob/master/Docs/Example_agent.png)
### Typical agent detail (space_coaster):