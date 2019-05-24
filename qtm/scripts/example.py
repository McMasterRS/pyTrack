class example():
    def __init__(self):
        self.name = "example"
        
    def parseData(self, data = None):
        
        # Example data manipulation/analysis script
        #
        # Input: A single frame of data containing the coordinates
        #        of all tracked points in the frame.
        #
        # Output: A modified array of data in an identical format to the input
        #
        # Format: 1xN numpy array of 3x1 numpy arrays containing coordinates in (x, y, z) order. 
        #
        # This example function simply inverts the x and y positions of all particles in the frame
     
        for i in range(0, len(data)):
            data[i] = (-1 * data[i][0], -1 * data[i][1], data[i][2])
        
        return data