import TcpClient
from TcpClient import ClientCommand, TaskCommand
import pickle

def handle_TAKEPICTURE(datacmd):
    filepath = '/home/pi/Desktop/pyUI/curimage.jpg'
    with picamera.PiCamera() as camera:
        camera.start_preview()
        camera.capture(self.filepath)
        camera.stop_preview()   

def handle_PROFILENAME(datacmd):
    profilename = datacmd.data

def handle_IMAGE(datacmd):
    filepath = '/home/pi/Desktop/pyUI/curimage.jpg'
    with open(filepath, "rb") as image:
        f = image.read()
        b = bytearray(f)
        client.cmd_q.put(ClientCommand(ClientCommand.SEND, TaskCommand(TaskCommand.IMAGE, b)))
        reply = client.reply_q.get(True)

def handle_POINTS(datacmd):
    pins = datacmd.data

def handle_RESULT(datacmd):
    client.cmd_q.put(ClientCommand(ClientCommand.SEND, TaskCommand(TaskCommand.IMAGE, b)))
    reply = client.reply_q.get(True)

client = TcpClient.SocketClientThread()
client.start()
client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, ('10.1.1.183', 5007)))
reply = client.reply_q.get(True)
handlers = {
    TaskCommand.TAKEPICTURE: handle_TAKEPICTURE,
    TaskCommand.PROFILENAME: handle_PROFILENAME,
    TaskCommand.IMAGE: handle_IMAGE,
    TaskCommand.POINTS: handle_POINTS,
    TaskCommand.RESULT: handle_RESULT,
}

while True:
    client.cmd_q.put(ClientCommand(ClientCommand.RECEIVE, ""))
    reply = client.reply_q.get(True)
    print('sct1: ', reply.type, reply.data)
    datacmd = pickle.loads(bytes(reply.data))
    print(datacmd)
    handlers[datacmd.type](datacmd)
    #client.alive.set()


client.cmd_q.put(ClientCommand(ClientCommand.CLOSE))
reply = client.reply_q.get(True)
print('sct2 close: ', reply.type, reply.data)
