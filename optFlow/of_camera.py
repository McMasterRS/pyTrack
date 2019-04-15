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


frame0 = vs.read()
frame0_gray = cv2.cvtColor(frame0,cv2.COLOR_BGR2GRAY)

time.sleep(.1)

frame1 = vs.read()
frame1_gray = cv2.cvtColor(frame1,cv2.COLOR_BGR2GRAY)

flow = cv2.calcOpticalFlowFarneback(frame0_gray,frame1_gray, None, 0.5, 2, 21, 1, 5, 1.1, 0)
mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])

print("Your video frame size is %d by %d." % np.shape(mag))
of_fb_winsize = np.mean(np.divide(np.shape(mag),30),dtype='int')


hsv = np.zeros_like(frame1)
hsv[...,1] = 255
hsv[...,0] = ang*180/np.pi/2
hsv[...,2] = mag
bgr = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)

DURATION = float(60)
TIME  = np.array([.00] * (int(1/.01) * int(DURATION)), dtype='float')
XYmag = np.array([.00] * (int(1/.01) * int(DURATION)), dtype='float')
XYang = np.array([.00] * (int(1/.01) * int(DURATION)), dtype='float')
mag_threshold = .05
MOVT_PLOTTING = 1

start_time = time.time()
SAMPLE_COUNTER = 0
TIME[0] = time.time()
while(1):

    frame1 = vs.read()
    frame1_gray = cv2.cvtColor(frame1,cv2.COLOR_BGR2GRAY)
    
    # Don't process identical frames, which could happen if the camera is covertly upsampling.
    # Somehow, by coincidence, the fps with flow estimation is just about the 
    # real fps without flow estimation but with skipping identical frames (fake new frames).
    if np.sum(np.abs(frame1_gray-frame0_gray))==0:
        #print("Fake frame")
        continue

    SAMPLE_COUNTER = SAMPLE_COUNTER + 1
    if (SAMPLE_COUNTER-1)>=len(TIME):
        TIME.resize(len(TIME)*2,refcheck=False)
        XYang.resize(len(XYang)*2,refcheck=False)
        XYmag.resize(len(XYmag)*2,refcheck=False)

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
    flow = cv2.calcOpticalFlowFarneback(frame0_gray, frame1_gray, None, .5, 0, of_fb_winsize, 1, 3, 1.1, 0)

    # maybe try LK?
    
    # average angle ?
    mag, ang = cv2.cartToPolar(flow[...,0], flow[...,1])
    
    #print([np.max(ang),np.min(ang),circmean(ang)])
    
    hsv[...,0] = ang*180/np.pi/2
    
    TIME[SAMPLE_COUNTER-1] = time.time() - start_time
        
    # Find the mean vector.
    flow[mag<mag_threshold,0]=np.NaN
    flow[mag<mag_threshold,1]=np.NaN
    X = np.nanmean(flow[...,0])
    Y = np.nanmean(flow[...,1])
    magmean = np.sqrt(X**2+Y**2)
    angmean = np.arctan2(Y,X)

    XYmag[SAMPLE_COUNTER-1] = magmean
    XYang[SAMPLE_COUNTER-1] = angmean

    # Experiment with the scaling and thresholding to map motion b/w 0 and 255.
    mag[mag<mag_threshold]=0
    mag=mag*7
    if np.max(np.abs(mag))>255:
        print(np.max(np.abs(mag)))

    hsv[...,2] = mag # hsv[...,2] = cv2.normalize(mag,None,alpha=0,beta=255,norm_type=cv2.NORM_MINMAX)
    bgr = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)
    
    cv2.putText(bgr, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                (10, bgr.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
    
    cv2.circle(bgr, (50,50), 30, (255,255,255,1), thickness = 2)
    cv2.line(bgr, (50,50), (int(50 + (X/3) * 30),int(50 + (Y/3) * 30)), (255,255,255,1), thickness = 2)
    
    cv2.imshow("Camera", frame1_gray)
    cv2.imshow('Dense optic flow',bgr)
    
    # Show the mean velocity vector.
    #plt.plot((0,X),(0,Y),'-')
    
    frame0_gray = frame1_gray


# cleanup the camera and close any open windows
vs.stop() if args.get("video", None) is None else vs.release()
cv2.destroyAllWindows()

time.sleep(1.0)


# cleanup the relevant variables
TIME = TIME[1:SAMPLE_COUNTER-1]
XYang = XYang[1:SAMPLE_COUNTER-1]
XYmag = XYmag[1:SAMPLE_COUNTER-1]
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
    plt.plot(TIME,XYmag,'-')

    plt.subplot(313)
    plt.xlabel('Time [s]')
    plt.ylabel(r"$ \bar \phi $ [rad]")
    plt.plot(TIME,XYang,'-')
    plt.ylim(-np.pi,np.pi)
    plt.yticks((-np.pi,-.5*np.pi,0,.5*np.pi,np.pi))
    
    plt.show()

#quit(1)
#sys.exit(0)