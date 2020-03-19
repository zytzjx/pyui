#!/usr/bin/env python
# coding: utf-8
 
import pyjsonrpc
from datetime import datetime
import RPi.GPIO as gp
import os
import sys
import time 
 
class RequestHandler(pyjsonrpc.HttpRequestHandler):
 
    @pyjsonrpc.rpcmethod
    def add(self, a, b):
        """Test method"""
        return a + b
    
    @pyjsonrpc.rpcmethod
    def updateProfile(self):
        curpath=os.path.abspath(os.path.dirname(sys.argv[0]))
        profilepath=os.path.join(curpath,"profiles")
        return [name for name in os.listdir(profilepath) if os.path.isdir(os.path.join(profilepath, name))]


    @pyjsonrpc.rpcmethod
    def Init(self):
        gp.setwarnings(False)
        gp.setmode(gp.BOARD)

        gp.setup(7, gp.OUT)
        gp.setup(11, gp.OUT)
        gp.setup(12, gp.OUT)

        gp.setup(15, gp.OUT)
        gp.setup(16, gp.OUT)
        gp.setup(21, gp.OUT)
        gp.setup(22, gp.OUT)

        gp.output(11, True)
        gp.output(12, True)
        gp.output(15, True)
        gp.output(16, True)
        gp.output(21, True)
        gp.output(22, True)
    
    @pyjsonrpc.rpcmethod
    def Uninit(self):
        gp.output(7, False)
        gp.output(11, False)
        gp.output(12, True)

    def capture(self, cam):
        cmd = "raspistill -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        os.system(cmd)
        return QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % cam)

    @pyjsonrpc.rpcmethod
    def TakePicture(self, index):
        if index==0:
            print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera A")
            i2c = "i2cset -y 1 0x70 0x00 0x04"
            os.system(i2c)
            gp.output(7, False)
            gp.output(11, False)
            gp.output(12, True)
        elif index == 1:
            print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera B")
            i2c = "i2cset -y 1 0x70 0x00 0x05"
            os.system(i2c)
            gp.output(7, True)
            gp.output(11, False)
            gp.output(12, True)
        else:
            print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera C")
            i2c = "i2cset -y 1 0x70 0x00 0x06"
            os.system(i2c)
            gp.output(7, False)
            gp.output(11, True)
            gp.output(12, False)
        return self.capture(index)

 
 
# Threading HTTP-Server
http_server = pyjsonrpc.ThreadingHttpServer(
    server_address = ('0.0.0.0', 8080),
    RequestHandlerClass = RequestHandler
)
print("Starting HTTP server ...")
print("URL: http://localhost:8080")
try:
    http_server.serve_forever()
except KeyboardInterrupt:
    http_server.shutdown()