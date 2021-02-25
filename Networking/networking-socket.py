# This project is the implementation of client/server application using the sockets.
# This contains both TCP and UDP protocols. 
# Multithreaded server is implemented as well. 



#TCP Server
import socket
import threading
from _thread import *




def protocol(connection, socket):
    while True:
        recMessage = connection.recv(256)
        print("Message received: ", recMessage.decode())
        if(recMessage.decode() == "hello"):
            connection.sendall("world\n".encode())
        elif(recMessage.decode() == "goodbye"):
            connection.sendall("farewell\n".encode())
            connection.close()
            break
        elif(recMessage.decode() == "exit"):
            connection.sendall("ok\n".encode())
            connection.close()
            socket.close()
            break
        else:
            connection.sendall(recMessage)


def tcpServer(host, port):
    socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    socketServer.bind((host, port))
    socketServer.listen(5)
    print("TCP Server waiting for clients to be connected")

    while True:
        try:
            tcpConn, clientIP = socketServer.accept()
            newThread = threading.Thread(target=protocol, args=(tcpConn, socketServer))
            newThread.daemon = True
            newThread.start()
        except ConnectionAbortedError:
            print("Server is shut down by client")

    
def tcpClient(host, port):
    socketClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    socketClient.connect((host, port))

    while True:
        message = input("enter command: ")
        print('sending: ', message)
        socketClient.sendall(message.encode())
        if(message == "exit"):
            new_message = socketClient.recv(256)
            print('received: ', new_message.decode())
            break
        new_message = socketClient.recv(256)
        print('received: ', new_message.decode())

    socketClient.close()

def udpProtocol(message, sockServer, clientIP):
    print("UDP Message Received: ", message.decode())

    if(message.decode() == "hello"):
        sockServer.sendto("world\n".encode(), clientIP)
    elif(message.decode() == "goodbye"):
        sockServer.sendto("farewell".encode(), clientIP)
    else:
        sockServer.sendto(message, clientIP)


def udpServer(host, port):
    sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sockServer.bind((host, port))
    print("UDP server is on")

    while True:
        message, clientIP = sockServer.recvfrom(256)
        if(message.decode() == "exit"):
            sockServer.sendto("ok\n".encode(), clientIP)
            break
        newThread = threading.Thread(target=udpProtocol, args=(message, sockServer, clientIP))
        newThread.daemon = True
        newThread.start()

 

    sockServer.close()


def udpClient(host, port):
    
    sockClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        # message = input("enter command: ")
        message = "hi this is 2"
        sockClient.sendto(message.encode(), (host, port))

        receivedData, serverAddr = sockClient.recvfrom(256)
        
        print(receivedData.decode())
        if(receivedData.decode() == 'farewell'):
            sockClient.close()
            break
