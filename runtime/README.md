# Python Motion Platform Controller Version 3
This software enables a motion simulator or other client to control movement of the Middlesex University motion platform.

### Installation
Install the software by copying all the files in the runtime directory to your PC.  The software can run in any directory and no registry entries are needed. Install Python 2.7 if not already installed. The software is python 3.x compatible but has not been extensively tested in that environment.
Python numpy and pyqt5 modules are required.

### Software Overview
All activity is driven from the controller module through service calls that poll the client every 50 milliseconds. The client responds with orientation requests and/ or system commands. Orientation requests are in the form surge, sway, heave, roll, pitch, and yaw. These can be either real world values (mm and radians) or normalized values (values between -1 and 1 representing the maximum range of movement of the platform for each degree of freedom).

Note that the system needs most of the 50ms interval between service requests to calculate and drive the output; therefore the client must return promptly from the service calls. If necessary, the client can use the threaded client example as a model to decouple client processing from the system service routine.

### Changes from previous version
This version uses pyqt5 instead of tkinter for the user interface

The new 'flying' platform is supported in addition to the existing chairs

Client classes are derived from client_api module