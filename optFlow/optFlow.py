# import the necessary packages
from imutils.video import VideoStream
import datetime
import time
import numpy as np
import cv2
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtGui
#import farneback3d

from libraries.videocaptureasync import VideoCaptureAsync
from scipy.spatial import distance

class Participant():
    def __init__(self, x, y, color):
    
        self.name = "Region"
        
        self.xRange = np.array([x, x+1])
        self.yRange = np.array([y, y+1])
        
        self.color = color
        
        self.X = 0
        self.Y = 0
        
        self.XYmag = []
        self.XYang = []
        
        self.flow = []
        
    def setUp(self, x, y):  
        # Creates a 1x1px box if the user just clicks and releases in the same spot
        if x == self.xRange[0]:
            x += 1
        if y == self.yRange[0]:
            y += 1
        self.xRange = np.array(range(min(self.xRange[0], x), max(self.xRange[0], x)))
        self.yRange = np.array(range(min(self.yRange[0], y), max(self.yRange[0], y)))
        
    def reset(self):
        self.X = 0
        self.Y = 0
        
        self.XYmag = []
        self.XYang = []
        
        self.flow = []
        
class OptFlow():
    def __init__(self, master, video = None):
    
        self.master = master
        
        # Some more parameters.
        self.REL_PHASE_FEEDBACK = 0
        self.ANY_FEEDBACK = 1
        self.MOVT_PLOTTING = 1
        self.feedback_circle_r = 200 # The size of the circle in the center of the screen.
        self.mag_threshold = .1 # This is important. We try to reduce noise by zero-ing out fluctuations in pixel intensity below a certain threshold.
        self.ABS_FRAME_DIFF = []
        self.FAKE_FRAME_COUNTER = 0

        self.participents = []
        
        self.recording = False
        self.data = []
        
        self.videoType = ""
        self.frameCounter = 0
        
        # if the video argument is None, then we are reading from webcam
        if video is None:
            self.vs = VideoCaptureAsync(src=0)
            #self.vs.start()
            self.videoType = "cam"
        # otherwise, we are reading from a video file
        else:
            self.vs = cv2.VideoCapture(video)
            self.videoType = "vid"
        
        self.frame00 = self.vs.read()[1]
        self.frame0 = cv2.flip(cv2.cvtColor(self.frame00,cv2.COLOR_BGR2GRAY),1)
        self.frame01 = []
        self.frame1 = []
        self.hsv = np.zeros_like(self.frame00)
        self.hsv[..., 1] = 255
        
        s = np.shape(self.frame0)
        print("Your video frame size is %d by %d." % s)
        self.of_fb_winsize = np.mean(np.divide(s,30),dtype='int')
        self.center=(np.int(np.round(s[1]/2)),np.int(np.round(s[0]/2)))
        
        self.colorlist = [(230, 25, 75, 1), (60, 180, 75, 1), (255, 225, 25, 1), (0, 130, 200, 1), (245, 130, 48, 1), (145, 30, 180, 1), (70, 240, 240, 1), (240, 50, 230, 1), (210, 245, 60, 1), (250, 190, 190, 1), (0, 128, 128, 1), (230, 190, 255, 1), (170, 110, 40, 1), (255, 250, 200, 1), (128, 0, 0, 1), (170, 255, 195, 1), (128, 128, 0, 1), (255, 215, 180, 1), (0, 0, 128, 1), (128, 128, 128, 1), (255, 255, 255, 1)]
        self.showFPS = False
        
        self.TIME = [time.time()]
         
    def reset(self):
        self.frame00 = self.vs.read()[1]
        self.frame0 = cv2.flip(cv2.cvtColor(self.frame00,cv2.COLOR_BGR2GRAY),1)
        self.frame1 = []
        self.frame01 = []
        self.hsv = np.zeros_like(self.frame00)
        self.hsv[..., 1] = 255
        self.TIME = [time.time()]
        self.data = []
        
        if self.videoType == "cam":
            self.vs.start()
        
        for item in self.participents:
            item.reset()
            
    def updateSettings(self, settings):
        self.of_fb_winsize = np.mean(np.divide(np.shape(self.frame0), settings["resolution"]), dtype = 'int')
        self.showFPS = settings["showFPS"]
            
            
    def boxSelect(self, event, x, y, flags, param):
    
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.colorlist) > 0:
                part = Participant(x, y, self.colorlist[0])
                self.participents.append(part)
        elif event == cv2.EVENT_LBUTTONUP:
            if len(self.colorlist) > 0:
                self.participents[-1].setUp(x, y)
                self.colorlist.pop(0)
        
        
    def update(self, trackState, pauseState):
        
        if not pauseState: 
            vidRead = self.vs.read()[1]
            if vidRead is None:
                self.vs.set(cv2.CAP_PROP_POS_AVI_RATIO, 0)
                vidRead = self.vs.read()[1]

            self.frame01 = cv2.flip(vidRead,1)
            self.frame1 = cv2.cvtColor(self.frame01,cv2.COLOR_BGR2GRAY)
     
            self.data.append(self.frame01)

            # Don't process identical frames, which could happen if the camera is covertly upsampling.
            # Somehow, by coincidence, the fps with flow estimation is just about the 
            # real fps without flow estimation but with skipping identical frames (fake new frames).
            if self.recording:
                frameDiff = np.sum(np.abs(frame01 - frame00))
                ABS_FRAME_DIFF.append(frameDiff)
                if frameDiff == 0:
                    FAKE_FRAME_COUNTER += 1
                    if FAKE_FRAME_COUNTER == 100:
                        np.mod(FAKE_FRAME_COUNTER)
                        print("100 fake frames")
                    return

            # https://docs.opencv.org/4.0.1/dc/d6b/group__video__track.html#ga5d10ebbd59fe09c5f650289ec0ece5af
            # (..., ..., ...,                                  pyr_scale, levels, winsize, iterations, poly_n, poly_sigma, flags	)
            # pyr_scale = .5 means each next layer is .5 the size of the previous.
            # levels, number of layers
            # winsize, larger is smoother and faster but lower res
            # iterations, ...
            # poly_n, typically 5 or 7
            # poly_sigma, 1.1 or 1.5
            # flags, extra options
            flow = cv2.calcOpticalFlowFarneback(self.frame0, self.frame1, None, .5, 0, self.of_fb_winsize, 1, 5, 1.1, 0)
            
            # average angle
            mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])

            self.hsv[...,0] = ang*180/np.pi/2
            self.hsv[...,2] = mag
            
            # Find the mean vector.
            # Why was this NAN? this caused a lot of bugs with the code if the entire
            # array was below the threshold amount
            flow[mag<self.mag_threshold,0]=np.NaN
            flow[mag<self.mag_threshold,1]=np.NaN
            
            # Work out the x/y and mag/angle components of each participant
            for item in self.participents:
                # Split the data on x and then y. Doing this in one command crashes the code for some obscure reason
                fl2 = flow[:, item.xRange, :]
                fl2 = fl2[item.yRange, :, :]
                item.X = np.nanmean(fl2[:,:,0])
                item.Y = np.nanmean(fl2[:,:,1])
                
                item.X = np.nan_to_num(item.X)
                item.Y = np.nan_to_num(item.Y)   

                item.XYmag.append(np.sqrt(item.X ** 2 + item.Y ** 2))
                item.XYang.append(np.arctan2(item.Y, item.X))
               
                if item.XYang[-1] < 0:
                    item.XYang[-1] = np.mod(item.XYang[-1], np.pi) + np.pi
                    
                if trackState == True:
                    item.xRange += int(item.X)
                    item.yRange += int(item.Y)
        
        if len(self.participents) >= 2:
            # Get the relative angle between the first two participents
            relAng = np.mod(np.subtract(self.participents[0].XYang[-1],self.participents[1].XYang[-1]), 2*np.pi)
            xrel, yrel = cv2.polarToCart(1, relAng)
        else:
            xrel, yrel = 0, 0
        
        if not pauseState:
            # # Experiment with the scaling and thresholding to map motion b/w 0 and 255.
            mag[mag<self.mag_threshold]=0
            mag=mag*10
            if np.max(np.abs(mag))>255:
                print(np.max(np.abs(mag)))
            
            self.TIME.append(time.time() - self.TIME[0])
            
            self.hsv[...,2] = mag 

        # I don't remember any more why I commented this out. Oh yeah. You want to be able to tell how much movement is detected, and how fast, from the video.
        # hsv[...,2] = cv2.normalize(mag,None,alpha=0,beta=255,norm_type=cv2.NORM_MINMAX)
        bgr = cv2.cvtColor(self.hsv,cv2.COLOR_HSV2BGR)
        
        cv2.putText(bgr, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, bgr.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
                

        
        cv2.circle(bgr, self.center, self.feedback_circle_r, (25,25,25,1), thickness = 1)
        
        cv2.setMouseCallback("Camera", self.boxSelect)
        camImg = self.frame01.copy()
        for i, item in enumerate(self.participents):
            cv2.rectangle(camImg, (item.xRange[0], item.yRange[0]), (item.xRange[-1], item.yRange[-1]), item.color, thickness = 2)

        if self.showFPS:
            cv2.putText(camImg, "FPS: " + str(1.0 / (self.TIME[-1] - self.TIME[-2])), (10, bgr.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        
        # Either display individual velocity vectors or the relative phase.
        if self.REL_PHASE_FEEDBACK == 1:
            cv2.line(bgr, self.center, (int(self.center[0] + xrel[0] * self.feedback_circle_r),int(self.center[1] + yrel[0] * self.feedback_circle_r)), (200,200,250,1), thickness = 2)
        else:
            for item in self.participents:
                cv2.line(bgr, self.center, (int(self.center[0] + item.X * self.feedback_circle_r),int(self.center[1] + item.Y * self.feedback_circle_r)), item.color, thickness = 2)
        
            cv2.imshow("Camera", camImg)
        if self.ANY_FEEDBACK:
            cv2.imshow('Dense optic flow',bgr)
    
        if not pauseState:
            self.frame0 = self.frame1
            self.frame00 = self.frame01

        
    def closeStream(self):
        if self.videoType == "cam":
            self.vs.stop()
        else:
            self.vs.release()
            
        cv2.destroyAllWindows()
        self.TIME = self.TIME[1:]   
        self.TIME = [t - self.TIME[0] for t in self.TIME]
        
        buttonReply = QMessageBox.question(self.master, '', "Save test data?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            f = QtGui.QFileDialog.getSaveFileName(self.master, "Save File", "", "AVI file (*.avi)")[0]
            
            if f is not "":
                height, width, layers = self.data[-1].shape
                mov = cv2.VideoWriter(f, cv2.VideoWriter_fourcc(*'DIVX'), np.mean(1.0 / np.diff(self.TIME)), (width, height), True)
                
                for frame in self.data:
                    mov.write(frame)
                mov.release()

        if self.MOVT_PLOTTING:
            self.runVis()
        
    def runVis(self):
    
        # Framerate
        plt.subplot(311)
        DTIME = np.diff(self.TIME)
        SR = np.divide(1,DTIME) 
        plt.xlabel('Time, s')
        plt.ylabel('Frame acquisition rate, fps')
        plt.plot(self.TIME[1:],SR,'-')   

        # Magnitude of optic flow
        plt.subplot(312)
        plt.xlabel('Time [s]')
        plt.ylabel('|X| [px]')
        for item in self.participents:
            plt.plot(self.TIME,item.XYmag,'-')

        # Angle of optic flow
        plt.subplot(313)
        plt.xlabel('Time [s]')
        plt.ylabel(r"$ \bar \phi $ [rad]")
        for item in self.participents:
            plt.plot(self.TIME,item.XYang,'-')
        plt.ylim(0*np.pi,2*np.pi)
        plt.yticks((0,.5*np.pi,np.pi,1.5*np.pi,2*np.pi))
        
        plt.show()