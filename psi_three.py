#!/usr/bin/python3
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
from multiprocessing import Process
from datetime import datetime
import shutil

from  serialstatus import FDProtocol
import serial
from xmlrpc.client import ServerProxy
import xmlrpc.client

import subprocess
import numpy as np

import testScrew
import myconstdef

files = []

#CURSOR_NEW = QtGui.QCursor(QtGui.QPixmap('cursor.png'))

def listImages(path):
#path = 'c:\\projects\\hc2\\'
    # r=root, d=directories, f = files
    for r, _, f in os.walk(path):
        for file in f:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(r, file))

class DrawPicThread(QThread):
    #signal = pyqtSignal('PyQt_PyObject')
    def __init__(self, imagelabel, index):
        QThread.__init__(self)
        self.imagelabel=imagelabel
        self.index = index

    def run(self):
        import testrsync
        logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync++")
        #process = subprocess.Popen(["rsync", "-avzP", '--delete', '/tmp/ramdisk', "pi@192.168.1.16:/tmp/ramdisk"],
        #    stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #process.stdin.write(b'qa\n')
        #process.communicate()[0]
        #process.wait()
        testrsync.rsync()
        logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync--")
        #process.stdin.close()
        self.imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % self.index)#pixmap

        #status = self.imagelabel.DrawImageResults(self.data)
        #self.signal.emit((self.index, status))


class StatusCheckThread(QThread):
#https://kushaldas.in/posts/pyqt5-thread-example.html
    signal = pyqtSignal(int)
    def __init__(self):
        QThread.__init__(self)
        self.serialport = "/dev/ttyUSB0"
        self.exit_event = threading.Event()
        self.threhold = 8000

    def setThrehold(self, value):
        self.threhold = value
    # run method gets called when we start the thread
    def run(self):
        ser = serial.serial_for_url('alt://{}'.format(self.serialport), baudrate=115200, timeout=1)
    #ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1)
        status=-1
        oldstatus=-1
        with serial.threaded.ReaderThread(ser, FDProtocol) as statusser:
            while not self.exit_event.is_set():
                statusser.setProxThreshold(self.threhold)
                if statusser.proximityStatus and statusser.laserStatus:
                    if status!=1:
                        status=1
                        #do task start
                elif not statusser.proximityStatus:
                    if status!=2:
                        status=2
                        #start preview
                elif not statusser.laserStatus:
                    if status != 3:
                        status = 3
                if oldstatus!=status:
                    self.signal.emit(status)
                    oldstatus = status
                #time.sleep(0.05)
                self.msleep(50)

