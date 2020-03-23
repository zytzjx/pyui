#!/usr/bin/env python3
import sys
import os
import io
import time
import picamera
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal
from PyQt5 import QtWidgets,  QtGui
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit, QHBoxLayout)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi
import logging
import settings
from settings import Settings
import ImageLabel
import json
import threading

from  serialstatus import FDProtocol
import serial
from xmlrpc.client import ServerProxy
import xmlrpc.client

import subprocess

files = []

#CURSOR_NEW = QtGui.QCursor(QtGui.QPixmap('cursor.png'))

def listImages(path):
#path = 'c:\\projects\\hc2\\'
    # r=root, d=directories, f = files
    for r, _, f in os.walk(path):
        for file in f:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(r, file))

class StatusCheckThread(QThread):
#https://kushaldas.in/posts/pyqt5-thread-example.html
    signal = pyqtSignal(int)
    def __init__(self):
        QThread.__init__(self)
        self.serialport = "/dev/ttyUSB0"
        self.exit_event = threading.Event()

    # run method gets called when we start the thread
    def run(self):
        ser = serial.serial_for_url('alt://{}'.format(self.serialport), baudrate=9600, timeout=1)
    #ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1)
        status=-1
        with serial.threaded.ReaderThread(ser, FDProtocol) as statusser:
            while not self.exit_event.is_set():
                if statusser.proximityStatus and not statusser.ultraSonicStatus:
                    if status!=1:
                        status=1
                        #do task start
                elif not statusser.proximityStatus:
                    if status!=2:
                        status=2
                        #start preview
                elif statusser.ultraSonicStatus:
                    if status != 3:
                        status = 3
                self.signal.emit(status)
                #time.sleep(0.05)
                self.msleep(50)

