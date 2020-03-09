from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,  QDir
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit, QFileDialog, QDialogButtonBox)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi
import logging
import json
import os.path


DEFAULTCONFIG={"cw":3280,"ch":2464,"profilepath":"/home/pi/Desktop/pyUI/profiles"}

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
        self.data=DEFAULTCONFIG
        if os.path.isfile('config.json'):
            with open('config.json') as json_file:
                self.data = json.load(json_file)
        else:
            with open('config.json', 'w') as outfile:
                json.dump(DEFAULTCONFIG, outfile)

        self.pbDir.clicked.connect(self.On_DirClick)
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        self.buttonBox.button(QDialogButtonBox.Save).clicked.connect(self.save)


    @pyqtSlot()
    def On_DirClick(self):
        download_path=self.data["profilepath"]
        fname = QFileDialog.getExistingDirectory(self, 'Select a directory', download_path)
        if fname:
            fname = QDir.toNativeSeparators(fname)

        if os.path.isdir(fname):
            self.lineEdit_3.setText(fname)
            self.data["profilepath"] = fname


    def apply(self):
        with open('config.json', 'w') as outfile:
            json.dump(self.data, outfile)

    def save(self):
        with open('config.json', 'w') as outfile:
            json.dump(self.data, outfile)
        self.accept()