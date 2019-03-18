import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import numpy as np
import c3d
import qtm
import asyncio

from motionGui import MotionGui

class MotionLoad:

    def __init__(self, master):
        
        self.master = master
        self.data = []
        
        self.inputFrame = tk.Frame(master)
        self.inputFrame.pack()
        
        self.inputFile = tk.Entry(self.inputFrame, width = 50)
        self.inputFile.pack(expand = 1, fill = 'x', side = tk.LEFT, padx = 2, pady = 0)
        
        self.openBt = tk.Button(self.inputFrame, text = "Load", width = 12, command = self.openFile)
        self.openBt.pack(expand = 0, side = tk.LEFT, anchor = tk.W, padx = 2, pady = 0)
        
        self.streamFrame = tk.Frame(master)
        self.streamFrame.pack()
        
        self.streamIP = tk.Entry(self.streamFrame, width = 50)
        self.streamIP.pack(expand = 1, fill = 'x', side = tk.LEFT, padx = 2, pady = 0)
        
        self.streamBt = tk.Button(self.streamFrame, text = "Stream", width = 12, command = self.streamData)
        self.streamBt.pack(expand = 0, side = tk.LEFT, anchor = tk.W, padx = 2, pady = 0)
        
    def openFile(self):
        fl = filedialog.askopenfilename()
        if fl != "":
            self.inputFile.delete(0, tk.END)
            self.inputFile.insert(0, fl)
            data = []
            #try:
            reader = c3d.Reader(open(fl, 'rb'))
            for i, points, analog in reader.read_frames():
                data.append(points[:, 0:3])
            print("File loading complete")
            #except:
            #    messagebox.showwarning("WARNING", "Error loading file")
                
            self.newWindow = tk.Toplevel(self.master)
            self.master.plotTrack = MotionGui(self.newWindow)
            self.master.plotTrack.addData(data, int(data[0].size / 3), reader.header.frame_rate, reader.header.last_frame - reader.header.first_frame)
            self.master.plotTrack.buildGui()
            
            self.newWindow.wm_protocol("WM_DELETE_WINDOW", self.master.destroy)
            self.newWindow.after(self.master.plotTrack.framerate, self.master.plotTrack.update)
            self.master.withdraw()
            
    async def streamData(self):
        connection = await qtm.connect("127.0.0.1")
        if connection is None:
            return

        await connection.stream_frames(components=["3d"], on_packet=self.on_packet)
    
    def on_packet(self, packet):
        """ Callback function that is called everytime a data packet arrives from QTM """
        print("Framenumber: {}".format(packet.framenumber))
        header, markers = packet.get_3d_markers()
        print("Component info: {}".format(header))
        for marker in markers:
            print("\t", marker)
            
if __name__ == "__main__":
    root = tk.Tk()
    root.app = MotionLoad(root)
    root.mainloop()