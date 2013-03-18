#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import debug

import sys
from PySide import QtCore, QtGui

from mediancut import median_cut
from mediancut2 import median_cut2

COLOR_NUM = 9

class DominantColorViewer(QtGui.QWidget):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setWindowTitle('Dominant Color Checker')

        self.combo = QtGui.QComboBox()
        self.combo.addItems(['Median Cut', 'Modified Median Cut'])
        self.combo.currentIndexChanged.connect(self.changed)
        self.current = 0
        self.path = None
        
        self.imageLabel = QtGui.QLabel()
        self.button = QtGui.QPushButton('open')
        self.button.clicked.connect(self.open)
        self.palette = DominantColorPalette()

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.imageLabel)
        layout.addWidget(self.palette)
        layout.addWidget(self.button)        
        self.setLayout(layout)
        self.resize(300, 300)

    def open(self):
        (path, type) = QtGui.QFileDialog.getOpenFileName(self, "Open File")
        if path:
            self.path = path
            self.do()

    def changed(self, index):
        self.current = index
        self.do()

    def do(self):
        if not self.path: return
        image = QtGui.QImage(self.path)
        self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image).scaledToWidth(300))
        if self.current == 0:
            colors = median_cut(self.path, COLOR_NUM)
        elif self.current == 1:
            colors = median_cut2(self.path, COLOR_NUM)
        self.palette.setColors(colors)
        

class DominantColorPalette(QtGui.QPushButton):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.setSizePolicy(
            QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,
                              QtGui.QSizePolicy.Fixed,
                              QtGui.QSizePolicy.PushButton))
        self.colors = [(0, 0, 0)] * COLOR_NUM

    def sizeHint(self):
        return QtCore.QSize(300, 70)

    def setColors(self, colors):
        self.colors = colors
        self.update()

    def paintEvent(self, e):
        ctx = QtGui.QPainter()
        ctx.begin(self)

        w = h = 25
        for i, color in enumerate(self.colors):
            x = (w + 5) * i + 3
            y = 10
            ctx.setBrush(QtGui.QColor(*color))
            ctx.drawRect(x, y, w, h)

        ctx.end()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    dcv = DominantColorViewer()
    dcv.show()
    sys.exit(app.exec_())
    
