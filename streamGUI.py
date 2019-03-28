from PyQt5 import QtGui, uic, QtCore
from PyQt5.QtWidgets import QFileDialog
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import sys, os
import numpy as np
import c3d
import cv2
import qtm
import asyncio
from quamash import QSelectorEventLoop

from extensions.GLTextItem import GLTextItem
from scriptsGui import ScriptsGUI

class MotionGUI:
    def __init__(self):
        self.comboStyle =  """ QListWidget:item:selected:active {background: #cde8ff; color: black}
                               QListWidget:item:selected:!active {background: gray; color: black}
                               QListWidget:item:selected:disabled {background: gray; color: black}
                               QListWidget:item:selected:!disabled {background: #cde8ff; color: black} 
                           """
        self.data = np.array([(0,0,0)])
        
        self.window = uic.loadUi("./ui/streamGui.ui")
        self.window.show()
        
        self.plot = self.window.findChild(gl.GLViewWidget, "plot")
        self.plot.setCameraPosition(distance = 3000)
        self.scatter = gl.GLScatterPlotItem(pos = self.data)
        self.plot.addItem(self.scatter)
        
        self.frame = 0
        
        self.tbIP = self.window.findChild(QtGui.QLineEdit, "tbIP")
        self.tbIP.setText("127.0.0.1")
        
        self.btStream = self.window.findChild(QtGui.QPushButton, "btStream")
        self.btStream.clicked.connect(self.loadStream)

        self.btScripts = self.window.findChild(QtGui.QPushButton, "btScripts")
        self.btScripts.clicked.connect(self.openScripts)
        
        self.btRecord = self.window.findChild(QtGui.QPushButton, "btRecord")
        self.btRecord.clicked.connect(self.recordPlot)

        self.scripts = ScriptsGUI(self)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    def update(self):
        self.frame = 0
        
    def openScripts(self):
        self.scripts.window.show()
        
    def loadStream(self):
        asyncio.ensure_future(self.setupStream())
        asyncio.get_event_loop().run_forever()
        
    async def setupStream(self):
        ip = self.tbIP.text()
        connection = await qtm.connect(ip)
        if connection is None:
            return
        await connection.stream_frames(frames = "frequency:30", components = ["3d"], on_packet = self.onPacket)
        
    def onPacket(self, packet):
        self.data = []
        #print("Framenumber: {}".format(packet.framenumber))
        header, markers = packet.get_3d_markers()
        #print("Component info: {}".format(header))
        for marker in markers:
            #print("\t", marker)
            self.data.append((marker.x, marker.y, marker.z))
        data = self.scripts.parseData(self.data)
        self.scatter.setData(pos = np.array(data))
        
              
    def openScripts(self):
        self.scripts.window.show()
        
    def recordPlot(self):
        
        if not os.path.exists("./temp/"):
            os.mkdir("./temp")
        
        out = cv2.VideoWriter("./test.mp4", cv2.VideoWriter_fourcc(*'DIVX'), 30, (800, 600))
        for i in range(self.slideStart.value(), self.slideEnd.value()):
            self.frame = i
            self.plotData()
            d = self.plot.renderToArray((800, 600))
            pg.makeQImage(d).save("./temp/test" + str(i) + ".png")
            img = cv2.imread("./temp/test" + str(i) + ".png")
            out.write(img)
        for i in range(self.slideStart.value(), self.slideEnd.value()):
            os.remove("./temp/test" + str(i) + ".png")
        out.release()
    
## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    loop = QSelectorEventLoop(app)
    asyncio.set_event_loop(loop)
    gui = MotionGUI()
    #if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    QtGui.QApplication.instance().exec_()