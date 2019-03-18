import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import numpy as np
import c3d

import matplotlib as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation

import pyqtgraph as pg
pg.mkQApp()

import asyncio
import qtm

import time

fig = Figure()
ax = fig.add_subplot(111, projection='3d')




class MotionGui:

    def __init__(self, master):
        self.master = master
        
        ######################################################
        ##                      Plot                        ##
        ######################################################

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        self.setList = []
        self.linkList = []
        self.dataNames = []
        
        self.frame = 0
        self.startFrame = 0
        self.endFrame = 0
        self.framerate = 0
        
        self.recording = False
        
        self.time = time.time()
        
        #asyncio.ensure_future(self.setup())
        #asyncio.get_event_loop().run_forever()
        
    async def setup(self):
        """ Main function """
        connection = await qtm.connect("127.0.0.1")
        if connection is None:
            return

        #await connection.stream_frames(components=["3d"], on_packet=self.on_packet)
        
    def buildGui(self):
        
        # Animated plot
        self.plotCanv = FigureCanvasTkAgg(self.fig, master=self.master)
        self.plotCanv.get_tk_widget().pack(expand = 0, fill = "x", padx = 5, pady = 5, side = tk.TOP)   
        self.ax.mouse_init()
        self.fig.set_facecolor('black')
        self.initPlot()
       
        ######################################################
        ##                  Frame options                   ##
        ######################################################
        
        # Frame to contain first row of plot controls
        self.vidFrame1 = tk.Frame(self.master)
        self.vidFrame1.pack(expand = 1, fill = 'x', padx = 5, pady = 0, side = tk.TOP, anchor = tk.N)
        
        # "Current Frame" label
        self.scaleLbl1 = tk.Label(self.vidFrame1, text = "Current frame", width = 12)
        self.scaleLbl1.pack(expand = 0, padx = 0, pady = 0, side = tk.LEFT, anchor = tk.W)
        
        # Current position scalebar
        var2 = tk.DoubleVar()
        self.currentPos = tk.Scale(self.vidFrame1, from_ = 0, to = self.endFrame, orient = tk.HORIZONTAL, showvalue = 0, variable = var2)
        self.currentPos.pack(expand = 1, fill = "x", padx = 0, pady = 0, side = tk.LEFT)
        
        # Second row of plot controls
        self.vidFrame2 = tk.Frame(self.master)
        self.vidFrame2.pack(expand = 1, fill = 'x', padx = 5, pady = 0, side = tk.TOP, anchor = tk.N)
        
        # "Start Frame" label
        self.scaleLbl2 = tk.Label(self.vidFrame2, text = "Start frame", width = 12)
        self.scaleLbl2.pack(expand = 0, padx = 0, pady = 0, side = tk.LEFT, anchor = tk.W)
        
        # Start frame scalebar
        var3 = tk.DoubleVar()
        self.startPos = tk.Scale(self.vidFrame2, from_ = 0, to = self.endFrame, orient = tk.HORIZONTAL, showvalue = 0, variable= var3)
        self.startPos.pack(expand = 1, fill = "x", padx = 0, pady = 0, side = tk.LEFT, anchor = tk.W)
        
        # Third row of plot controls
        self.vidFrame3 = tk.Frame(self.master)
        self.vidFrame3.pack(expand = 1, fill = 'x', padx = 5, pady = 0, side = tk.TOP, anchor = tk.N)
        
        # "End Frame" label
        self.scaleLbl3 = tk.Label(self.vidFrame3, text = "End frame", width = 12)
        self.scaleLbl3.pack(expand = 0, padx = 0, pady = 0, side = tk.LEFT, anchor = tk.W)
        
        # Start frame scalebar
        var4 = tk.DoubleVar()
        self.endPos = tk.Scale(self.vidFrame3, from_ = 0, to = self.endFrame, orient = tk.HORIZONTAL, showvalue = 0, variable= var4)
        self.endPos.pack(expand = 1, fill = "x", padx = 0, pady = 0, side = tk.LEFT, anchor = tk.W)
        self.endPos.set(self.endFrame)
        
        ######################################################
        ##           Data and linking selection             ##
        ######################################################
        
        # Listbox with the point labels in
        self.listbox = tk.Listbox(self.master, selectmode = 'multiple', exportselection=False)
        self.listbox.pack(expand=0, fill="both", padx=5, pady = 5, side=tk.LEFT, anchor = tk.W)
        for item in self.dataNames:
            self.listbox.insert("end", item)
        self.listbox.select_set(0, tk.END)
        
        # left Listbox of combinations
        self.comboList1 = tk.Listbox(self.master, exportselection=False)
        self.comboList1.pack(expand=1, fill="both", padx = 0, pady = 5, side=tk.LEFT, anchor = tk.W)
        
        # Right Listbox of combinations
        self.comboList2 = tk.Listbox(self.master, exportselection=False)
        self.comboList2.pack(expand=1, fill="both", padx = 0, pady = 5, side=tk.LEFT, anchor = tk.W)
        
        # Selection matching event
        self.comboList1.bind("<<ListboxSelect>>", self.onSelectLeft)
        self.comboList2.bind("<<ListboxSelect>>", self.onSelectRight)
        
        ######################################################
        ##                  Linking Options                 ##
        ######################################################
        
        # Options parent frame
        self.optFrameParent = tk.Frame(self.master)
        self.optFrameParent.pack(expand = 0, padx = 5, pady = 0, side = tk.LEFT, anchor = tk.W)
        
        # Left options subframe
        self.optFrame1 = tk.Frame(self.optFrameParent)
        self.optFrame1.pack(expand = 1, padx = 0, pady = 0, side = tk.LEFT, anchor = tk.NW)
        
        # Drop down menu 1
        var6 = tk.StringVar()
        self.linkDrop1 = ttk.Combobox(self.optFrame1, textvariable = var6, state="readonly", width = 10)
        self.linkDrop1['values'] = self.dataNames
        self.linkDrop1.pack(expand = 0, padx = 5, pady = 5, side = tk.TOP, anchor = tk.NW)
        self.linkDrop1.var = var6
        self.linkDrop1.current(0)
        
        # Drop down menu 2
        var7 = tk.StringVar()
        self.linkDrop2 = ttk.Combobox(self.optFrame1, textvariable = var7, state="readonly", width = 10)
        self.linkDrop2['values'] = self.dataNames
        self.linkDrop2.pack(expand = 0, padx = 5, pady = 5, side = tk.TOP, anchor = tk.NW)
        self.linkDrop2.var = var7
        self.linkDrop2.current(1)
        
        # Link button
        self.linkPoints = tk.Button(self.optFrame1, text = "Link", command = self.linkPoints)
        self.linkPoints.pack(expand = 0, fill = "x", padx = 5, pady = 5, side = tk.TOP, anchor = tk.NW)
        
        # Remove button
        self.remLink = tk.Button(self.optFrame1, text = "Delete", command = self.deletePoints)
        self.remLink.pack(expand = 0, fill = "x", padx = 5, pady = 5, side = tk.TOP, anchor = tk.NW)
        
        ######################################################
        ##                  General Options                 ##
        ######################################################
        
        # Right options subframe
        self.optFrame2 = tk.Frame(self.optFrameParent)
        self.optFrame2.pack(expand = 0, padx = 0, pady = 0, side = tk.LEFT, anchor = tk.NW)
        
        # FPS options subframe
        self.fpsFrame = tk.Frame(self.optFrame2)
        self.fpsFrame.pack(expand = 0, padx = 0, pady = 0, side = tk.TOP, anchor = tk.W)
        
        # FPS label
        self.fpsLabel = tk.Label(self.fpsFrame, text = "fps")
        self.fpsLabel.pack(expand = 0, padx = 5, pady = 4, side = tk.LEFT, anchor = tk.NW)
        
        # FPS selector
        varSpin = tk.IntVar(value = 30)
        self.fpsSpin = tk.Spinbox(self.fpsFrame, from_ = 1, to = 100, textvariable = varSpin, width = 3)
        self.fpsSpin.pack(expand = 0, padx = 5, pady = 4, side = tk.LEFT, anchor = tk.NW)
        
        # Pause button
        var5 = tk.IntVar()
        self.pause = tk.Checkbutton(self.optFrame2, text = "Pause", variable = var5, indicatoron = 0)
        self.pause.pack(expand = 0, fill = "x", padx = 5, pady = 5, side = tk.TOP, anchor = tk.NW)
        self.pause.var = var5
        
        # Button to enable/disable axis in plot
        var = tk.IntVar()
        self.axisCheck = tk.Checkbutton(self.optFrame2, text = "Show Axis", variable = var)
        self.axisCheck.pack(expand = 0, padx = 5, pady = 5, side = tk.TOP, anchor = tk.NW)
        self.axisCheck.select()
        self.axisCheck.var = var
        
        self.record = tk.Button(self.optFrame2, text = "\ud83d\udd34 Record", command = self.record)
        self.record.pack(expand = 0, fill = "x", padx = 5, pady = 4, side = tk.TOP, anchor = tk.NW)
        
        
    def on_packet(self, packet):
        """ Callback function that is called everytime a data packet arrives from QTM """
        print("Framenumber: {}".format(packet.framenumber))
        header, markers = packet.get_3d_markers()
        print("Component info: {}".format(header))
        for marker in markers:
            print("\t", marker)

    # Function to make right link listbox match selection of left
    def onSelectLeft(self, evt):
        # Try statement to catch exception when nothing in box
        try:
            # Clear selection and swap to new one
            self.comboList2.selection_clear(0, tk.END)
            self.comboList2.select_set(self.comboList1.curselection())
        except:
            return
        
    # Same but for when the user selects the right listbox
    def onSelectRight(self, evt):
        try:
            self.comboList1.selection_clear(0, tk.END)
            self.comboList1.select_set(self.comboList2.curselection())
        except:
            return

    # Creates a linked set of 2 points and adds them to list
    def linkPoints(self):
        # Check if they're the same point
        if self.linkDrop1.var.get() == self.linkDrop2.var.get():
            tk.messagebox.showwarning("WARNING", "Cannot link point to itself")
            return
            
        # Check if pair of points already exists
        for pair in self.linkList:
            if pair == [self.linkDrop1.current(), self.linkDrop2.current()] or pair == [self.linkDrop2.current(), self.linkDrop1.current()]:
                tk.messagebox.showwarning("WARNING", "Link between these points already exists")
                return
        
        # If valid, add to list array and update listboxes
        self.linkList.append([self.linkDrop1.current(), self.linkDrop2.current()])
        self.comboList1.insert("end", self.linkDrop1.var.get())
        self.comboList2.insert("end", self.linkDrop2.var.get())
        
    # Delete a link    
    def deletePoints(self):
        # Loop through link list
        for i, pair in enumerate(self.linkList):
            # Delete pair that matches the selected link
            if pair == [self.linkDrop1.current(), self.linkDrop2.current()] or pair == [self.linkDrop2.current(), self.linkDrop1.current()]:
               self.linkList.pop(i)
               self.comboList1.delete(i)
               self.comboList2.delete(i)
               return
               
    def initPlot(self):
    
        self.ax.set_xlim(-1000,1000)
        self.ax.set_ylim(-1000,1000)
        self.ax.set_zlim(-1000,1000)
        self.ax.grid(False)
        self.ax.set_axis_off()
        self.ax.set_facecolor('black')
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        self.artists = []
        
    def plotData(self, fr = -1):
        
        for artist in self.artists:
            artist.remove()
            
        self.artists.clear()
        
        # Draw axis
        #if self.axisCheck.var.get():
        #    self.ax.plot([-2000,2000],[0,0],[0,0], c = 'red')
        #    self.ax.plot([0,0],[-2000,2000],[0,0], c = 'green')
        #    self.ax.plot([0,0], [0,0], [-2000,2000], c = 'blue')
            
        if fr >= 0:
            self.frame = fr + self.startFrame

        # Draw datapoints + text
        for j in range(0, len(self.setList)):
            dp = self.data[self.frame][self.setList[j]]
            #dp = self.currentData[self.setList[j]]
            self.artists.append(self.ax.scatter(xs = dp[0], ys = dp[1], zs = dp[2], c = 'blue'))
            self.artists.append(self.ax.text(x = dp[0] + 10, y = dp[1] + 10, z = dp[2] + 10, s = self.dataNames[self.setList[j]], zdir=[1,0,0], color = 'white'))

        # Draw link lines
        #for i in range(0, len(self.linkList)):
        #    dp1 = self.data[self.frame][self.linkList[i][0]]
        #    dp2 = self.data[self.frame][self.linkList[i][1]]
        #    self.artists.append(self.ax.plot(xs = [dp1[0], dp2[0]], ys = [dp1[1], dp2[1],], zs = [dp1[2], dp2[2]], c = 'g'))
        
        if fr < 0: 
            self.plotCanv.draw()  
        else:
            return self.artists
        
    def addData(self, data, points, fps, frameCount):
        self.data = data
        self.framerate = int(1000 / fps)
        self.dataSets = points
        self.endFrame = frameCount
        for i in range(0, self.dataSets):
            self.dataNames.append(str(i))
            
    def record(self):
        if self.recording:
            self.record["text"] = "\ud83d\udd34 Record"
        else:
            self.record["text"] = "\ud83d\udd34 Recording"
            Writer = plt.animation.writers['ffmpeg']
            writer = Writer(fps=30, metadata=dict(artist='Me'), bitrate=1800)
            ani = plt.animation.FuncAnimation(self.fig, self.plotData, self.endFrame - self.startFrame - 1, interval = int(1000/30), blit = True)
            ani.save('./test.mp4', writer=writer)
            print("Saved!")
        self.recording ^= True
               
    # Runs the plotting and animation code
    def update(self):
        
        
        # Updates list of currently selected points
        self.setList = [idx for idx in self.listbox.curselection()]
        
        # Gets the sweeper data for the current and min/max animation frames
        self.frame = self.currentPos.get()
        self.startFrame = self.startPos.get()
        self.endFrame = self.endPos.get()
        
        # Checks if the system is paused
        if not self.pause.var.get():
            self.frame += 1
        
        # Loops animation
        if self.frame < self.startFrame or self.frame > self.endFrame:
            self.frame = self.startFrame
            
        # Sets framerate
        self.framerate = int(1000 / int(self.fpsSpin.get()))
        
        self.currentPos.set(self.frame)
        self.time = time.time()
        self.plotData()
        print((time.time() - self.time))
        
        
        # Re-calls this function at rate set by framerate variable
        self.master.after(self.framerate, self.update)   
               