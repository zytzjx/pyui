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
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit, QHBoxLayout, QMessageBox)
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
import resource

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
        self.logger.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync++")
        #process = subprocess.Popen(["rsync", "-avzP", '--delete', '/tmp/ramdisk', "pi@192.168.1.16:/tmp/ramdisk"],
        #    stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #process.stdin.write(b'qa\n')
        #process.communicate()[0]
        #process.wait()
        testrsync.rsync()
        self.logger.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync--")
        #process.stdin.close()
        self.imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % self.index)#pixmap

        #status = self.imagelabel.DrawImageResults(self.data)
        #self.signal.emit((self.index, status))


class StatusCheckThread(QThread):
#https://kushaldas.in/posts/pyqt5-thread-example.html
    signal = pyqtSignal(int)
    def __init__(self, myvar, parent=None):
        QThread.__init__(self, parent)        
        self.serialport = "/dev/ttyUSB0"
        self.exit_event = threading.Event()
        self.mylock = myvar
        self.threhold = 40000

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
                if not self.mylock.locked():
                    if oldstatus != status:
                        self.signal.emit(status)
                        oldstatus = status
                #time.sleep(0.05)
                self.msleep(50)
            statusser.stop()

class UISettings(QDialog):
    """Settings dialog widget
    """
    #filepath=""
    keyboardID=0
    resized = pyqtSignal()
    def __init__(self, parent=None):
        super(UISettings, self).__init__()
        self.logger = logging.getLogger('PSILOG')
        spathUI = os.path.join(os.path.dirname(os.path.realpath(__file__)),"psi_new.ui")
        loadUi(spathUI, self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.changeStyle('Fusion')
        self.takelock=threading.Lock()
        self.takepic=threading.Event()
        self.stop_prv = threading.Event()

        self.pbClose.clicked.connect(self.closeEvent)
        self.pbImageChange.clicked.connect(self.on_click)
        self.pbImageChangeDown.clicked.connect(self.on_click)
        self.pbStart.clicked.connect(self.on_startclick)
        self.serialThread = StatusCheckThread(self.takelock)
        self.config=settings.DEFAULTCONFIG
        self._loadConfigFile()
        self.updateProfile()
        #self.resized.connect(self.someFunction)
        self.pbSetting.clicked.connect(self.on_settingclick)
        self.pbKeyBoard.clicked.connect(self.on_KeyBoardclick)
        self.checkBox.stateChanged.connect(self.btnstate)
        self.tabWidget.currentChanged.connect(self.on_CameraChange)

        #self.leIMEI.setInputMask('9')
        self.leIMEI.editingFinished.connect(self.on_imei_editfinished)
        self.leModel.editingFinished.connect(self.on_model_editfinished)
        #self.leProfile.hide()
        self.previewEvent = threading.Event()
        self.imageTop.SetCamera(ImageLabel.CAMERA.TOP)
        self.imageLeft.SetCamera(ImageLabel.CAMERA.LEFT)
        self.imageRight.SetCamera(ImageLabel.CAMERA.RIGHT)
        self.startKey =False
        #self.clientleft = ServerProxy(myconstdef.URL_LEFT, allow_none=True)
        self.clienttop = ServerProxy(myconstdef.URL_TOP, allow_none=True)
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
        self._profilepath=""  #with profile name
        self.profilename=""

        self.imeidb=None
        self.loadImeidb()
        self.serialThread.start()


    def loadImeidb(self):
        if os.path.isfile('imei2model.json'):
            with open('imei2model.json') as json_file:
                self.imeidb = json.load(json_file)

    def ImeiQuery(self, imei):
        #"cmc_maker": "Apple",
        #"cmc_model": "iPhone3GS",
        #"maker": "Apple",
        #"model": "iPhone3GS",
        if 'doc' in self.imeidb:
            for item in self.imeidb['doc']:
                if imei.startswith(item['uuid']):
                    maker = item['maker'] if 'maker' in item else ''
                    model = item['model'] if 'model' in item else ''
                    cmc_maker = item['cmc_maker'] if 'cmc_maker' in item else ''
                    cmc_model = item['cmc_model'] if 'cmc_model' in item else ''
                    return (maker, model, cmc_maker, cmc_model)
        return ('','','','')

    def _getProfileName(self):
        self.profilename = ''
        if self.leModel.text()!="" and self.leStationID.text()!='':
            self.profilename = self.leModel.text() +'_'+self.leStationID.text()
            self.config["phonemodel"] = self.leModel.text()
            self._saveConfigFile()
            return True
        return False

    def on_imei_editfinished(self):
        if len(self.leIMEI.text())>=8:
            _,model,_,_ = self.ImeiQuery(self.leIMEI.text())
            self.leModel.setText(model)
            self._getProfileName()

    def on_model_editfinished(self):
        self._getProfileName()        

    def StatusChange(self, value):
        if self.checkBox.isChecked():
            return
        self.takelock.acquire()
        print("value is :"+str(value))
        if (value == 2):
            self.OnPreview()
        elif(value == 1):
            if self.isAutoDetect:
                self.previewEvent.set() 
                #start process
                self.on_startclick()
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
            self.logger.debug("capturing window 0x%x ", self.keyboardID)
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


    def _saveConfigFile(self):
        with open('config.json', 'w') as json_file:
            json.dump(self.config, json_file, indent=4)

    def _loadConfigFile(self):
        if os.path.isfile('config.json'):
            with open('config.json') as json_file:
                self.config = json.load(json_file)

        self.imageWidth = self.config['cw'] if 'cw' in self.config else 3280
        self.imageHeight = self.config['ch'] if 'ch' in self.config else 2464
        myconstdef.screwWidth = self.config['screww'] if 'screww' in self.config else 40
        myconstdef.screwHeight = self.config['screwh']  if 'screwh' in self.config else 40
        self.isPreview= self.config['preview'] if 'preview' in self.config else True
        self.isAutoDetect = self.config["autostart"] if 'autostart' in self.config else True
        spath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"profiles")
        self.sProfilePath = self.config["profilepath"] if 'profilepath' in self.config else spath
        self.leStationID.setText(self.config["stationid"] if 'stationid' in self.config else '1')
        self.leModel.setText(self.config["phonemodel"] if 'phonemodel' in self.config else '')
        self.serialThread.setThrehold(self.config["threhold"] if 'threhold' in self.config else 20000)


    def createprofiledirstruct(self, profiename):
        #self.clientleft = ServerProxy(myconstdef.URL_LEFT, allow_none=True)
        self.clienttop = ServerProxy(myconstdef.URL_TOP, allow_none=True)
        self.clientright = ServerProxy(myconstdef.URL_RIGHT, allow_none=True)
        #self.imageLeft.setServerProxy(self.clientleft)
        self.imageTop.setServerProxy(self.clienttop)
        self.imageRight.setServerProxy(self.clientright)

    def closeEvent(self, event):
        self.stop_prv.set()
        if self.threadPreview != None:
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
        #self._profilepath=self.config["profilepath"]
        #self.comboBox.addItems([name for name in os.listdir(self._profilepath) if os.path.isdir(os.path.join(self._profilepath, name))])
        #self.comboBox.setCurrentIndex(self.config["comboxindex"] if 'comboxindex' in self.config and self.config["comboxindex"]<self.comboBox.count() else 0)

    @staticmethod
    def createSShServer():
        from paramiko import SSHClient
        import paramiko
        ssh = SSHClient()
        #ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=myconstdef.IP, username='pi', password=myconstdef.PASSWORD, look_for_keys=False)

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
        self.logger.info("preview: thread is starting...")
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
        self.logger.info("preview: thread ending...")

    def _GetImageShow(self):
        self.logger.info("preview: thread starting...")
        #self.imageTop.clear()
        #self.imageLeft.clear()
        #self.imageRight.clear()
        self.lblStatus.setText("ready")
        self.lblStatus.setStyleSheet('''
        color: black
        ''')
        
        self.imageTop.setImageScale() 
        self.stop_prv.clear()
        #logging.info(self.clientleft.startpause(False))
        self.logger.info(self.clienttop.startpause(False))
        while True:
            #data = self.clientleft.preview().data
            data = self.clienttop.preview().data
            image = Image.open(io.BytesIO(data))
            imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
            pixmap = QPixmap.fromImage(imageq)
            self.imageTop.ShowPreImage(pixmap)
            if self.stop_prv.is_set():
                self.stop_prv.clear()
                #self.clientleft.startpause(True)
                for i in range(0,2):
                    while True:
                        try:
                            self.clienttop.startpause(True)
                        except :
                            continue
                        break
                break

        self.stop_prv.clear()
        self.logger.info("preview: thread ending...")


    @pyqtSlot()
    def btnstate(self):
        if self.sender().isChecked():
            self.imageTop.isProfile = True
            self.imageLeft.isProfile = True
            self.imageRight.isProfile = True
            #self.leProfile.show()
            #self.comboBox.hide()
        else:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            try:
                self.imageTop.isProfile = False
                self.imageLeft.isProfile = False
                self.imageRight.isProfile = False
                #self.leProfile.hide()
                #self.comboBox.clear() 
                #self.comboBox.addItems([name for name in os.listdir(self.config["profilepath"]) if os.path.isdir(os.path.join(self.config["profilepath"], name))])
                #self.comboBox.setCurrentIndex(self.config["comboxindex"] if 'comboxindex' in self.config and self.config["comboxindex"]<self.comboBox.count() else 0)
                #self.comboBox.show()
                tl = Process(target=self.runsyncprofiles, args=(True,))
                tl.start()
                tr = Process(target=self.runsyncprofiles, args=(False,))
                tr.start()
                tl.join()
                tr.join()

            except Exception as e:
                self.logger.exception(str(e))
            finally:
                QApplication.restoreOverrideCursor() 


    @pyqtSlot()
    def on_CameraChange(self):
        return


    @pyqtSlot()
    def on_KeyBoardclick(self):
        self.ShowKeyBoard()

    @pyqtSlot()
    def on_settingclick(self):
        #dlg = Settings(self, self.clientleft, self.clientright)
        self.stop_prv.set() 

        dlg = Settings(self.clienttop, self.clientright, self)
        if dlg.exec_():
            self._loadConfigFile()
            self.logger.info("Success!")
        else:
            self.logger.info("Cancel!")  


    def __jason(self):
        self.isAutoDetect = False
        while True:
            self.on_startclick()
            time.sleep(2)

    @pyqtSlot()
    def on_click(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Stop':
            self.stop_prv.set() 
            threading.Thread(target=self.__jason).start()
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
        ip = myconstdef.IP_TOP
        if not isLeft:
            ip = myconstdef.IP_RIGHT
        
        cmd = 'rsync -avz -e ssh pi@{0}:{1}/ {1}/'.format(ip, self.config["profilepath"])
        os.system(cmd)

    def capture(self, cam, IsDetect=True):
        cmd = "raspistill -vf -hf -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        if cam ==0:
            cmd = "raspistill -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        self.logger.info(cmd)
        os.system(cmd)
        if not IsDetect:
            shutil.copyfile("/tmp/ramdisk/phoneimage_%d.jpg" % cam, os.path.join(self._profilepath, self._DirSub(cam), self.profilename+".jpg"))
        else:
            self._callyanfunction(cam)

    def _callyanfunction(self, index):
        #self.profilename= self.leProfile.text() if self.checkBox.isChecked() else self.comboBox.currentText()
        self.logger.info('callyanfunction:' + self.profilename)
        txtfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".txt")
        smplfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".jpg")
        self.logger.info(txtfilename)
        self.logger.info(smplfilename)
        if os.path.exists(txtfilename) and os.path.exists(smplfilename):
            self.logger.info("*testScrews**")
            try:
                self.imageresults = testScrew.testScrews(
                    txtfilename, 
                    smplfilename, 
                    "/tmp/ramdisk/phoneimage_%d.jpg" % index)
            except :
                self.imageresults = []
                pass
            
            self.logger.info("-testScrews end--")
            self.logger.info(self.imageresults)

    def _startdetectthread(self, index):
        self.yanthread = Process(target=self._callyanfunction, args=(index,))
        self.yanthread.start()
        self.yanthread.join()

    def _showImage(self, index, imagelabel):
        imagelabel.setImageScale()     
        self.logger.info("Start testing %d" % index)
        for iretry in range(0,1):
            while True:
                try:
                    if index==ImageLabel.CAMERA.TOP.value:
                        self.clienttop.TakePicture(index, not self.checkBox.isChecked()) 
                    elif index==ImageLabel.CAMERA.RIGHT.value:
                        self.clientright.TakePicture(index, not self.checkBox.isChecked())  
                    elif index == ImageLabel.CAMERA.LEFT.value:
                        self.capture(index, not self.checkBox.isChecked())
                except :
                    time.sleep(0.1)  
                    continue
                break

        self.logger.info("Start transfer %d" % index)
        imagelabel.SetProfile(self.profilename, self.profilename+".jpg")
        if self.checkBox.isChecked():
            if index==ImageLabel.CAMERA.LEFT.value:
                #imagelabel.SetProfile(self.profilename, self.profilename+".jpg")
                imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % index)#pixmap
            else:
                #data = self.clientleft.imageDownload(index).data if index == 1 else self.clientright.imageDownload(index).data
                data = self.clienttop.imageDownload(index).data if index == ImageLabel.CAMERA.TOP.value else self.clientright.imageDownload(index).data
                self.logger.info("end testing %d" % index)
                image = Image.open(io.BytesIO(data))
                image.save("/tmp/ramdisk/temp_%d.jpg" % index)
                #imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
                #pixmap = QPixmap.fromImage(imageq)
                imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/temp_%d.jpg" % index)#pixmap
        else:
            #imagelabel.SetProfile(self.profilename, self.profilename+".jpg")
            if index==ImageLabel.CAMERA.LEFT.value:
                imagelabel.ShowPreImage(QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % index))
            else:
                pass

    def _drawtestScrew(self, index, imagelabel):
        ret=0
        if index==ImageLabel.CAMERA.LEFT.value:
            ret = imagelabel.DrawImageResults(self.imageresults)
        else:
            #ss = self.clientleft.ResultTest(index) if index==1 else self.clientright.ResultTest(index)
            ss = self.clienttop.ResultTest(index) if index==1 else self.clientright.ResultTest(index)
            ret = imagelabel.DrawImageResults(json.loads(ss))
        return ret

    def _ThreadTakepictureLeft(self):
        try:
            self._showImage(ImageLabel.CAMERA.LEFT.value, self.imageLeft)
        except Exception as ex:
            self.logger.exception(str(ex))
            status = 5

        self.logger.info("ending camera Left and transfer")

    def _ThreadTakepictureRight(self):
        try:
            self._showImage(ImageLabel.CAMERA.RIGHT.value, self.imageRight)
        except Exception as ex:
            self.logger.exception(str(ex))
            status = 5

        self.logger.info("ending camera right and transfer")


    def _ThreadTakepicture(self):
        #self.takelock.acquire()
        #status, status1, status2 = 0, 0, 0
        self.takepic.clear()
        try:
            self._showImage(ImageLabel.CAMERA.TOP.value, self.imageTop)
        except Exception as ex:
            self.logger.exception(str(ex))
            status = 5
        #finally:
        #    self.takelock.release()

        self.logger.info("ending camera A and transfer")
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
        #self.imageTop.DrawImageResults(self.imageresults, None )
        self.imageTop.clear()
        self.imageTop.imagedresult = 0
        data = json.loads(self.clienttop.ResultTest(ImageLabel.CAMERA.TOP.value))
        if len(data)>0:
            #status1 = self.testScrewResult(data)
            status1 = self.imageTop.DrawImageResults(data, QPixmap(self.profileimages[ImageLabel.CAMERA.TOP.value]))

    def DrawResultLeft(self):
        self.imageLeft.clear()
        self.imageLeft.imagedresult = 0
        self.imageLeft.DrawImageResults(self.imageresults, None )
        #data = json.loads(self.clientleft.ResultTest(1))
        #if len(data)>0:
        #    #status1 = self.testScrewResult(data)
        #    status1 = self.imageLeft.DrawImageResults(data, QPixmap(self.profileimages[1]))

    def DrawResultRight(self):
        self.imageRight.clear()
        self.imageRight.imagedresult = 0
        data = json.loads(self.clientright.ResultTest(ImageLabel.CAMERA.RIGHT.value))
        if len(data)>0:
            #status2 = self.testScrewResult(data)
            status2 = self.imageRight.DrawImageResults(data, QPixmap(self.profileimages[ImageLabel.CAMERA.RIGHT.value]))

    def _loadProfile(self):
        #self.profileimages[ImageLabel.CAMERA.TOP.value]=os.path.join(pathtop,  self.profilename+".jpg")
        #self.profileimages[ImageLabel.CAMERA.LEFT.value]=os.path.join(pathleft,  self.profilename+".jpg")
        #self.profileimages[ImageLabel.CAMERA.RIGHT.value]=os.path.join(pathright,  self.profilename+".jpg")
        #pre, ext = os.path.splitext(renamee)
        #os.rename(renamee, pre + new_extension)
        for i in ImageLabel.CAMERA:
            imageName = self.profileimages[i.value]
            if not os.path.exists(imageName):
                continue
            pre, ext = os.path.splitext(imageName)
            screwTxt = pre+'.txt'
            if not os.path.exists(screwTxt):
                continue
            centerpoint=[]
            with open(screwTxt) as f:
                for line in f:
                    words = line.split()                    
                    roi_0 = int(words[1][:-1])
                    roi_1 = int(words[2][:-1])
                    roi_2 = int(words[3][:-1])
                    roi_3 = int(words[4])
                    x = roi_0 + int((roi_1 - roi_0 + 1)/2)
                    y = roi_2 + int((roi_3 - roi_2 + 1)/2)
                    centerpoint.append((x,y))
            
            if i == ImageLabel.CAMERA.TOP :
                self.imageTop.DrawImageProfile(centerpoint, QPixmap(imageName))
            elif i == ImageLabel.CAMERA.LEFT :
                self.imageLeft.DrawImageProfile(centerpoint, QPixmap(imageName))
            elif i == ImageLabel.CAMERA.RIGHT :
                self.imageRight.DrawImageProfile(centerpoint, QPixmap(imageName))



    @pyqtSlot()
    def on_startclick(self):
        self._getProfileName()
        if self.profilename=="":
            #error_dialog = QtWidgets.QErrorMessage(self)
            #error_dialog.showMessage('Oh no! Profile name is empty.') 
            QMessageBox.question(self, 'Error', "Oh no! Profile name is empty.", QMessageBox.Cancel, QMessageBox.Cancel)
            return             
        
        self.imageTop.clear()
        self.imageLeft.clear()
        self.imageRight.clear()

        pathleft = os.path.join(self.config["profilepath"], self.profilename, "left")
        pathtop = os.path.join(self.config["profilepath"], self.profilename, "top")
        pathright = os.path.join(self.config["profilepath"], self.profilename, "right")
            
        self.profileimages[ImageLabel.CAMERA.TOP.value]=os.path.join(pathtop,  self.profilename+".jpg")
        self.profileimages[ImageLabel.CAMERA.LEFT.value]=os.path.join(pathleft,  self.profilename+".jpg")
        self.profileimages[ImageLabel.CAMERA.RIGHT.value]=os.path.join(pathright,  self.profilename+".jpg")

        self.stop_prv.set() 
        if self.stop_prv.is_set():
            time.sleep(0.1)  

        self._profilepath = os.path.join(self.config["profilepath"], self.profilename)
        if not self.checkBox.isChecked() and not os.path.exists(self._profilepath):
            QMessageBox.question(self, 'Error', "Oh no! Create profile please.", QMessageBox.Cancel, QMessageBox.Cancel)
            return  

        if self.checkBox.isChecked() and os.path.exists(self._profilepath):
            buttonReply = QMessageBox.question(self, 'Info', "Profile Exists. Do you want to the profile?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if buttonReply == QMessageBox.Cancel:
                return  
            if buttonReply == QMessageBox.Yes:
                self._loadProfile()
                return
            if buttonReply == QMessageBox.No:
                pass


        if self.checkBox.isChecked():
            mode = 0o777
            os.makedirs(pathleft, mode, True) 
            os.makedirs(pathtop, mode, True) 
            os.makedirs(pathright, mode, True) 

        
        if self.startKey:
            self.ShowKeyBoard()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            #self.profilename= self.leProfile.text() if self.checkBox.isChecked() else self.comboBox.currentText()
            #self.clientleft.profilepath(self.config["profilepath"], self.profilename)
            try:
                self.clientright.profilepath(self.config["profilepath"], self.profilename)        
            except:
                pass
            
            try:
                self.clienttop.profilepath(self.config["profilepath"], self.profilename)
            except:
                pass

            self.logger.info("Start testing click")
            if  self.checkBox.isChecked():
                self.clienttop.setScrewSize(myconstdef.screwWidth, myconstdef.screwHeight)
                self.clientright.setScrewSize(myconstdef.screwWidth, myconstdef.screwHeight)
            self.logger.info("Start testing top")
            p = threading.Thread(target=self._ThreadTakepicture)
            p.start()
            pLeft = threading.Thread(target=self._ThreadTakepictureLeft)
            pLeft.start()
            pRight = threading.Thread(target=self._ThreadTakepictureRight)
            pRight.start()
            p.join()
            self.logger.info("Start end top")        
            pLeft.join()
            self.logger.info("Start end left")        
            pRight.join()
            self.logger.info("Start end right")        
            if not self.checkBox.isChecked():
                status, status1, status2 = 0, 0, 0
                #self.takepic.wait()
                #self.takepic.clear()
                try:
                    self.logger.info("Start Draw Info")
                    
                    threads=[]
                    ttop = threading.Thread(target=self.DrawResultTop)
                    ttop.start()
                    threads.append(ttop)
                    self.logger.info("Draw top finish")
                    
                    tleft = threading.Thread(target=self.DrawResultLeft)
                    tleft.start()
                    threads.append(tleft)
                    self.logger.info("Draw left finish")

                    tright = threading.Thread(target=self.DrawResultRight)
                    tright.start()
                    threads.append(tright)
                    
                    for t in threads:
                        t.join()
                    
                    status = self.imageTop.imagedresult
                    status1 = self.imageLeft.imagedresult
                    status2 = self.imageRight.imagedresult
                    self.logger.info("End Draw Info:%d:%d:%d"%(status, status1, status2))
                except :
                    status = 5

                status = max([status, status1, status2])
                if status==0:
                    self.lblStatus.setText("")
                    self.lblStatus.setStyleSheet('''
                    border-image: url(:/icons/yes.png); 
                    ''')
                elif status==1:
                    self.lblStatus.setText("")
                    self.lblStatus.setStyleSheet('''
                    border-image: url(:/icons/warning.png);
                    ''')
                else:
                    self.lblStatus.setText("")
                    self.lblStatus.setStyleSheet('''
                    border-image: url(:/icons/no.png); 
                    ''')

            self.logger.info("task finished")

        except Exception as e:
            self.logger.exception(str(e))
        finally:
            QApplication.restoreOverrideCursor() 



    def _shutdown(self):
        #client = ServerProxy("http://localhost:8888", allow_none=True)
        try:
            #self.clientleft.CloseServer()
            self.clienttop.CloseServer()
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
        self.logger.info(str(self.lblStatus.width())+"X"+str(self.lblStatus.height()))
        self.lblStatus.setFixedSize(self.lblStatus.width(),self.lblStatus.width())
        self.logger.info("Status Size:"+str(self.lblStatus.width())+"X"+str(self.lblStatus.height()))
        window.tabWidget.setCurrentIndex(0)
        self.imageTop.setImageScale() 
        self.imageLeft.setImageScale() 
        self.imageRight.setImageScale() 


    def OnPreview(self):
        allowpreview = self.config["preview"] if 'preview' in self.config else True
        if not allowpreview:
            return
        if self.threadPreview==None or not self.threadPreview.is_alive():
            self.threadPreview= threading.Thread(target=self._GetImageShow)#self.PreviewCamera)
            self.threadPreview.start()
        
def CreateLog():
    import logging
    from logging.handlers import RotatingFileHandler

    formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(funcName)s(%(lineno)d) %(message)s')

    logFile = '/tmp/ramdisk/psi.log'
    handler = RotatingFileHandler(logFile, mode='a', maxBytes=1*1024*1024, 
                                    backupCount=500, encoding=None, delay=False)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger = logging.getLogger('PSILOG')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

if __name__ == "__main__":
    #%(threadName)s       %(thread)d
    #logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s[%(thread)d] - %(levelname)s - %(message)s')
    logger = CreateLog()
    app = QApplication(sys.argv)
    window = UISettings()
    
    window.show()
    window.showFullScreen()

    threading.Thread(target=window.ChangeTab).start()
    logger.info(os.path.dirname(os.path.realpath(__file__)))
    logger.info(str(window.width())+"X"+str(window.height()))   
    sys.exit(app.exec_())
