from xmlrpc.client import ServerProxy
import xmlrpc.client

if __name__ == '__main__':
    client = ServerProxy("http://localhost:8888", allow_none=True)

    print(client.add(1, 2))
    print(client.updateProfile(""))
    print(client.profilepath('/home/pi/Desktop/pyUI/profiles', 'aaa'))
    print(client.ResultTest(5))
    #client.call('Init')
    client.TakePicture(0, False)
    client.TakePicture(1)
    client.TakePicture(2)
    client.CreateSamplePoint(0, 150,200)
    #client.call('Uninit')
    client.CloseServer()

    '''
    # 上传文件
    put_handle = open("girl.jpg", 'rb')
    server.image_put(xmlrpc.client.Binary(put_handle.read()))
    put_handle.close()
    # 下载文件
    get_handle = open("get_boy.jpg", 'wb')
    get_handle.write(server.image_get().data)
    get_handle.close()
    '''