class UISettings(QDialog):
    """Settings dialog widget
    """
    #filepath=""
    keyboardID=0
    resized = pyqtSignal()
    def __init__(self, parent=None):
        super(UISettings, self).__init__()
        loadUi('/home/pi/Desktop/pyUI/psi_auto.ui', self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.changeStyle('Fusion')
        self.pbClose.clicked.connect(self.closeEvent)
        self.pbImageChange.clicked.connect(self.on_click)
        self.pbImageChangeDown.clicked.connect(self.on_click)
        self.pbStart.clicked.connect(self.on_startclick)
        self.serialThread = StatusCheckThread()
        self.config=settings.DEFAULTCONFIG
        self.updateProfile()
        #self.resized.connect(self.someFunction)
        self.pbSetting.clicked.connect(self.on_settingclick)
        self.pbKeyBoard.clicked.connect(self.on_KeyBoardclick)
        self.checkBox.stateChanged.connect(self.btnstate)
        self.tabWidget.currentChanged.connect(self.on_CameraChange)
        self.comboBox.currentTextChanged.connect(self.OnChangeItem)
        self.leProfile.hide()
        self.previewEvent = threading.Event()
        self.imageTop.SetCamera(ImageLabel.CAMERA.TOP)
        self.imageLeft.SetCamera(ImageLabel.CAMERA.LEFT)
        self.imageRight.SetCamera(ImageLabel.CAMERA.RIGHT)
        self.takelock=threading.Lock()
        self.takepic=threading.Event()
        self.stop_prv = threading.Event()
        self.startKey =False
        self.clientleft = ServerProxy(myconstdef.URL_LEFT, allow_none=True)
        self.clientright = ServerProxy(myconstdef.URL_RIGHT, allow_none=True)
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

        self.serialThread.signal.connect(self.StatusChange)
 
        self.threadPreview=None
        #self.imageResults=[0]*3
        self.profileimages=["","",""]
        self.imageresults = []
        self.yanthread=None
        self._profilepath=""
        self.profilename=""

    def StatusChange(self, value):
        self.takelock.acquire()
        print("value is :"+str(value))
        if (value == 2):
            self.OnPreview()
        elif(value == 1):
            self.previewEvent.set() 
            time.sleep(0.1)
            #start process
            #self.on_startclick()
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


    def OnChangeItem(self, value):
        index = self.comboBox.currentIndex()
        if(index>=0):
            self.config['comboxindex'] = index
        self._saveConfigFile()
        
        self.profileimages[0]=os.path.join(self.config["profilepath"], self.comboBox.currentText(), "top", self.comboBox.currentText()+".jpg")
        self.profileimages[1]=os.path.join(self.config["profilepath"], self.comboBox.currentText(), "left", self.comboBox.currentText()+".jpg")
        self.profileimages[2]=os.path.join(self.config["profilepath"], self.comboBox.currentText(), "right", self.comboBox.currentText()+".jpg")


    def _saveConfigFile(self):
        with open('config.json', 'w') as json_file:
            json.dump(self.config, json_file, indent=4)

    def _loadConfigFile(self):
        if os.path.isfile('config.json'):
            with open('config.json') as json_file:
                self.config = json.load(json_file)
        self.serialThread.setThrehold(self.config["threhold"] if 'threhold' in self.config else 20000)


    def createprofiledirstruct(self, profiename):
        self._loadConfigFile()
        self.clientleft = ServerProxy(myconstdef.URL_LEFT, allow_none=True)
        self.clientright = ServerProxy(myconstdef.URL_RIGHT, allow_none=True)
        self.imageLeft.setServerProxy(self.clientleft)
        self.imageRight.setServerProxy(self.clientright)

    def closeEvent(self, event):
        self.stop_prv.set()
        while self.threadPreview.is_alive():
            time.sleep(0.1)
        self._shutdown()
        self.serialThread.exit_event.set()
        self.close()


    def resizeEvent(self, event):
        self.resized.emit()
        return super(UISettings, self).resizeEvent(event)

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        QApplication.setPalette(QApplication.style().standardPalette())

    def updateProfile(self):
        self.createprofiledirstruct("")
        self._profilepath=self.config["profilepath"]
        self.comboBox.addItems([name for name in os.listdir(self._profilepath) if os.path.isdir(os.path.join(self._profilepath, name))])
        self.comboBox.setCurrentIndex(self.config["comboxindex"] if 'comboxindex' in self.config and self.config["comboxindex"]<self.comboBox.count() else 0)

    @staticmethod
    def createSShServer():
        from paramiko import SSHClient
        import paramiko
        ssh = SSHClient()
        #ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=myconstdef.IP, username='pi', password=myconstdef.PSSWORD, look_for_keys=False)

        stdin, stdout, stderr = ssh.exec_command('DISPLAY=:0.0 python3 ~/Desktop/pyUI/serversingletask.py &')
        bErrOut = True
        
        for line in stdout.read().splitlines():
            bErrOut = False
            break

        if bErrOut:
            for line in stderr.read().splitlines():
                print(line)
                break
        
        ssh.close()


    def PreviewCamera(self):
        # Create the in-memory stream
        logging.info("preview: thread is starting...")
        self.stop_prv.clear()
        #while not self.stop_prv.is_set():
        stream = io.BytesIO()
        with picamera.PiCamera() as camera:
            camera.ISO = 50
            camera.resolution=(640,480)
            for foo in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
                if self.stop_prv.is_set():
                    self.stop_prv.clear()
                    break
                stream.truncate()
                stream.seek(0)
                image = Image.open(stream)
                imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
                pixmap = QPixmap.fromImage(imageq)
                self.imageTop.ShowPreImage(pixmap)
                #self.imageTop.pixmap = pixmap
                stream.seek(0)
                stream.truncate()

                if self.stop_prv.is_set():
                    self.stop_prv.clear()
                    break
                    
            camera.close()
 
        self.stop_prv.clear()
        logging.info("preview: thread ending...")

    def _GetImageShow(self):
        self.imageTop.setImageScale() 
        logging.info(self.clientleft.startpause(False))
        while True:
            data = self.clientleft.preview().data
            image = Image.open(io.BytesIO(data))
            imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
            pixmap = QPixmap.fromImage(imageq)
            #self.imageTop.imagepixmap = pixmap
            self.imageTop.ShowPreImage(pixmap)
            if self.previewEvent.is_set():
                self.previewEvent.clear()
                self.clientleft.startpause(True)
                break


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
            self.comboBox.clear() 
            self.comboBox.addItems([name for name in os.listdir(self.config["profilepath"]) if os.path.isdir(os.path.join(self.config["profilepath"], name))])
            self.comboBox.setCurrentIndex(self.config["comboxindex"] if 'comboxindex' in self.config and self.config["comboxindex"]<self.comboBox.count() else 0)
            self.comboBox.show()
            tl = Process(target=self.runsyncprofiles, args=(True,))
            tl.start()
            tr = Process(target=self.runsyncprofiles, args=(False,))
            tr.start()
            tl.join()
            tr.join()

    @pyqtSlot()
    def on_CameraChange(self):
        return


    @pyqtSlot()
    def on_KeyBoardclick(self):
        self.ShowKeyBoard()

    @pyqtSlot()
    def on_settingclick(self):
        dlg = Settings(self, self.clientleft, self.clientright)
        if dlg.exec_():
            self._loadConfigFile()
            print("Success!")
        else:
            print("Cancel!")  

        #self.ShowKeyBoard()      

    @pyqtSlot()
    def on_click(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Image UP':
            self.stop_prv.set() 
        else:
            self.OnPreview()
    
    def _DirSub(self, argument):
        switcher = {
            1: "left",
            0: "top",
            2: "right",
        }
        return switcher.get(argument, "Invalid")

    def runsyncprofiles(self, isLeft):
        ip = myconstdef.IP_LEFT
        if not isLeft:
            ip = myconstdef.IP_RIGHT
        
        cmd = 'rsync -avz -e ssh pi@{0}:{1}/ {1}/'.format(ip, self.config["profilepath"])
        os.system(cmd)

    def capture(self, cam, IsDetect=True):
        cmd = "raspistill -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        logging.info(cmd)
        os.system(cmd)
        if not IsDetect:
            shutil.copyfile("/tmp/ramdisk/phoneimage_%d.jpg" % cam, os.path.join(self._profilepath, self._DirSub(cam), self.profilename+".jpg"))
        else:
            self._callyanfunction(cam)

    def _callyanfunction(self, index):
        self.profilename= self.leProfile.text() if self.checkBox.isChecked() else self.comboBox.currentText()
        logging.info('callyanfunction:' + self.profilename)
        txtfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".txt")
        smplfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".jpg")
        logging.info(txtfilename)
        logging.info(smplfilename)
        if os.path.exists(txtfilename) and os.path.exists(smplfilename):
            logging.info("*testScrews**")
            try:
                self.imageresults = testScrew.testScrews(
                    txtfilename, 
                    smplfilename, 
                    "/tmp/ramdisk/phoneimage_%d.jpg" % index)
            except :
                self.imageresults = []
                pass
            
            logging.info("-testScrews end--")
            logging.info(self.imageresults)

    def _startdetectthread(self, index):
        self.yanthread = Process(target=self._callyanfunction, args=(index,))
        self.yanthread.start()
        self.yanthread.join()

    def _showImage(self, index, imagelabel):
        imagelabel.setImageScale()     
        logging.info("Start testing %d" % index)
        if index==1:
            self.clientleft.TakePicture(index, not self.checkBox.isChecked()) 
        elif index==2:
            self.clientright.TakePicture(index, not self.checkBox.isChecked())  
        elif index == 0:
            self.capture(0, not self.checkBox.isChecked())

        logging.info("Start transfer %d" % index)
        if self.checkBox.isChecked():
            if index==0:
                imagelabel.SetProfile(self.profilename, self.profilename+".jpg")
                imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % index)#pixmap
            else:
                data = self.clientleft.imageDownload(index).data if index == 1 else self.clientright.imageDownload(index).data
                logging.info("end testing %d" % index)
                image = Image.open(io.BytesIO(data))
                image.save("/tmp/ramdisk/temp_%d.jpg" % index)
                #imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
                #pixmap = QPixmap.fromImage(imageq)
                imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/temp_%d.jpg" % index)#pixmap
        else:
            imagelabel.SetProfile(self.leProfile.text(), self.leProfile.text()+".jpg")
            if index==0:
                imagelabel.ShowPreImage(QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % index))
            else:
                pass

    def _drawtestScrew(self, index, imagelabel):
        ret=0
        if index==0:
            ret = imagelabel.DrawImageResults(self.imageresults)
        else:
            ss = self.clientleft.ResultTest(index) if index==1 else self.clientright.ResultTest(index)
            ret = imagelabel.DrawImageResults(json.loads(ss))
        return ret

    def _ThreadTakepictureLeft(self):
        try:
            self._showImage(1, self.imageLeft)
        except Exception as ex:
            logging.info(str(ex))
            status = 5

        logging.info("ending camera Left and transfer")

    def _ThreadTakepictureRight(self):
        try:
            self._showImage(2, self.imageRight)
        except Exception as ex:
            logging.info(str(ex))
            status = 5

        logging.info("ending camera right and transfer")


    def _ThreadTakepicture(self):
        #self.takelock.acquire()
        #status, status1, status2 = 0, 0, 0
        self.takepic.clear()
        try:
            self._showImage(0, self.imageTop)
        except Exception as ex:
            logging.info(str(ex))
            status = 5
        #finally:
        #    self.takelock.release()

        logging.info("ending camera A and transfer")
        self.takepic.set()

    def testScrewResult(self, data):
        ret = 0
        for itemscrew in data:
            if itemscrew[0] == np.nan or itemscrew[0] < 0.35:
                ret = 2
                break
            elif itemscrew[0] >= 0.45:
                pass
            else:
                if ret != 2:
                    ret= 1 

        return ret

    def DrawResultTop(self):
        self.imageTop.DrawImageResults(self.imageresults, None )

    def DrawResultLeft(self):
        data = json.loads(self.clientleft.ResultTest(1))
        if len(data)>0:
            #status1 = self.testScrewResult(data)
            status1 = self.imageLeft.DrawImageResults(data, QPixmap(self.profileimages[1]))

    def DrawResultRight(self):
        data = json.loads(self.clientright.ResultTest(2))
        if len(data)>0:
            #status2 = self.testScrewResult(data)
            status2 = self.imageRight.DrawImageResults(data, QPixmap(self.profileimages[2]))


    @pyqtSlot()
    def on_startclick(self):
        if self.leProfile.text()=="" and self.checkBox.isChecked():
            error_dialog = QtWidgets.QErrorMessage(self)
            error_dialog.showMessage('Oh no! Profile name is empty.') 
            return             
        
        self.stop_prv.set() 
        self.profilename= self.leProfile.text() if self.checkBox.isChecked() else self.comboBox.currentText()
        self.clientleft.profilepath(self.config["profilepath"], self.profilename)
        self.clientright.profilepath(self.config["profilepath"], self.profilename)        
        self._profilepath = os.path.join(self.config["profilepath"], self.profilename)
        pathleft = os.path.join(self.config["profilepath"], self.profilename, "left")
        pathtop = os.path.join(self.config["profilepath"], self.profilename, "top")
        pathright = os.path.join(self.config["profilepath"], self.profilename, "right")
        if self.checkBox.isChecked():
            mode = 0o777
            os.makedirs(pathleft, mode, True) 
            os.makedirs(pathtop, mode, True) 
            os.makedirs(pathright, mode, True) 
            
        self.profileimages[0]=os.path.join(pathtop,  self.profilename+".jpg")
        self.profileimages[1]=os.path.join(pathleft,  self.profilename+".jpg")
        self.profileimages[2]=os.path.join(pathright,  self.profilename+".jpg")
        if self.stop_prv.is_set():
            time.sleep(0.2)  

        logging.info("Start testing click")

        logging.info("Start testing t")
        p = threading.Thread(target=self._ThreadTakepicture)
        p.start()
        pLeft = Process(target=self._ThreadTakepictureLeft)
        pLeft.start()
        pRight = Process(target=self._ThreadTakepictureRight)
        pRight.start()
        p.join()
        logging.info("Start end t")        
        pLeft.join()
        logging.info("Start end left")        
        pRight.join()
        logging.info("Start end right")        
        if not self.checkBox.isChecked():
            status, status1, status2 = 0, 0, 0
            #self.takepic.wait()
            #self.takepic.clear()
            try:
                logging.info("Start Draw Info")
                
                threads=[]
                ttop = threading.Thread(target=self.DrawResultTop)
                ttop.start()
                threads.append(ttop)
                logging.info("Draw top finish")
                
                tleft = threading.Thread(target=self.DrawResultLeft)
                tleft.start()
                threads.append(tleft)
                logging.info("Draw left finish")

                tright = threading.Thread(target=self.DrawResultRight)
                tright.start()
                threads.append(tright)
                
                for t in threads:
                    t.join()
                
                status = self.imageTop.imagedresult
                status1 = self.imageLeft.imagedresult
                status2 = self.imageRight.imagedresult
                logging.info("End Draw Info")
            except :
                status = 5

            status = max([status, status1, status2])
            if status==0:
                self.lblStatus.setText("success")
                self.lblStatus.setStyleSheet('''
                color: green
                ''')
            elif status==1:
                self.lblStatus.setText("warning")
                self.lblStatus.setStyleSheet('''
                color: yellow
                ''')
            else:
                self.lblStatus.setText("Error")
                self.lblStatus.setStyleSheet('''
                color: red
                ''')

        logging.info("task finished")

        return

    def _shutdown(self):
        #client = ServerProxy("http://localhost:8888", allow_none=True)
        try:
            self.clientleft.CloseServer()
            self.clientright.CloseServer()
        except :
            pass

    def ChangeTab(self):
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(0)
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(1)
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(2)
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(0)
        self.serialThread.start()
        self.imageTop.setImageScale() 
        self.imageLeft.setImageScale() 
        self.imageRight.setImageScale() 


    def OnPreview(self):
        if self.threadPreview==None or not self.threadPreview.is_alive():
            self.threadPreview= threading.Thread(target=self._GetImageShow)#self.PreviewCamera)
            self.threadPreview.start()
        
 
if __name__ == "__main__":
    #%(threadName)s       %(thread)d
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s[%(thread)d] - %(levelname)s - %(message)s')
    app = QApplication(sys.argv)
    window = UISettings()
    
    window.show()
    window.showFullScreen()

    threading.Thread(target=window.ChangeTab).start()

    logging.info(str(window.width())+"X"+str(window.height()))   
    sys.exit(app.exec_())