class UISettings(QDialog):
    """Settings dialog widget
    """
    #filepath=""
    pixmap = None
    keyboardID=0
    resized = pyqtSignal()
    def __init__(self, parent=None):
        super(UISettings, self).__init__()
        loadUi('psi_auto.ui', self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.changeStyle('Fusion')
        self.pbClose.clicked.connect(self.closeEvent)
        self.pbImageChange.clicked.connect(self.on_click)
        self.pbImageChangeDown.clicked.connect(self.on_click)
        self.pbStart.clicked.connect(self.on_startclick)
        self.updateProfile()
        #self.resized.connect(self.someFunction)
        self.pbSetting.clicked.connect(self.on_settingclick)
        self.checkBox.stateChanged.connect(self.btnstate)
        self.tabWidget.currentChanged.connect(self.on_CameraChange)
        self.leProfile.hide()
        self.previewEvent = threading.Event()
        self.imageTop.SetCamera(ImageLabel.CAMERA.TOP)
        self.imageLeft.SetCamera(ImageLabel.CAMERA.LEFT)
        self.imageRight.SetCamera(ImageLabel.CAMERA.RIGHT)
        self.takelock=threading.Lock()
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

        self.config=settings.DEFAULTCONFIG

        self.serialThread = StatusCheckThread()
        self.serialThread.signal.connect(self.StatusChange)
        #self.serialThread.start()

        self.threadPreview=None
        #self.on_CameraChange()
        #self.setWindowOpacity(0.5) 
        #self.setAttribute(Qt.WA_TranslucentBackground) 

        #self.resize(800, 600) 
    #def mouseMoveEvent(self, evt: QMouseEvent) -> None:
    #    logging.info(str(evt.pos().x())+"=="+str(evt.pos().y())) 
    #    super(UISettings, self).mouseMoveEvent(evt)

    #def mousePressEvent(self, evt: QMouseEvent) -> None:
    #    logging.info(str(evt.pos().x())+"=>"+str(evt.pos().y())) 
    #    super(UISettings, self).mousePressEvent(evt)

    def StatusChange(self, value):
        self.takelock.acquire()
        print("value is :"+str(value))
        self.takelock.release()

    #@staticmethod
    def createKeyboard(self):
        subprocess.Popen(["killall","matchbox-keyboa"])
        self.keyboardID = 0
        
        p = subprocess.Popen(["matchbox-keyboard", "--xid"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.keyboardID = int(p.stdout.readline())
        threading.Thread(target=lambda : print(p.stdout.readline())).start()


    def ShowKeyBoard(self):
        try:
            self.createKeyboard()
            if self.keyboardID == 0:
                return
            logging.debug("capturing window 0x%x ", self.keyboardID)
            embed_window = QtGui.QWindow.fromWinId(self.keyboardID)
            embed_widget = QtWidgets.QWidget.createWindowContainer(embed_window)
            infoWindow2 = QDialog(parent=self)
            embed_widget.setMinimumWidth(580)
            embed_widget.setMinimumHeight(280)
            hbox2 = QHBoxLayout()
            hbox2.addWidget(embed_widget)
            infoWindow2.setLayout(hbox2)
            infoWindow2.show()
        except:
            pass
        #rect = self.geometry()
        #self.infoWindow2.setGeometry(rect.x()+rect.width(), rect.y()+rect.height(), 400, 300)
        #self.move(rect.x()+rect.width(), rect.y()+rect.height())
        #hbox2 = QHBoxLayout()
        #hbox2.addWidget(embed_widget)
        #infoWindow2.setLayout(hbox2)
        #infoWindow2.show()


    def createprofiledirstruct(self, profiename):
        if profiename == '':
            return False
        
        if os.path.isfile('config.json'):
            with open('config.json') as json_file:
                self.config = json.load(json_file)
        '''
        pathleft = os.path.join(self.config["profilepath"], profiename, "left")
        pathtop = os.path.join(self.config["profilepath"], profiename, "top")
        pathright = os.path.join(self.config["profilepath"], profiename, "right")
        mode = 0o777
        os.makedirs(pathleft, mode, True) 
        os.makedirs(pathtop, mode, True) 
        os.makedirs(pathright, mode, True) '''

    def closeEvent(self, event):
        self._shutdown()
        self.serialThread.exit_event.set()
        self.close()


    def resizeEvent(self, event):
        self.resized.emit()
        return super(UISettings, self).resizeEvent(event)

    '''def someFunction(self):
        logging.info(str(self.width())+"X"+str(self.height()))   '''

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        QApplication.setPalette(QApplication.style().standardPalette())

    def updateProfile(self):
        curpath=os.path.abspath(os.path.dirname(sys.argv[0]))
        profilepath=os.path.join(curpath,"profiles")
        self.comboBox.addItems([name for name in os.listdir(profilepath) if os.path.isdir(os.path.join(profilepath, name))])

    '''    
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
        #qimage = QImage(imageq)
        #pixmap = QPixmap(qimage)
        pixmap = QPixmap.fromImage(imageq)
        self.imageTop.imagepixmap = pixmap
        #self.lblImage.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))   
    '''

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

    def takephotoshow(self, cameraindex, picname, profilename):
        #self.takephoto           

        if ImageLabel.CAMERA.TOP==cameraindex:
            self.imageTop.profilerootpath = self.config["profilepath"]
            self.imageTop.setImageScale()
            self.imageTop.SetProfile(profilename, "top.jpg")
            self.pixmap = QPixmap(picname)
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageTop.imagepixmap = self.pixmap
            self.imageTop.SetCamera(ImageLabel.CAMERA.TOP)
            #self.imageTop.SetProfile("iphone6s_top_1","iphone6s_top_1.jpg")
        elif ImageLabel.CAMERA.LEFT==cameraindex:
            self.imageLeft.profilerootpath = self.config["profilepath"]
            self.imageLeft.setImageScale()
            self.imageLeft.SetProfile(profilename, "left.jpg")
            self.pixmap = QPixmap(picname)
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageLeft.imagepixmap = self.pixmap
            self.imageLeft.SetCamera(ImageLabel.CAMERA.LEFT)
            #self.imageTop.SetProfile("iphone6s_top_2","iphone6s_top_2.jpg")
        else:
            self.imageRight.profilerootpath = self.config["profilepath"]
            self.imageRight.setImageScale()
            self.imageRight.SetProfile(profilename, "right.jpg")
            self.pixmap = QPixmap(picname)
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageRight.imagepixmap = self.pixmap
            self.imageRight.SetCamera(ImageLabel.CAMERA.RIGHT)


    @pyqtSlot()
    def on_CameraChange(self):
        return


    @pyqtSlot()
    def on_settingclick(self):
        '''dlg = Settings(self)
        if dlg.exec_():
            print("Success!")
        else:
            print("Cancel!")  '''

        self.ShowKeyBoard()      

    @pyqtSlot()
    def on_click(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Image UP':
            self.previewEvent.set() 
        else:
            self.OnPreview()

    def _showImage(self, index, imagelabel):
        client.TakePicture(index)   
        imagelabel.setImageScale()     
        data = client.imageDownload(index).data
        image = Image.open(io.BytesIO(data))
        imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
        pixmap = QPixmap.fromImage(imageq)
        imagelabel.imagepixmap = pixmap

    def _drawtestScrew(self, index, imagelabel, data):
        ret=True
        for itemscrew in range(data):
            if itemscrew[0] < 0.60:
                print(data[1])
                ret = False
                imagelabel.DrawImageResult(itemscrew[1])
        return ret

    def _ThreadTakepicture(self):
        self.takelock.acquire()
        client = ServerProxy("http://localhost:8888", allow_none=True)
        client.profilepath('/home/pi/Desktop/pyUI/profiles', 'aaa')
        
        self._showImage(0, self.imageTop)

        self._showImage(1, self.imageLeft)

        self._showImage(2, self.imageRight)

        self._drawtestScrew(index, self.imageTop, client.ResultTest(0))
        self._drawtestScrew(index, self.imageLeft, client.ResultTest(1))
        self._drawtestScrew(index, self.imageRight, client.ResultTest(2))

        self.takelock.release()


    @pyqtSlot()
    def on_startclick(self):
        if self.leProfile.text()=="" and self.checkBox.isChecked():
            error_dialog = QtWidgets.QErrorMessage(self)
            error_dialog.showMessage('Oh no! Profile name is empty.') 
            return             

        threading.Thread(target=self._ThreadTakepicture).start()
        #self.createprofiledirstruct(self.leProfile.text())
        #self.on_CameraChange()
        #self.imageTop.setImageScale()

        #self.pixmap = QPixmap('/home/pi/Desktop/pyUI/iphone6s_3_s1.jpg')
        #logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
        #self.imageTop.imagepixmap = self.pixmap
        return

    def _shutdown(self):
        client = ServerProxy("http://localhost:8888", allow_none=True)
        client.CloseServer()


    def _GetImageShow(self):
        #from PIL import Image
        #import urllib.request

        client = ServerProxy("http://localhost:8888", allow_none=True)
        #url = 'http://127.0.0.1:5000/startpause'
        #urllib.request.urlopen(url)
        logging.info(client.startpause())
        time.sleep(0.1)
        while True:
            #url = 'http://127.0.0.1:5000/preview'
            data = client.preview().data
            image = Image.open(io.BytesIO(data))
            imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
            pixmap = QPixmap.fromImage(imageq)
            self.imageTop.imagepixmap = pixmap
            if self.previewEvent.is_set():
                self.previewEvent.clear()
                #url = 'http://127.0.0.1:5000/startpause'
                #urllib.request.urlopen(url)
                client.startpause()
                break

    def ChangeTab(self):
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(0)
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(1)
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(2)
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(0)

    def OnPreview(self):
        if self.threadPreview==None or not self.threadPreview.is_alive():
            self.threadPreview= threading.Thread(target=self._GetImageShow)
            self.threadPreview.start()
 
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    app = QApplication(sys.argv)
    #listImages('C:/Users/jefferyz/Desktop/pictures/')
    window = UISettings()
 
    window.show()
    window.showFullScreen()

    threading.Thread(target=window.ChangeTab).start()

    logging.info(str(window.width())+"X"+str(window.height()))   
    sys.exit(app.exec_())
