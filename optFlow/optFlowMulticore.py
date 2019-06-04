# import the necessary packages
from imutils.video import VideoStream
import argparse
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
    def __init__(self, xrange, yrange, color):
    
        self.name = "Region"
        
        self.xRange = np.array([xrange, xrange])
        self.yRange = np.array([yrange, yrange])
        
        self.color = color
        
        self.X = 0
        self.Y = 0
        
        self.XYmag = []
        self.XYang = []
        
        self.flow = []
        
        
    def setUp(self, x, y):  
    
        x1 = min(self.xRange[0], x)
        x2 = max(self.xRange[0], x)
        
        y1 = min(self.yRange[0], y)
        y2 = max(self.yRange[0], y)
        
        self.xRange = np.array(range(x1, x2))
        self.yRange = np.array(range(y1, y2))
        
    def reset(self):
        self.X = 0
        self.Y = 0
        
        self.XYmag = []
        self.XYang = []
        
        self.flow = []
        
class OptFlow():
    def __init__(self, master):
        self.master = master
        # Some more parameters.
        self.REL_PHASE_FEEDBACK = 0
        self.ANY_FEEDBACK = 1
        self.MOVT_PLOTTING = 1
        self.feedback_circle_r = 200 # The size of the circle in the center of the screen.
        self.mag_threshold = .1 # This is important. We try to reduce noise by zero-ing out fluctuations in pixel intensity below a certain threshold.
        self.ABS_FRAME_DIFF = []
        self.FAKE_FRAME_COUNTER = 0
        
        self.camera = cv2.namedWindow("Camera")
        cv2.setMouseCallback("Camera", self.boxSelect)
        cv2.destroyAllWindows()
        
        self.participents = []
        
        self.recording = False
        self.data = []
        self.dt = []
        
        # construct the argument parser and parse the arguments
        ap = argparse.ArgumentParser()
        ap.add_argument("-v", "--video", help="path to the video file")
        ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
        self.args = vars(ap.parse_args())
        
        # if the video argument is None, then we are reading from webcam
        if self.args.get("video", None) is None:
            self.vs = VideoCaptureAsync(src=0)
        # otherwise, we are reading from a video file
        else:
            self.vs = cv2.VideoCaptureAsync(self.args["video"])
            
        self.vs.start()
        
        self.frame00 = self.vs.read()[1]
        self.frame0 = cv2.flip(cv2.cvtColor(self.frame00,cv2.COLOR_BGR2GRAY),1)
        self.frame01 = []
        self.frame1 = []
        self.hsv = np.zeros_like(self.frame00)
        self.hsv[..., 1] = 255
        
        s = np.shape(self.frame0)
        print("Your video frame size is %d by %d." % s)
        self.of_fb_winsize = np.mean(np.divide(s,10),dtype='int')
        self.center=(np.int(np.round(s[1]/2)),np.int(np.round(s[0]/2)))
        
        self.colorlist = [(230, 25, 75, 1), (60, 180, 75, 1), (255, 225, 25, 1), (0, 130, 200, 1), (245, 130, 48, 1), (145, 30, 180, 1), (70, 240, 240, 1), (240, 50, 230, 1), (210, 245, 60, 1), (250, 190, 190, 1), (0, 128, 128, 1), (230, 190, 255, 1), (170, 110, 40, 1), (255, 250, 200, 1), (128, 0, 0, 1), (170, 255, 195, 1), (128, 128, 0, 1), (255, 215, 180, 1), (0, 0, 128, 1), (128, 128, 128, 1), (255, 255, 255, 1)]
        
        self.TIME = [time.time()]
        self.time = time.time()
         
    def reset(self):
        self.frame00 = self.vs.read()[1]
        self.frame1 = []
        self.frame01 = []
        self.hsv = np.zeros_like(self.frame00)
        self.hsv[..., 1] = 255
        self.TIME = [time.time()]
        self.data = [cv2.flip(self.vs.read()[1])]
        
        self.time = time.time()
        
        self.vs.start()
        
        for item in self.participents:
            item.reset()
            
            
    def boxSelect(self, event, x, y, flags, param):
    
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.colorlist) > 0:
                part = Participant(x, y, self.colorlist[0])
                self.participents.append(part)
        elif event == cv2.EVENT_LBUTTONUP:
            if len(self.colorlist) > 0:
                self.participents[-1].setUp(x, y)
                self.colorlist.pop(0)
        
    
    def getData(self):
        self.data.append(cv2.flip(self.vs.read()[1],1))
        self.dt.append(self.time - time.time())
        self.time = time.time()

    def update(self):
        self.frame00 = self.data[-2]
        self.frame0 = cv2.cvtColor(self.frame00,cv2.COLOR_BGR2GRAY)
        
        self.frame01 = self.data[-1]
        self.frame1 = cv2.cvtColor(self.frame01,cv2.COLOR_BGR2GRAY)
        
        runOptFlow(self.frame0, self.frame1, self.participents)
        
        
    def runOptFlow(self, frame0, frame1, participants):

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
        
        hsv = np.zeros_like(self.frame00)
        hsv[...,0] = ang*180/np.pi/2
        hsv[...,2] = mag
        
        # Find the mean vector.
        flow[mag<self.mag_threshold,0]=0
        flow[mag<self.mag_threshold,1]=0
        
        # Work out the x/y and mag/angle components of each participant
        for item in participants:
            # Split the data on x and then y. Doing this in one command crashes the code for some obscure reason
            fl2 = flow[:, item.xRange, :]
            fl2 = fl2[item.yRange, :, :]
            item.X = np.nanmean(fl2[:,:,0])
            item.Y = np.nanmean(fl2[:,:,1])
            item.XYmag = (np.sqrt(item.X ** 2 + item.Y ** 2))
            item.XYang = (np.arctan2(item.Y, item.X))
            if item.XYang < 0:
                item.XYang = np.mod(item.XYang, np.pi) + np.pi
        
        if len(participants) >= 2:
            # Get the relative angle between the first two participents
            relAng = np.mod(np.subtract(participants[0].XYang,participants[1].XYang), 2*np.pi)
            xrel, yrel = cv2.polarToCart(1, relAng)
        else:
            xrel, yrel = 0, 0
        
        # # Experiment with the scaling and thresholding to map motion b/w 0 and 255.
        mag[mag<self.mag_threshold]=0
        mag=mag*10
        if np.max(np.abs(mag))>255:
            print(np.max(np.abs(mag)))
            
        hsv[...,2] = mag 
        # I don't remember any more why I commented this out. Oh yeah. You want to be able to tell how much movement is detected, and how fast, from the video.
        # hsv[...,2] = cv2.normalize(mag,None,alpha=0,beta=255,norm_type=cv2.NORM_MINMAX)
        bgr = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
        
        cv2.putText(bgr, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, bgr.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        
        cv2.circle(bgr, self.center, self.feedback_circle_r, (25,25,25,1), thickness = 1)
        
        cv2.setMouseCallback("Camera", self.boxSelect)
        camImg = self.frame01.copy()
        for i, item in enumerate(participants):
            cv2.rectangle(camImg, (item.xRange[0], item.yRange[0]), (item.xRange[-1], item.yRange[-1]), item.color, thickness = 2)
        
        # Either display individual velocity vectors or the relative phase.
        if self.REL_PHASE_FEEDBACK == 1:
            cv2.line(bgr, self.center, (int(self.center[0] + xrel[0] * self.feedback_circle_r),int(self.center[1] + yrel[0] * self.feedback_circle_r)), (200,200,250,1), thickness = 2)
        else:
            for item in self.participents:
                cv2.line(bgr, self.center, (int(self.center[0] + item.X * self.feedback_circle_r),int(self.center[1] + item.Y * self.feedback_circle_r)), item.color, thickness = 2)
        
            cv2.imshow("Camera", camImg)
        if self.ANY_FEEDBACK:
            cv2.imshow('Dense optic flow',bgr)
    
        
        self.TIME.append(time.time() - self.TIME[0])
        
    def closeStream(self):
        self.vs.stop() if self.args.get("video", None) is None else self.vs.release()
        cv2.destroyAllWindows()
        self.TIME = self.TIME[1:]   
        self.TIME = [t - self.TIME[0] for t in self.TIME]
        
        buttonReply = QMessageBox.question(self.master, '', "Save test data?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            f = QtGui.QFileDialog.getSaveFileName(self.master, "Save File")[0]
            np.save(f, self.data)

        if self.MOVT_PLOTTING:
            self.runVis()
        
    def runVis(self):
        plt.subplot(311)
        DTIME = np.diff(self.TIME)
        SR = np.divide(1,DTIME) 
        plt.xlabel('Time, s')
        plt.ylabel('Frame acquisition rate, fps')
        plt.plot(self.TIME[1:],SR,'-')   

        plt.subplot(312)
        plt.xlabel('Time [s]')
        plt.ylabel('|X| [px]')
        for item in self.participents:
            plt.plot(self.TIME,item.XYmag,'-')

        plt.subplot(313)
        plt.xlabel('Time [s]')
        plt.ylabel(r"$ \bar \phi $ [rad]")
        for item in self.participents:
            plt.plot(self.TIME,item.XYang,'-')
        plt.ylim(0*np.pi,2*np.pi)
        plt.yticks((0,.5*np.pi,np.pi,1.5*np.pi,2*np.pi))
        
        plt.show()