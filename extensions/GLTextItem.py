import pyqtgraph.opengl as gl
from pyqtgraph.opengl.GLGraphicsItem import GLGraphicsItem
from pyqtgraph.Qt import QtCore, QtGui

class GLTextItem(GLGraphicsItem):
    def __init__(self):
        GLGraphicsItem.__init__(self)

        self.text = []
        self.pos = []

    def setGLViewWidget(self, GLViewWidget):
        self.GLViewWidget = GLViewWidget
        
    def setData(self, pos, text):
        self.pos = pos
        self.text = text

    def paint(self):
        self.GLViewWidget.qglColor(QtCore.Qt.white)
        for i, pos in enumerate(self.pos):
            self.GLViewWidget.renderText(pos[0], pos[1], pos[2], self.text[i])