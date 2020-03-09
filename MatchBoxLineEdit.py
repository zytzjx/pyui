from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit)
import subprocess
#import time

class MatchBoxLineEdit(QLineEdit):
    def focusInEvent(self, e):
        try:
            subprocess.Popen(["matchbox-keyboard"])
            #time.sleep(1)
            win = subprocess.check_output(['xdotool', 'getactivewindow']).strip()
            subprocess.check_call(['xdotool','windowsize',win, '640','480'])
            subprocess.check_call(['xdotool','windowmove',win, str(self.x()), str(self.y()+40)])
        except FileNotFoundError:
            pass

    def focusOutEvent(self,e):
        subprocess.Popen(["killall","matchbox-keyboa"])
