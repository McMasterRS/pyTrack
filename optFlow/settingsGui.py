from PyQt5 import QtGui, uic, QtCore

class SettingsGUI():

    def __init__(self, master):
        self.window = uic.loadUi("./ui/settingsUI.ui")
        
        self.cbFPS = self.window.findChild(QtGui.QCheckBox, "cbFPS")
        self.sbResolution = self.window.findChild(QtGui.QSpinBox, "sbResolution")
        
    def getValues(self):
        return({"showFPS" : self.cbFPS.isChecked(), "resolution" : self.sbResolution.value()})
        