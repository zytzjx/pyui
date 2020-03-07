from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,QPoint, QRect
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLabel)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
import logging
import profiledata
import os
import sys
import enum

class CAMERA(enum.Enum):
   LEFT = 0
   TOP = 1
   RIGHT = 2

class ImageLabel(QLabel):
    #LEFTCAMERA, TOPCAMERA, RIGHTCAMERA=range(3)
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
        self.ProfilePoint=[]
        self._camerapoisition=CAMERA.TOP
        self.profile=profiledata.profile("","")
        self._indexscrew=0

    def fileprechar(self, argument):
        switcher = {
            CAMERA.LEFT: "L",
            CAMERA.TOP: "T",
            CAMERA.RIGHT: "R",
        }
        return switcher.get(argument, "Invalid")

    def SetProfile(self, profilename, filename):
        self.profile.profilename = profilename
        self.profile.filename = filename

    def SetCamera(self, which):
        self._camerapoisition = which

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
        curpath=os.path.abspath(os.path.dirname(sys.argv[0]))
        profilepath=os.path.join(curpath,"profiles", self.profile.profilename)
        filename = self.fileprechar(self._camerapoisition)+str(self._indexscrew)+".png" 
        profilepath=os.path.join(profilepath, filename)
        self._indexscrew+=1
        cropQPixmap.save(profilepath)
        screwpoint = profiledata.screw(self.profile.profilename, filename, pt, QPoint(x,y), QPoint(x1,y1))
        self.ProfilePoint.append(screwpoint)
        sinfo = profilepath+", "+str(x)+", "+str(x1)+", "+str(y)+", "+str(y1)
        profiletxt = os.path.join(os.path.dirname(profilepath) , self.profile.profilename+".txt")
        self.append_new_line(profiletxt, sinfo)



    def append_new_line(self, file_name, text_to_append):
        """Append given text as a new line at the end of file"""
        # Open the file in append & read mode ('a+')
        with open(file_name, "a+") as file_object:
            # Move read cursor to the start of file.
            file_object.seek(0)
            # If file is not empty then append '\n'
            data = file_object.read(100)
            if len(data) > 0:
                file_object.write("\n")
            # Append text at the end of file
            file_object.write(text_to_append)


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
        #self.ProfilePoint.append(QPoint(x * self.scalex, y*self.scaley))

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