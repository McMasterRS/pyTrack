from PyQt5 import QtGui, uic, QtCore
from PyQt5.QtWidgets import QFileDialog, QWidget
import numpy as np
import importlib
import os
from extensions.dragTable import TableWidgetDragRows

class ScriptsGUI:
    def __init__(self, master):
        self.master = master
        self.window = uic.loadUi("./ui/scriptUI.ui")
        
        self.btScript = self.window.findChild(QtGui.QPushButton, "btScript")
        self.btScript.clicked.connect(self.addScript)
        
        self.btDelete = self.window.findChild(QtGui.QPushButton, "btDelete")
        self.btDelete.clicked.connect(self.delScript)
        
        self.tbScripts = self.window.findChild(TableWidgetDragRows, "tbScripts")
        self.tbScripts.setModes()
        
        self.scriptList = {}
        
    def addScript(self):
        dialog = QFileDialog()
        file = dialog.getOpenFileName(self.window, "Open Script", filter = ("Python files (*.py)"))[0]
        
        if file == "":
            return
        
        try:
            # Convert file location into a module that can be called and add to dict
            spec = importlib.util.spec_from_file_location("runTest", file)
            self.scriptList[os.path.basename(file)[:-3]] = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.scriptList[os.path.basename(file)[:-3]])   
        except:
            print("Error importing script")
            return
        
        if not "parseData" in dir(self.scriptList[os.path.basename(file)[:-3]]):
            print("Error: Script does not contain parseData function")
            return
            
        rowPosition = self.tbScripts.rowCount()
        self.tbScripts.insertRow(rowPosition)
        chkBoxItem = QtGui.QTableWidgetItem()
        chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        chkBoxItem.setCheckState(QtCore.Qt.Checked)  
        
        self.tbScripts.setItem(rowPosition, 0, chkBoxItem)
        self.tbScripts.setItem(rowPosition, 1, QtGui.QTableWidgetItem(os.path.basename(file)[:-3])) 
        self.tbScripts.setItem(rowPosition, 2, QtGui.QTableWidgetItem(file)) 

    def delScript(self):
        # Make sure a row is selected
        if self.tbScripts.currentRow() >= 0:
            self.scriptList.pop(self.tbScripts.item(self.tbScripts.currentRow(), 1).text())
            self.tbScripts.removeRow(self.tbScripts.currentRow())
            
    def parseData(self, oldData):
        data = oldData.copy()
        for row in (row for row in range(0, self.tbScripts.rowCount()) if self.tbScripts.item(row, 0).checkState()):
            script = self.tbScripts.item(row,1).text()
            data = self.scriptList[script].parseData(data)
            
        return data
            
        