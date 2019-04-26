# import the necessary packages
from imutils.video import VideoStream
import argparse
import datetime
#import imutils
import time
import numpy as np
import cv2
#import sys
#from astropy.stats.circstats import circmean
import matplotlib.pyplot as plt


"""
I did:
 Scaled the feedback.
 Two hard-coded ROIs (left and right sides of screen).
 Separate parameters for the two ROIs.
 Relative phase of the two, REL_PHASE_FEEDBACK flag.
 Switch feedback between individual movement or relative phase, the "collective" variable.

To Do:
 Feedback in a different window.
 There's something weird going on with optic flow estimation. It seems to alternate 
 between values every other frame. Before I though I had fixed this by removing 
 the duplicate frames that the camera can send to fake a higher fps. But now the 
 issue has appeared again. You can also see it as an up-down pattern in the mag ts,
 especially if you slowly move sideways.
 
Question:
 Is there a way to optimize this so that it doesn't load the CPU so much?
 In principle this can be done by adding a wait time in the loop, but here this
 would interfere with the camera acquisition.

"""

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the video file")
ap.add_argument("-a", "--min-area", type=int, default=500, help="minimum area size")
args = vars(ap.parse_args())

# if the video argument is None, then we are reading from webcam
if args.get("video", None) is None:
	vs = VideoStream(src=0).start()
	time.sleep(1.0)

# otherwise, we are reading from a video file
else:
	vs = cv2.VideoCapture(args["video"])

frame00 = vs.read()
frame0 = cv2.cvtColor(frame00,cv2.COLOR_BGR2GRAY)

s = np.shape(frame0)
print("Your video frame size is %d by %d." % s)
of_fb_winsize = np.mean(np.divide(np.shape(frame0),30),dtype='int')
center=(np.int(np.round(s[1]/2)),np.int(np.round(s[0]/2)))
feedback_circle_r = 100

REL_PHASE_FEEDBACK = 0

# Define a hard-coded ROI. Here it's just left and right sides of the frame.

xrange0 = list(range(0,np.int(np.round(s[1]/2))))
xrange1 = list(range(np.int(np.round(s[1]/2)),s[1]-1))

#frame1 = vs.read()
#frame1_gray = cv2.cvtColor(frame1,cv2.COLOR_BGR2GRAY)

#flow = cv2.calcOpticalFlowFarneback(frame0_gray,frame1_gray, None, 0.5, 2, 21, 1, 5, 1.1, 0)
#mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])


time.sleep(.1)
frame1 = cv2.cvtColor(vs.read(),cv2.COLOR_BGR2GRAY)

flow = cv2.calcOpticalFlowFarneback(frame0,frame1, None, 0.5, 2, 21, 1, 5, 1.1, 0)
mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])
frame0 = frame1

#hsv = np.zeros((s[0],s[1],3))
hsv = np.zeros_like(frame00)
hsv[...,1] = 255
hsv[...,0] = ang*180/np.pi/2
hsv[...,2] = mag
bgr = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)


DURATION = float(60)

TIME  = np.array([.00] * (int(1/.01) * int(DURATION)), dtype='float')
ABS_FRAME_DIFF = np.zeros(((int(1/.01) * int(DURATION))+1,1), dtype='float')
XYmag = np.zeros(((int(1/.01) * int(DURATION))+1,3))
XYang = np.zeros(((int(1/.01) * int(DURATION))+1,3))
mag_threshold = .1
MOVT_PLOTTING = 1


flow[mag<mag_threshold,0]=np.NaN
flow[mag<mag_threshold,1]=np.NaN
X0 = np.nanmean(flow[:,xrange0,0])
X1 = np.nanmean(flow[:,xrange1,0])
Y0 = np.nanmean(flow[:,xrange0,1])
Y1 = np.nanmean(flow[:,xrange1,1])

XYmag[0,0] = np.sqrt(X0**2+Y0**2)
XYmag[0,1] = np.sqrt(X1**2+Y1**2)
XYang[0,0] = np.arctan2(Y0,X0)
XYang[0,1] = np.arctan2(Y1,X1)

