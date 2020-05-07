from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit, QFileDialog, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi

class ResultDialog(QDialog):
    def __init__(self, data,  parent=None):
        super(ResultDialog, self).__init__()
        loadUi('dlgResult.ui', self)
        #self.changeStyle('Fusion')
        self.setWindowFlags(Qt.WindowMinimizeButtonHint  | Qt.WindowTitleHint | Qt.FramelessWindowHint)
        self.setWindowTitle("PSI Result")
        self.pbExit.clicked.connect(self.close)
        self.data = data

    def Value2Str(self, status):
        if status==0:
            return "Success"
        elif status==1:
            return "Warning"
        else:
            return "Error"

    def ShowData(self):
        index = 0
        for dd in self.data:
            self.tableWidget.setItem(index,0, QTableWidgetItem(str(index+1))
            self.tableWidget.setItem(index,1, QTableWidgetItem(self.Value2Str(dd[0]))
            self.tableWidget.setItem(index,2, QTableWidgetItem(self.Value2Str(dd[1]))
            self.tableWidget.setItem(index,3, QTableWidgetItem(self.Value2Str(dd[2]))
