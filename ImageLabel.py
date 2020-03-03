from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,QPoint
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLabel)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
import logging

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        self.setMouseTracking(True)
        self.CURSOR_NEW = QCursor(QPixmap('cursor.png').scaled(25,25, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.CUR_CUESOR = self.cursor()
        self._imagepixmap = None
        self.w = 0
        self.h = 0
        self.scalex =0.0
        self.scaley =0.0
        self.imagel = 0
        self.imaget = 0

    def setImageScale(self):
        if self.w == 0 or self.h ==0:
            self.w = self.width()
            self.h = self.height()

    @property
    def imagepixmap(self):
        return self._imagepixmap

    @imagepixmap.setter
    def imagepixmap(self, value):
        self._imagepixmap = value
        self.setPixmap(value.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.scalex = float(value.width()) / self.pixmap().width()
        self.scaley = float(value.height()) / self.pixmap().height()
        self.imagel = (self.width() - self.pixmap().width())/2
        self.imaget = (self.height() - self.pixmap().height())/2
        logging.info(str(self.pixmap().width())+"X"+str(self.pixmap().height()))
        print(self.scalex)
        print(self.scaley)

    #def mouseMoveEvent(self, evt):
    #    logging.info(str(evt.pos().x())+"=="+str(evt.pos().y())) 
    #    print("On Hover") # event.pos().x(), event.pos().y()

    def mouseInImage(self, x, y):
        if self._imagepixmap == None:
            return False
        if x>=self.imagel and x <= self.imagel+self.pixmap().width() and y>=self.imaget and y <= self.imaget+self.pixmap().height():
            return True
        
        return False

    def DrawImage(self, x, y, clr = Qt.red):
        # convert image file into pixmap
        #pixmap = QPixmap(self.filepath)
        if self._imagepixmap == None:
            return
        # create painter instance with pixmap
        painterInstance = QPainter(self._imagepixmap)

        # set rectangle color and thickness
        penRectangle = QPen(clr)
        penRectangle.setWidth(3)

        # draw rectangle on painter
        painterInstance.setPen(penRectangle)
        painterInstance.drawEllipse(QPoint(x * self.scalex, y*self.scaley),15,15)

        # set pixmap onto the label widget
        self.setPixmap(self._imagepixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    
        painterInstance.end()

    def mousePressEvent(self, evt):
        #logging.info(str(evt.pos().x())+"=>"+str(evt.pos().y())) 
        #print(evt)
        if self.mouseInImage(evt.pos().x(), evt.pos().y()):
            self.DrawImage(evt.pos().x()-self.imagel, evt.pos().y()-self.imaget)


    def enterEvent(self, event):
        QApplication.setOverrideCursor(self.CURSOR_NEW)
        #print("hovered")

    def leaveEvent(self, event):
        QApplication.setOverrideCursor(self.CUR_CUESOR)
        #print("left")