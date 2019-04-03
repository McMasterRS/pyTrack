from PyQt5 import QtGui, uic, QtCore
from PyQt5.QtWidgets import QFileDialog
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import sys, os
import numpy as np
import c3d
import cv2

from extensions.GLTextItem import GLTextItem
from scriptsGui import ScriptsGUI

class MotionGUI:
    def __init__(self):
        self.comboStyle =  """ QListWidget:item:selected:active {background: #cde8ff; color: black}
                               QListWidget:item:selected:!active {background: gray; color: black}
                               QListWidget:item:selected:disabled {background: gray; color: black}
                               QListWidget:item:selected:!disabled {background: #cde8ff; color: black} 
                           """
        data = []
        
        self.window = uic.loadUi("./ui/motionGui.ui")
        self.window.show()
        
        dialog = QFileDialog()
        fl = dialog.getOpenFileName(self.window, "Open File", "","C3D file (*c3d);;NumPy file (*.npy)")[0]
        self.posNP = []

        if fl[-3:] == "c3d":
            reader = c3d.Reader(open(fl, 'rb'))
            
            for i, points, analog in reader.read_frames():
                data.append(points[:, 0:3])
            self.posNP = np.array(data)
        elif fl[-3:] == "npy":
            self.posNP = np.load(fl)
        self.nameList = []
        for i, item in enumerate(self.posNP[0]):
            self.nameList.append(str(i))
        
        self.plot = self.window.findChild(gl.GLViewWidget, "plot")
        self.plot.setCameraPosition(distance = np.max(self.posNP) * 1.1)
        self.scatter = gl.GLScatterPlotItem(pos = self.posNP[0])
        self.plot.addItem(self.scatter)
        self.lines = gl.GLLinePlotItem(mode = 'lines')
        self.plot.addItem(self.lines)
        self.text = GLTextItem()
        self.text.setGLViewWidget(self.plot)
        self.plot.addItem(self.text)
        
        self.frame = 0
        
        self.slideFrame = self.window.findChild(QtGui.QSlider, "slideFrame")
        self.slideFrame.setMaximum(len(self.posNP)-1)
        self.slideFrame.sliderMoved.connect(self.setFrame)
        
        self.slideStart = self.window.findChild(QtGui.QSlider, "slideStart")
        self.slideStart.setMaximum(len(self.posNP)-1)
        self.slideStart.sliderMoved.connect(self.setFrameMin)
        
        self.slideEnd = self.window.findChild(QtGui.QSlider, "slideEnd")
        self.slideEnd.setMaximum(len(self.posNP)-1)
        self.slideEnd.setValue(len(self.posNP)-1)
        self.slideEnd.sliderMoved.connect(self.setFrameMax)
        
        self.pointList = self.window.findChild(QtGui.QListWidget, "pointList")
        for name in self.nameList:
            item = QtGui.QListWidgetItem(name, self.pointList)
        self.pointList.selectAll()
        self.pointList.setStyleSheet(self.comboStyle)

        self.linkList = self.window.findChild(QtGui.QTableWidget, "linkList")
        self.linkList.setStyleSheet(self.comboStyle)
        
        self.linkCb1 = self.window.findChild(QtGui.QComboBox, "linkCb1")
        self.linkCb1.addItems("%s" % item for item in self.nameList)
        
        self.linkCb2 = self.window.findChild(QtGui.QComboBox, "linkCb2")
        self.linkCb2.addItems("%s" % item for item in self.nameList)
        
        self.btLink = self.window.findChild(QtGui.QPushButton, "btLink")
        self.btLink.clicked.connect(self.linkPoints)
        
        self.btDelete = self.window.findChild(QtGui.QPushButton, "btDelete")
        self.btDelete.clicked.connect(self.deleteLink)
        
        self.links = []
        
        self.ckPause = self.window.findChild(QtGui.QCheckBox, "ckPause")
        self.ckText = self.window.findChild(QtGui.QCheckBox, "ckText")
        
        self.btScripts = self.window.findChild(QtGui.QPushButton, "btScripts")
        self.btScripts.clicked.connect(self.openScripts)
        
        self.btRecord = self.window.findChild(QtGui.QPushButton, "btRecord")
        self.btRecord.clicked.connect(self.recordPlot)
        self.recordStyle = self.btRecord.styleSheet()

        self.scripts = ScriptsGUI(self)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

    def update(self):
        if not self.ckPause.checkState():
            self.frame += 1
            if self.frame > self.slideEnd.value():
                self.frame = self.slideStart.value()
                
        self.slideFrame.setValue(self.frame)
        self.plotData()
        
    def plotData(self):
        data = self.scripts.parseData(self.posNP[self.frame])
        # Draw points
        pos = [x.row() for x in self.pointList.selectedIndexes()]
        self.scatter.setData(pos = data[pos])

        # Draw lines
        lines = [[data[item[0]], data[item[1]]] for item in self.links]

        if len(lines) > 0:
            lines = np.array(lines)
            self.lines.setData(pos = lines)
        
        if self.ckText.checkState():
            text = [str(x.row()) for x in self.pointList.selectedIndexes()]
            self.text.setData(data[pos], text)
        else:
            self.text.setData([],[])
    
    def setFrame(self):
        self.frame = self.slideFrame.value()
        
    def setFrameMax(self):
        if self.frame > self.slideEnd.value():
            self.frame = self.slideEnd.value()
            
    def setFrameMin(self):
        if self.frame < self.slideStart.value():
            self.frame = self.slideStart.value()

    def linkPoints(self):
        # Make sure that none of the existing links match the new one
        for item in self.links:
            if item[0] == self.linkCb1.currentIndex() and item[1] == self.linkCb2.currentIndex():
                return
            if item[1] == self.linkCb1.currentIndex() and item[0] == self.linkCb2.currentIndex():
                return
                
        self.links.append([self.linkCb1.currentIndex(), self.linkCb2.currentIndex()])
        self.linkList.insertRow(self.linkList.rowCount())
        self.linkList.setItem(self.linkList.rowCount() - 1, 0, QtGui.QTableWidgetItem(self.linkCb1.currentText()))
        self.linkList.setItem(self.linkList.rowCount() - 1, 1, QtGui.QTableWidgetItem(self.linkCb2.currentText()))
        
    def deleteLink(self):
        if self.linkList.currentRow() >= 0:
            self.links.pop(self.linkList.currentRow())
            self.linkList.removeRow(self.linkList.currentRow())
        # Clear the link lines if none are left
        if len(self.links) == 0:
            self.lines.setData(pos = np.array([[0,0,0],[0,0,0]]))
            
    def openScripts(self):
        self.scripts.window.show()
        
    def recordPlot(self):
        self.btRecord.setText("Recording")
        self.btRecord.setStyleSheet("background-color: red")
        if not os.path.exists("./temp/"):
            os.mkdir("./temp")
        dialog = QFileDialog()
        fl = dialog.getSaveFileName(self.window, "Save Video", "", "MP4 file (*.mp4)")
        
        if fl[0] == "":
                return
        out = cv2.VideoWriter(fl[0], cv2.VideoWriter_fourcc(*'DIVX'), 30, (800, 600))
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
        self.btRecord.setText("Record")
        self.btRecord.setStyleSheet(self.recordStyle)
    
## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    #app.setQuitOnLastWindowClosed(False)
    gui = MotionGUI()
    sys.exit(app.exec_())