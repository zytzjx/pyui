from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi
import logging

class Settings(QDialog):
    """Settings dialog widget
    """
 
    def __init__(self, parent=None):
        super(Settings, self).__init__()
        loadUi('Setting.ui', self)
        #self.changeStyle('Fusion')
        self.setWindowFlags(Qt.WindowMinimizeButtonHint  | Qt.WindowTitleHint | Qt.FramelessWindowHint)
        self.setWindowTitle("PSI Setting")
        screenGeometry = QApplication.desktop().screenGeometry()
        x = (screenGeometry.width() - self.width()) / 2
        y = (screenGeometry.height() - self.height()) / 2
        self.move(x, y)