start_time = time.time()
SAMPLE_COUNTER = 0
FAKE_FRAME_COUNTER = 0
TIME[0] = time.time()
while(1):
    frame01 = vs.read()
    frame1 = cv2.cvtColor(frame01,cv2.COLOR_BGR2GRAY)
    
    # Don't process identical frames, which could happen if the camera is covertly upsampling.
    # Somehow, by coincidence, the fps with flow estimation is just about the 
    # real fps without flow estimation but with skipping identical frames (fake new frames).
    ABS_FRAME_DIFF[SAMPLE_COUNTER] = np.sum(np.abs(frame01-frame00))
    if ABS_FRAME_DIFF[SAMPLE_COUNTER] == 0:
        FAKE_FRAME_COUNTER = FAKE_FRAME_COUNTER + 1
        if np.mod(FAKE_FRAME_COUNTER,100) == 0:
            print("100 fake frames.")
        continue

    SAMPLE_COUNTER = SAMPLE_COUNTER + 1
    if (SAMPLE_COUNTER-1)>=len(TIME):
        TIME.resize(len(TIME)*2,refcheck=False)
        XYang.resize((len(XYang)*2,3),refcheck=False)
        XYmag.resize((len(XYmag)*2,3),refcheck=False)

    # if the `q` key is pressed, break from the loop
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    
    if 0:
        print(TIME[SAMPLE_COUNTER]-TIME[SAMPLE_COUNTER-1])
        
    if 0:
        continue
        
    
    # https://docs.opencv.org/4.0.1/dc/d6b/group__video__track.html#ga5d10ebbd59fe09c5f650289ec0ece5af
    # (..., ..., ...,                                  pyr_scale, levels, winsize, iterations, poly_n, poly_sigma, flags	)
    # pyr_scale = .5 means each next layer is .5 the size of the previous.
    # levels, number of layers
    # winsize, larger is smoother and faster but lower res
    # iterations, ...
    # poly_n, typically 5 or 7
    # poly_sigma, 1.1 or 1.5
    # flags, extra options
    flow = cv2.calcOpticalFlowFarneback(frame0, frame1, None, .5, 0, of_fb_winsize, 1, 3, 1.1, 0)

    # maybe try LK?
    
    # average angle
    mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])
    
    hsv[...,0] = ang*180/np.pi/2
    hsv[...,2] = mag
    
    TIME[SAMPLE_COUNTER-1] = time.time() - start_time
        
    # Find the mean vector.
    flow[mag<mag_threshold,0]=np.NaN
    flow[mag<mag_threshold,1]=np.NaN
    X0 = np.nanmean(flow[:,xrange0,0])
    X1 = np.nanmean(flow[:,xrange1,0])
    Y0 = np.nanmean(flow[:,xrange0,1])
    Y1 = np.nanmean(flow[:,xrange1,1])

    XYmag[SAMPLE_COUNTER-1,0] = np.sqrt(X0**2+Y0**2)
    XYmag[SAMPLE_COUNTER-1,1] = np.sqrt(X1**2+Y1**2)
    XYang[SAMPLE_COUNTER-1,0] = np.arctan2(Y0,X0)
    if XYang[SAMPLE_COUNTER-1,0]<0:
        XYang[SAMPLE_COUNTER-1,0] = np.mod(XYang[SAMPLE_COUNTER-1,0],np.pi)+np.pi
    XYang[SAMPLE_COUNTER-1,1] = np.arctan2(Y1,X1)
    if XYang[SAMPLE_COUNTER-1,1]<0:
        XYang[SAMPLE_COUNTER-1,1] = np.mod(XYang[SAMPLE_COUNTER-1,1],np.pi)+np.pi
    XYang[SAMPLE_COUNTER-1,2] = np.mod(XYang[SAMPLE_COUNTER-1,0] - XYang[SAMPLE_COUNTER-1,1],2*np.pi)
    xrel,yrel=cv2.polarToCart(1,XYang[SAMPLE_COUNTER-1,2])

    # Experiment with the scaling and thresholding to map motion b/w 0 and 255.
    mag[mag<mag_threshold]=0
    mag=mag*10
    if np.max(np.abs(mag))>255:
        print(np.max(np.abs(mag)))

    hsv[...,2] = mag # hsv[...,2] = cv2.normalize(mag,None,alpha=0,beta=255,norm_type=cv2.NORM_MINMAX)
    bgr = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
    
    cv2.putText(bgr, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, bgr.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
                
    #cv2.circle(bgr, (50,50), 30, (255,255,255,1), thickness = 2)
    #cv2.line(bgr, (50,50), (int(50 + (X/3) * 30),int(50 + (Y/3) * 30)), (255,255,255,1), thickness = 2)
    
    cv2.circle(bgr, center, feedback_circle_r, (255,255,255,1), thickness = 1)
    if REL_PHASE_FEEDBACK == 1:
        cv2.line(bgr, center, (int(center[0] + xrel[0] * feedback_circle_r),int(center[1] + yrel[0] * feedback_circle_r)), (200,200,250,1), thickness = 2)
    else:
        cv2.line(bgr, center, (int(center[0] + (X0) * feedback_circle_r),int(center[1] + (Y0) * feedback_circle_r)), (255,0,255,1), thickness = 2)
        cv2.line(bgr, center, (int(center[0] + (X1) * feedback_circle_r),int(center[1] + (Y1) * feedback_circle_r)), (255,255,0,1), thickness = 2)
        
    
    cv2.imshow("Camera", frame1)
    cv2.imshow('Dense optic flow',bgr)
    
    frame0 = frame1
    frame00 = frame01

# cleanup the camera and close any open windows
vs.stop() if args.get("video", None) is None else vs.release()
cv2.destroyAllWindows()

time.sleep(.1)


# cleanup the relevant variables
TIME = TIME[1:SAMPLE_COUNTER-1]
ABS_FRAME_DIFF = ABS_FRAME_DIFF[1:SAMPLE_COUNTER-1]
XYang = XYang[1:SAMPLE_COUNTER-1,:]
XYmag = XYmag[1:SAMPLE_COUNTER-1,:]
mint=min(TIME)
TIME = [xx-mint for xx in TIME]


#v visualize for diagnostic purposes.
if MOVT_PLOTTING:
    plt.subplot(311)
    DTIME = np.diff(TIME)
    SR = np.divide(1,DTIME)
    plt.xlabel('Time, s')
    plt.ylabel('Frame acquisition rate, fps')
    plt.plot(TIME[1:],SR,'-')

    plt.subplot(312)
    plt.xlabel('Time [s]')
    plt.ylabel('|X| [px]')
    plt.plot(TIME,XYmag[:,(0,1)],'-')

    plt.subplot(313)
    plt.xlabel('Time [s]')
    plt.ylabel(r"$ \bar \phi $ [rad]")
    plt.plot(TIME,XYang,'-')
    plt.ylim(0*np.pi,2*np.pi)
    plt.yticks((0,.5*np.pi,np.pi,1.5*np.pi,2*np.pi))
    
    plt.figure()
    plt.plot(TIME,ABS_FRAME_DIFF,'-')
    plt.xlabel('Time [s]')
    plt.ylabel(r"$ \Sigma_i \Sigma_j |I_n - I_{n-1}| $")
    plt.show()
    

#quit(1)
#sys.exit(0)