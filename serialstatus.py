import logging
import serial
import serial.threaded
import threading
import time
import re

try:
    import queue
except ImportError:
    import Queue as queue


class FDProtocol(serial.threaded.LineReader):

    TERMINATOR = b'\r\n'

    def __init__(self):
        super(FDProtocol, self).__init__()
        self.alive = True
        #self.responses = queue.Queue()
        self.events = queue.Queue()
        self._event_thread = threading.Thread(target=self._run_event)
        self._event_thread.daemon = True
        self._event_thread.name = 'status-event'
        self._event_thread.start()
        self.lock = threading.Lock()
        self.ultraSonic = threading.Event()
        self.ultraSonicStatus = False
        self.proximity = threading.Event()
        self.proximityStatus = False

    def stop(self):
        """
        Stop the event processing thread, abort pending commands, if any.
        """
        self.alive = False
        self.events.put(None)
        #self.responses.put('<exit>')
    
    def _run_event(self):
        """
        Process events in a separate thread so that input thread is not
        blocked.
        """
        while self.alive:
            try:
                #self.handle_event(self.events.get())
                time.sleep(1)
            except:
                logging.exception('_run_event')
    
    def handle_line(self, line):
        """
        Handle input from serial port, check for events.
        """
        m = re.search(r'^(.*?):[ ]?(\d+)$', line)
        if m:
            #self.events.put(line)
            #if m.group(1)=="Ambient":
            #    if int(m.group(2))<5:
            #        self.ultraSonic.set()
            #        self.ultraSonicStatus = False
            #        print("Am less 5\n")
            if m.group(1) =="Proximity":
                if int(m.group(2))<150:
                    self.proximity.set()
                    self.proximityStatus = False
                    print("Proximity is %s\n" % m.group(2))
                else:
                    self.proximity.clear()
                    self.proximityStatus = True
            elif m.group(1) == "Distance":
                if int(m.group(2)) > 500:
                    self.ultraSonic.set()
                    self.ultraSonicStatus = False
                    print("Distance is %s\n" % m.group(2))
                else:
                    self.ultraSonic.clear()
                    self.ultraSonicStatus = True

    def handle_event(self, event):
        """
        Spontaneous message received.
        """
        print('event received:', event)

    def command(self, command):
        """
        Set an AT command and wait for the response.
        """
        with self.lock:  # ensure that just one thread is sending commands at once
            self.write_line(command)

if __name__ == '__main__':
    ser = serial.serial_for_url('alt:///dev/ttyUSB0', baudrate=9600, timeout=1)
    #ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1)
    with serial.threaded.ReaderThread(ser, FDProtocol) as statusser:
        
        while True:
            time.sleep(1)