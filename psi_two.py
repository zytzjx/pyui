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
from datetime import datetime

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
        self.pbKeyBoard.clicked.connect(self.on_KeyBoardclick)
        self.checkBox.stateChanged.connect(self.btnstate)
        self.tabWidget.currentChanged.connect(self.on_CameraChange)
        self.leProfile.hide()
        self.previewEvent = threading.Event()
        self.imageTop.SetCamera(ImageLabel.CAMERA.TOP)
        self.imageLeft.SetCamera(ImageLabel.CAMERA.LEFT)
        self.imageRight.SetCamera(ImageLabel.CAMERA.RIGHT)
        self.takelock=threading.Lock()
        self.startKey =False
        self.client = ServerProxy("http://192.168.1.12:8888", allow_none=True)
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

    def StatusChange(self, value):
        self.takelock.acquire()
        print("value is :"+str(value))
        self.takelock.release()

    #@staticmethod
    def createKeyboard(self):
        #subprocess.Popen(["killall","matchbox-keyboa"])
        #self.keyboardID = 0
        if self.keyboardID == 0:
            p = subprocess.Popen(["matchbox-keyboard", "--xid"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.keyboardID = int(p.stdout.readline())
            threading.Thread(target=lambda : print(p.stdout.readline())).start()
            self.startKey = True
            logging.debug("capturing window 0x%x ", self.keyboardID)
            embed_window = QtGui.QWindow.fromWinId(self.keyboardID)
            embed_widget = QtWidgets.QWidget.createWindowContainer(embed_window)
            embed_widget.setMinimumWidth(580)
            embed_widget.setMinimumHeight(280)
            hbox2 = QHBoxLayout()
            hbox2.addWidget(embed_widget)
            self.wdtKeyBoard.setLayout(hbox2)



    def ShowKeyBoard(self):
        try:
            if self.startKey:
                self.wdtKeyBoard.hide()
                self.startKey = False
                return

            self.createKeyboard()
            if self.keyboardID == 0:
                return
            self.wdtKeyBoard.show()
            self.startKey = True
            #elf.wdtKeyBoard.resize(580, 280)
        except:
            pass


    def createprofiledirstruct(self, profiename):
        if os.path.isfile('config.json'):
            with open('config.json') as json_file:
                self.config = json.load(json_file)

        self.client = ServerProxy("http://192.168.1.12:8888", allow_none=True)

        if profiename == '':
            return False
        
        pathleft = os.path.join(self.config["profilepath"], profiename, "left")
        pathtop = os.path.join(self.config["profilepath"], profiename, "top")
        pathright = os.path.join(self.config["profilepath"], profiename, "right")
        mode = 0o777
        #os.makedirs(pathleft, mode, True) 
        #os.makedirs(pathtop, mode, True) 
        #os.makedirs(pathright, mode, True) 

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
        self.createprofiledirstruct("")
        fpath=self.config["profilepath"]
        #client = ServerProxy("http://localhost:8888", allow_none=True)
        self.comboBox.addItems(self.client.updateProfile(fpath))
        #curpath=os.path.abspath(os.path.dirname(sys.argv[0]))
        #profilepath=os.path.join(curpath,"profiles")
        #self.comboBox.addItems([name for name in os.listdir(profilepath) if os.path.isdir(os.path.join(profilepath, name))])

    @staticmethod
    def createSShServer():
        from paramiko import SSHClient
        ssh = SSHClient()
        ssh.load_system_host_keys()
        ssh.connect('192.168.1.12', username='pi', password='qa', look_for_keys=False)
        _, stdout, _ = ssh.exec_command('python3 ~/Desktop/pyUI/servertask.py &')

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
    '''
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
    '''

    @pyqtSlot()
    def on_CameraChange(self):
        return


    @pyqtSlot()
    def on_KeyBoardclick(self):
        self.ShowKeyBoard()

    @pyqtSlot()
    def on_settingclick(self):
        dlg = Settings(self)
        if dlg.exec_():
            print("Success!")
        else:
            print("Cancel!")  

        #self.ShowKeyBoard()      

    @pyqtSlot()
    def on_click(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Image UP':
            self.previewEvent.set() 
        else:
            self.OnPreview()

    def _showImage(self, index, imagelabel, client):
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing %d" % index)
        client.TakePicture(index)   
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start transfer %d" % index)
        imagelabel.setImageScale()     
        data = client.imageDownload(index).data
        print(datetime.now().strftime("%H:%M:%S.%f"),"end testing %d" % index)
        image = Image.open(io.BytesIO(data))
        imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
        pixmap = QPixmap.fromImage(imageq)
        imagelabel.imagepixmap = pixmap

    def _drawtestScrew(self, index, imagelabel, data):
        ret=0
        for itemscrew in range(data):
            if itemscrew[0] < 0.35:
                ret = 2
                imagelabel.DrawImageResult(itemscrew[1], Qt.red)               
            elif itemscrew[0] >= 0.45:
                imagelabel.DrawImageResult(itemscrew[1], Qt.green)
            else:
                if ret != 2:
                    ret= 1 
                imagelabel.DrawImageResult(itemscrew[1], Qt.yellow)               

        return ret

    def _ThreadTakepicture(self):
        #client = ServerProxy("http://localhost:8888", allow_none=True)
        self.client.profilepath('/home/pi/Desktop/pyUI/profiles', 'aaa')
        self.takelock.acquire()
        status, status1, status2 = 0, 0, 0
        try:
            self._showImage(0, self.imageTop, self.client)

            self._showImage(1, self.imageLeft, self.client)

            self._showImage(2, self.imageRight, self.client)

            status=self._drawtestScrew(0, self.imageTop, self.client.ResultTest(0))        
            status1=self._drawtestScrew(1, self.imageLeft, self.client.ResultTest(1))
            status2=self._drawtestScrew(2, self.imageRight, self.client.ResultTest(2))
        except :
            status = 5
        finally:
            self.takelock.release()

        status = max([status, status1, status2])
        if status==0:
            self.lblStatus.setText("success")
            self.lblStatus.setStyleSheet('''
            color: green
            ''')
        elif status==1:
            self.lblStatus.setText("finish")
            self.lblStatus.setStyleSheet('''
            color: yellow
            ''')
        else:
            self.lblStatus.setText("Error")
            self.lblStatus.setStyleSheet('''
            color: red
            ''')

    @pyqtSlot()
    def on_startclick(self):
        if self.leProfile.text()=="" and self.checkBox.isChecked():
            error_dialog = QtWidgets.QErrorMessage(self)
            error_dialog.showMessage('Oh no! Profile name is empty.') 
            return             

        threading.Thread(target=self._ThreadTakepicture).start()
        return

    def _shutdown(self):
        #client = ServerProxy("http://localhost:8888", allow_none=True)
        self.client.CloseServer()


    def _GetImageShow(self):
        #from PIL import Image
        #import urllib.request

        #client = ServerProxy("http://localhost:8888", allow_none=True)
        #url = 'http://127.0.0.1:5000/startpause'
        #urllib.request.urlopen(url)
        logging.info(self.client.startpause())
        time.sleep(0.1)
        while True:
            #url = 'http://127.0.0.1:5000/preview'
            data = self.client.preview().data
            image = Image.open(io.BytesIO(data))
            imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
            pixmap = QPixmap.fromImage(imageq)
            self.imageTop.imagepixmap = pixmap
            if self.previewEvent.is_set():
                self.previewEvent.clear()
                #url = 'http://127.0.0.1:5000/startpause'
                #urllib.request.urlopen(url)
                self.client.startpause()
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
    UISettings.createSShServer()
    app = QApplication(sys.argv)
    #listImages('C:/Users/jefferyz/Desktop/pictures/')
    window = UISettings()
 
    window.show()
    window.showFullScreen()

    threading.Thread(target=window.ChangeTab).start()

    logging.info(str(window.width())+"X"+str(window.height()))   
    sys.exit(app.exec_())
