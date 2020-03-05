from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,QPoint, QRect
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
        self._imagepixmapback = None
        self.w = 0
        self.h = 0
        self.scalex =0.0
        self.scaley =0.0
        self.imagel = 0
        self.imaget = 0
        self.screwW = 24
        self.screwH = 24
        self._isProfile = False


    def setImageScale(self):
        if self.w == 0 or self.h ==0:
            self.w = self.width()
            self.h = self.height()
            logging.info("uilabel:"+str(self.w)+"X"+str(self.h))

    @property
    def isProfile(self):
        return self._isProfile

    @isProfile.setter
    def isProfile(self, value):
        self._isProfile = value

    @property
    def imagepixmap(self):
        return self._imagepixmap

    @imagepixmap.setter
    def imagepixmap(self, value):
        self._imagepixmap = value
        self._imagepixmapback = value.copy()
        self.setPixmap(value.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.scalex = float(value.width()) / self.pixmap().width()
        self.scaley = float(value.height()) / self.pixmap().height()
        self.imagel = (self.width() - self.pixmap().width())/2
        self.imaget = (self.height() - self.pixmap().height())/2
        logging.info("lblimage:"+str(self.pixmap().width())+"X"+str(self.pixmap().height()))
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

    def _savescrew(self, pt):
        x = pt.x()-self.screwW
        if x < 0 :
            x = 0
        y = pt.y() - self.screwH
        if y < 0 :
            y = 0

        x1 = pt.x()+self.screwW
        if x1 > self._imagepixmapback.width() :
            x1 = self._imagepixmapback.width()
        y1 = pt.y() + self.screwH
        if y1 > self._imagepixmapback.height() :
            y1 = self._imagepixmapback.width()
        
        currentQRect = QRect(QPoint(x,y),QPoint(x1,y1))
        cropQPixmap = self._imagepixmapback.copy(currentQRect)
        cropQPixmap.save('output.png')



    def DrawImage(self, x, y, clr = Qt.red):
        # convert image file into pixmap
        #pixmap = QPixmap(self.filepath)
        logging.info("draw:"+str(x)+"=>"+str(y)) 
        if self._imagepixmap == None or not self._isProfile:
            return
        # create painter instance with pixmap
        painterInstance = QPainter(self._imagepixmap)

        # set rectangle color and thickness
        penRectangle = QPen(clr)
        penRectangle.setWidth(3)

        # draw rectangle on painter
        painterInstance.setPen(penRectangle)
        painterInstance.drawEllipse(QPoint(x * self.scalex, y*self.scaley),25,25)

        # set pixmap onto the label widget
        self.setPixmap(self._imagepixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    
        painterInstance.end()
        self._savescrew(QPoint(x * self.scalex, y*self.scaley))



    def mousePressEvent(self, evt):
        logging.info("mousepress:"+str(evt.pos().x())+"=>"+str(evt.pos().y())) 
        #print(evt)
        if self.mouseInImage(evt.pos().x(), evt.pos().y()):
            self.DrawImage(evt.pos().x()-self.imagel, evt.pos().y()-self.imaget)


    def enterEvent(self, event):
        QApplication.setOverrideCursor(self.CURSOR_NEW)
        #print("hovered")

    def leaveEvent(self, event):
        QApplication.setOverrideCursor(self.CUR_CUESOR)
        #print("left")