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
        
        self.btStart = self.window.findChild(QtGui.QPushButton, "btStart")
        self.btStart.clicked.connect(self.flow.closeStream)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(10)
        
        
    def update(self):
        self.flow.update()
        
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    #app.setQuitOnLastWindowClosed(False)
    gui = ControlGUI()
    sys.exit(app.exec_())