# Motion tracking suite for QTM based tracking systems

## QTM module

### motionGui.py
Allows for c3d and npy data files to be imported and displayed.
*  Fully animated view of data
*  Frame start and end sliders to select subsections of animation
*  Point selection and linking
*  Importing of custom data analysis and manipulation scripts
*  Saves animation shown in data visualizer to file

### streamGui.py
*  Streams data directly from QTM instance
*  Also allows for importing of custom scripts
*  Allows data to be recorded and exported in .npy data format suitable for motionGui.py
*  Can connect to any QTM instance on the same network who's IP address you know

### Required Libraries:

* PyQt5  
* PyQtGraph  
* PyOpenGL  
* numpy  
* c3d  
* qtm

## Optical Flow module

### controlPanel.py
* Performs optic flow analysis on both webcam and video file input
* Lets you pause current video/webcam data for better positioning of test regions
* Allows for experimental motion tracking of the test regions

### Settings window
* Allows you to enable a fps timer for video output
* Lets you control the number of resolution elements in each dimension to be used for the optic flow. In general a higher number of elements gives a more accurate depiction of the object being tracked.

### Required Libraries
* Numpy
* cv2
* pyqt5
* matplotlib
* c3d

### How to use
1. Make sure all required libraries are installed (see above)
2. Run controlPanel.py
3. Click "Show Video" if using webcam input, or "Load Video" if loading from an existing file to open the video output and optic flow screens.
4. Click and drag on the video output screen to define test region bounds. These can be renamed by double clicking on their name in the listbox.
5. Start optic flow analysis by clicking "Start Test" on the control panel. This requires at least 1 region to be defined and prevents the creation of further test regions during the testing period.
6. Once testing is completed, click "Stop Test". You'll be prompted to save a video file of the raw footage from the test period. This is stored at the average fps over the testing period
7. Phase information and optic flow magnitude is then displayed
