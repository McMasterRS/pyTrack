from PyQt5 import QtGui, uic, QtCore
from PyQt5.QtWidgets import QFileDialog
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import sys, os
import numpy as np
import c3d
import cv2

from optFlow import OptFlow


class ControlGUI():

    def __init__(self):
        self.window = uic.loadUi("./ui/controlUI.ui")
        self.window.show()
        self.flow = OptFlow()
        
        self.btShow = self.window.findChild(QtGui.QPushButton, "btShow")
        self.btShow.clicked.connect(self.viewStream)
        self.shown = False
        
        self.btStart = self.window.findChild(QtGui.QPushButton, "btStart")
        self.btStart.clicked.connect(self.startStream)
        self.running = False
        
        self.tbParts = self.window.findChild(QtGui.QTableWidget, "tbParts")
        
        self.btDelete = self.window.findChild(QtGui.QPushButton, "btDelete")
        self.btDelete.clicked.connect(self.removeItem)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1)
        
    def update(self):
        if self.shown == True:
            self.flow.update()
            
            for i, item in enumerate(self.flow.participents):
                if self.tbParts.rowCount() <= i:
                    self.tbParts.insertRow(self.tbParts.rowCount())
                    self.tbParts.setItem(i, 0, QtGui.QTableWidgetItem(item.name))
                self.tbParts.item(i, 0).setBackground(QtGui.QColor(item.color[2], item.color[1], item.color[0], 255))
                
            
    def viewStream(self):
        if not self.running:
            if self.shown:
                self.btShow.setText("Show Video")
                self.shown = False
                self.flow.ANY_FEEDBACK = False
                cv2.destroyAllWindows()
                self.flow.vs.stop() if self.flow.args.get("video", None) is None else self.flow.vs.release()
            else:
                self.btShow.setText("Hide Video")
                self.shown = True
                self.flow.ANY_FEEDBACK = True
                self.flow.reset()
        
    def startStream(self):
        if self.running == True:
            self.btStart.setText("Start Test")
            self.btShow.setText("Show Video")
            self.shown = False
            self.running = False
            self.flow.closeStream()
        else:
            self.btStart.setText("Stop Test")
            self.flow.reset()
            self.running = True
            self.shown = True
            
    def removeItem(self):
        self.flow.colorlist.append(self.flow.participents[self.tbParts.currentRow()].color)
        self.flow.participents.pop(self.tbParts.currentRow())
        self.tbParts.removeRow(self.tbParts.currentRow())
        
        
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    #app.setQuitOnLastWindowClosed(False)
    gui = ControlGUI()
    sys.exit(app.exec_())