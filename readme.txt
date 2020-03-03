Install PyQT5

sudo apt-get update
sudo apt-get install qt5-default pyqt5-dev pyqt5-dev-tools

autorun:https://blog.csdn.net/geyo1992/article/details/80049821
sudo nano /etc/rc.local

export DISPLAY=:0
#X -nocursor -s 0 -dpms &
/home/pi/Desktop/pyUI/start.sh &

