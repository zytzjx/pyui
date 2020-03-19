#!/usr/bin/env python</em>
# coding: utf-8
 
import pyjsonrpc 

http_client = pyjsonrpc.HttpClient(
    url = "http://localhost:8080/jsonrpc"
    #username = "Username",
    #password = "Password"
)

print http_client.updateProfile()
http_client.Init()
# Result: 3
http_client.call("add",1,2)
print http_client.call("TakePicture",0)
http_client.TakePicture(1)
http_client.TakePicture(2)


http_client.Uninit() 
# It is also possible to use the *method* name as *attribute* name.
http_client.add(1, 2)
# Result: 3
 
# Notifications send messages to the server, without response.
http_client.notify("add", 3, 4)