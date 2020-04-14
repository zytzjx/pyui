from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,  QDir
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit, QFileDialog, QDialogButtonBox)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi
import logging
import json
import os.path
from xmlrpc.client import ServerProxy
import xmlrpc.client
import myconstdef



DEFAULTCONFIG={"cw":3280,"ch":2464,"profilepath":"/home/pi/Desktop/pyUI/profiles"}

class Settings(QDialog):
    """Settings dialog widget
    """
 
    def __init__(self, leftproxy, rightproxy, parent=None):
        super(Settings, self).__init__()
        loadUi('Setting.ui', self)
        #self.changeStyle('Fusion')
        self.setWindowFlags(Qt.WindowMinimizeButtonHint  | Qt.WindowTitleHint | Qt.FramelessWindowHint)
        self.setWindowTitle("PSI Setting")
        screenGeometry = QApplication.desktop().screenGeometry()
        x = (screenGeometry.width() - self.width()) / 2
        y = (screenGeometry.height() - self.height()) / 2
        self.move(x, y)
        self.data=DEFAULTCONFIG
        if os.path.isfile('config.json'):
            with open('config.json') as json_file:
                self.data = json.load(json_file)
        else:
            with open('config.json', 'w') as outfile:
                json.dump(DEFAULTCONFIG, outfile)

        self.leProfilePath.setText(self.data['profilepath'])
        self.leWidth.setText(str(self.data['cw']))
        self.leHeight.setText(str(self.data['ch']))

        self.leftProxy = leftproxy
        self.rightProxy = rightproxy
        self.pbDir.clicked.connect(self.On_DirClick)
        self.pbImport.clicked.connect(self.On_Import)
        self.pbExport.clicked.connect(self.On_Export)
        self.pbDelete.clicked.connect(self.On_Delete)
        self.pbRename.clicked.connect(self.On_Rename)
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save)

        for name in os.listdir(self.data['profilepath']):
            if os.path.isdir(os.path.join(self.data['profilepath'], name)):
                self.listWidget.addItem(name)

    def runsyncprofiles(self):
        cmd = 'rsync -avz -e ssh {1}/ pi@{0}:{1}/'.format(myconstdef.IP_LEFT, self.data["profilepath"])
        os.system(cmd)
        cmd = 'rsync -avz -e ssh {1}/ pi@{0}:{1}/'.format(myconstdef.IP_RIGHT, self.data["profilepath"])
        os.system(cmd)

    @pyqtSlot()
    def On_Import(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        logging.info(file)
        if os.path.isdir(file):
            shutil.copytree(file, self.data["profilepath"])   
            self.runsyncprofiles()

    @pyqtSlot()
    def On_Export(self):
        pass
    
    @pyqtSlot()
    def On_Delete(self):
        if self.listWidget.currentRow()>=0:         
            self.leftProxy.RemoveProfile(repr(self.listWidget.selectedItems()))
            self.rightProxy.RemoveProfile(repr(self.listWidget.selectedItems()))
    
    @pyqtSlot()
    def On_Rename(self, newname):
        if self.listWidget.currentRow()>=0:         
            self.leftProxy.RenameProfile(repr(self.listWidget.selectedItems()), newname)
            self.rightProxy.RenameProfile(repr(self.listWidget.selectedItems()), newname)

    @pyqtSlot()
    def On_DirClick(self):
        download_path=self.data["profilepath"]
        fname = QFileDialog.getExistingDirectory(self, 'Select a directory', download_path)
        if fname:
            fname = QDir.toNativeSeparators(fname)

        if os.path.isdir(fname):
            self.lineEdit_3.setText(fname)
            self.data["profilepath"] = fname


    def _savedata(self):
        self.data['cw'] = int(self.leWidth.text())
        self.data['ch'] = int(self.leHeight.text())
        self.data['threhold'] = self.sbPromixity.value
        self.data['preview'] = self.cbPreview.isChecked()
        with open('config.json', 'w') as outfile:
            json.dump(self.data, outfile)

    def apply(self):
        self._savedata()


    def save(self):
        self._savedata()
        self.accept()