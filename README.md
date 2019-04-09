# Motion tracking suite for QTM based tracking systems

## motionGui.py
Allows for c3d and npy data files to be imported and displayed.
*  Fully animated view of data
*  Frame start and end sliders to select subsections of animation
*  Point selection and linking
*  Importing of custom data analysis and manipulation scripts
*  Saves animation shown in data visualizer to file

## streamGui.py
*  Streams data directly from QTM instance
*  Also allows for importing of custom scripts
*  Allows data to be recorded and exported in .npy data format suitable for motionGui.py
*  Can connect to any QTM instance on the same network who's IP address you know

## Required Libraries:

* PyQt5  
* PyQtGraph  
* PyOpenGL  
* numpy  
* c3d  
* qtm
