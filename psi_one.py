#!/usr/bin/env python3
import sys
import os
import io
import time
import picamera
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi
import logging
from settings import Settings
import ImageLabel


files = []

#CURSOR_NEW = QtGui.QCursor(QtGui.QPixmap('cursor.png'))

def listImages(path):
#path = 'c:\\projects\\hc2\\'
    # r=root, d=directories, f = files
    for r, _, f in os.walk(path):
        for file in f:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(r, file))

class ImageCheckThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.git_url = ""

    # run method gets called when we start the thread
    def run(self):
        tmpdir = tempfile.mkdtemp()
        cmd = "git clone {0} {1}".format(self.git_url, tmpdir)
        subprocess.check_output(cmd.split())
        # git clone done, now inform the main thread with the output
        self.signal.emit(tmpdir)


class UISettings(QDialog):
    """Settings dialog widget
    """
    index = 0
    w = 0
    h = 0
    filepath=""
    pixmap = None
    resized = pyqtSignal()
    def __init__(self, parent=None):
        super(UISettings, self).__init__()
        loadUi('psi_one.ui', self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.changeStyle('Fusion')
        self.pbClose.clicked.connect(self.close)
        self.pbImageChange.clicked.connect(self.on_click)
        self.pbImageChangeDown.clicked.connect(self.on_click)
        self.pbStart.clicked.connect(self.on_startclick)
        self.updateProfile()
        self.resized.connect(self.someFunction)
        self.pbSetting.clicked.connect(self.on_settingclick)
        self.checkBox.stateChanged.connect(self.btnstate)
        self.tabWidget.currentChanged.connect(self.on_CameraChange)
        self.leProfile.hide()
        self.setStyleSheet('''
        QPushButton{background-color:rgba(255,178,0,50%);
            color: white;   
            border-radius: 10px;  
            border: 2px groove gray; 
            border-style: outset;}
		QPushButton:hover{background-color:white; 
            color: black;}
		QPushButton:pressed{background-color:rgb(85, 170, 255); 
            border-style: inset; }
        QWidget#Dialog{
            background:gray;
            border-top:1px solid white;
            border-bottom:1px solid white;
            border-left:1px solid white;
            border-top-left-radius:10px;
            border-bottom-left-radius:10px;
        }''')
        #self.on_CameraChange()
        #self.setWindowOpacity(0.5) # 设置窗口透明度
        #self.setAttribute(Qt.WA_TranslucentBackground) # 设置窗口背景透明

        #self.resize(800, 600) 
    #def mouseMoveEvent(self, evt: QMouseEvent) -> None:
    #    logging.info(str(evt.pos().x())+"=="+str(evt.pos().y())) 
    #    super(UISettings, self).mouseMoveEvent(evt)

    #def mousePressEvent(self, evt: QMouseEvent) -> None:
    #    logging.info(str(evt.pos().x())+"=>"+str(evt.pos().y())) 
    #    super(UISettings, self).mousePressEvent(evt)

    

    def resizeEvent(self, event):
        self.resized.emit()
        return super(UISettings, self).resizeEvent(event)

    def someFunction(self):
        logging.info(str(self.width())+"X"+str(self.height()))   

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        QApplication.setPalette(QApplication.style().standardPalette())

    def updateProfile(self):
        curpath=os.path.abspath(os.path.dirname(sys.argv[0]))
        profilepath=os.path.join(curpath,"profiles")
        self.comboBox.addItems([name for name in os.listdir(profilepath) if os.path.isdir(os.path.join(profilepath, name))])
        
 
    def loadimage(self,filepath):
        pixmap = QPixmap(filepath)
        self.imageTop.setPixmap(pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    def loadimageA(self):
        #self.index+=1
        filepath=files[self.index%len(files)]
        self.loadimage(filepath)

    def DrawImage(self, x, y, clr = Qt.red):
        # convert image file into pixmap
        #pixmap = QPixmap(self.filepath)
        if self.pixmap == None:
            return
        # create painter instance with pixmap
        painterInstance = QPainter(self.pixmap)

        # set rectangle color and thickness
        penRectangle = QPen(clr)
        penRectangle.setWidth(3)

        # draw rectangle on painter
        painterInstance.setPen(penRectangle)
        painterInstance.drawEllipse(x,y,25,25)

        # set pixmap onto the label widget
        self.imageTop.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    
        painterInstance.end()

    def PreviewCamera(self):
        # Create the in-memory stream
        stream = io.BytesIO()
        with picamera.PiCamera() as camera:
            camera.start_preview()
            time.sleep(1)
            camera.capture(stream, format='jpeg')
            camera.stop_preview()
        # "Rewind" the stream to the beginning so we can read its content
        stream.seek(0)
        image = Image.open(stream)
        imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
        #qimage = QImage(imageq) #cast PIL.ImageQt object to QImage object -that´s the trick!!!
        #pixmap = QPixmap(qimage)
        pixmap = QPixmap.fromImage(imageq)
        self.imageTop.imagepixmap = pixmap
        #self.lblImage.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))   

    @pyqtSlot()
    def btnstate(self):
        if self.sender().isChecked():
            self.imageTop.isProfile = True
            self.imageLeft.isProfile = True
            self.imageRight.isProfile = True
            self.leProfile.show()
            self.comboBox.hide()
        else:
            self.imageTop.isProfile = False
            self.imageLeft.isProfile = False
            self.imageRight.isProfile = False
            self.leProfile.hide()
            self.comboBox.show()

    @pyqtSlot()
    def on_CameraChange(self):
        if self.tabWidget.currentIndex()==0:
            self.imageTop.setImageScale()
            self.imageTop.SetProfile(self.leProfile.text(), "top.jpg")
            self.pixmap = QPixmap('iphone6s_3_s1.jpg')
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageTop.imagepixmap = self.pixmap
            self.imageTop.SetCamera(ImageLabel.CAMERA.TOP)
            self.imageTop.SetProfile("iphone6s_top_1","iphone6s_top_1.jpg")
        elif self.tabWidget.currentIndex()==1:
            self.imageLeft.setImageScale()
            self.imageLeft.SetProfile(self.leProfile.text(), "left.jpg")
            self.pixmap = QPixmap('/home/pi/Desktop/pyUI/curimage.jpg')
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageLeft.imagepixmap = self.pixmap
            self.imageLeft.SetCamera(ImageLabel.CAMERA.LEFT)
            self.imageTop.SetProfile("iphone6s_top_2","iphone6s_top_2.jpg")
        else:
            self.imageRight.setImageScale()
            self.imageRight.SetProfile(self.leProfile.text(), "right.jpg")
            self.pixmap = QPixmap('/home/pi/Desktop/pyUI/iphone6s_3_s1.jpg')
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageRight.imagepixmap = self.pixmap
            self.imageRight.SetCamera(ImageLabel.CAMERA.RIGHT)


    @pyqtSlot()
    def on_settingclick(self):
        dlg = Settings(self)
        if dlg.exec_():
            print("Success!")
        else:
            print("Cancel!")        

    @pyqtSlot()
    def on_click(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Image UP':
            self.index+=1
            self.DrawImage(50,50)           
        else:
            self.index-=1
            self.PreviewCamera()

    @pyqtSlot()
    def on_startclick(self):
        if self.leProfile.text()=="" and self.checkBox.isChecked():
            error_dialog = QtWidgets.QErrorMessage(self)
            error_dialog.showMessage('Oh no! Profile name is empty.') 
            return             
        self.imageTop.setImageScale()

        self.pixmap = QPixmap('/home/pi/Desktop/pyUI/iphone6s_3_s1.jpg')
        logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
        self.imageTop.imagepixmap = self.pixmap
        return

        self.filepath = '/home/pi/Desktop/pyUI/curimage.jpg'
        with picamera.PiCamera() as camera:
            camera.resolution = (3280, 2464)
            camera.start_preview()
            camera.capture(self.filepath)
            camera.stop_preview()   

        self.pixmap = QPixmap(self.filepath)
        logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
        self.imageTop.imagepixmap = self.pixmap
        #self.lblImage.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation)) 
        #logging.info(str(self.lblImage.pixmap().width())+"X"+str(self.lblImage.pixmap().height()))
        #logging.info(str(self.w)+"X"+str(self.h))   


 
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    app = QApplication(sys.argv)
    #listImages('C:/Users/jefferyz/Desktop/pictures/')
    window = UISettings()
 
    window.show()
    window.showFullScreen()
     
    logging.info(str(window.width())+"X"+str(window.height()))   
    sys.exit(app.exec_())
