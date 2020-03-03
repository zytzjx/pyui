import socket 
from threading 
import Thread 
#from socketserver import ThreadingMixIn
import struct
import error as SocketError
import errno
import logging
import queue
from TcpClient import TaskCommand,ClientCommand,ClientReply
import pickle

# Multithreaded Python server : TCP Server Socket Thread Pool

class ClientThread(Thread): 
    def __init__(self,ip,port,conn):
        Thread.__init__(self)
        self.ip = ip 
        self.port = port 
        self.conn = conn
        self.peername=socket.getfqdn(ip)
        print ("[+] New server socket thread started for " + ip +":" + str(port) )
        self.reply_q = reply_q or Queue()

    def SendDataToClient(data):
        realdata=pickle.dumps(data)
        header = struct.pack('<L', len(realdata))
        try:
            self.socket.sendall(header + realdata)
        except IOError as e:
            logging.debug(str(e))

    def _recv_n_bytes(self, n):
        """ Convenience method for receiving exactly n bytes from
            self.socket (assuming it's open and connected).
        """
        data = ''
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if chunk == '':
                break
            data += chunk
        return data

    def _error_reply(self, errstr):
        return ClientReply(ClientReply.ERROR, errstr)

    def _success_reply(self, data=None):
        return ClientReply(ClientReply.SUCCESS, data)

    def run(self): 
        running = True
        while running : 
            try:
                header_data = self._recv_n_bytes(4)
                if len(header_data) == 4:
                    msg_len = struct.unpack('<L', header_data)[0]
                    data = self._recv_n_bytes(msg_len)
                    if len(data) == msg_len:
                        self.reply_q.put(self._success_reply(data))
                        return
                running = False
                self.reply_q.put(self._error_reply('Socket closed prematurely'))
            except SocketError as e:
                if e.errno == errno.ECONNRESET:
                    print("Socket client close.\n")

                conn.close()
                self.reply_q.put(self._error_reply(str(e)))
                running=False

# Multithreaded Python server : TCP Server Socket Program Stub
TCP_IP = '0.0.0.0' 
TCP_PORT = 9980 
BUFFER_SIZE = 1024 # Usually 1024, but we need quick response 
threads = [] 

def _StartTcpServer(nport=TCP_PORT):
    TCP_PORT = nport
    tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    tcpServer.bind((TCP_IP, TCP_PORT)) 
 
    while True: 
        tcpServer.listen(4) 
        print ("Multithreaded Python server : Waiting for connections from TCP clients..." )
        
        (conn, (ip,port)) = tcpServer.accept() 
        newthread = ClientThread(ip,port, conn) 
        newthread.start() 
        threads.append(newthread) 

        threads = [item for item in threads if item.is_alive()]
        print(threads)

    #for t in threads: 
    #    t.join()


def startThreadServer():
    threading.Thread(target=_StartTcpServer).start()

def TakePicture():
    for t in threads:
        t.SendDataToClient((TaskCommand.TAKEPICTURE, "take picture"))

def SendProfile(profile):
    for t in threads:
        t.SendDataToClient((TaskCommand.PROFILENAME, profile))

def GetImage():
    for t in threads:
        t.SendDataToClient((TaskCommand.IMAGE, "imagefile"))

def GetResult():
    for t in threads:
        t.SendDataToClient((TaskCommand.RESULT,"result"))

