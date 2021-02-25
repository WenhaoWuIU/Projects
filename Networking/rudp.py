# This is the implementation of reliable UDP 
# This section includes rudp server and rudpclient
# with protocols of stop-and-wait and go-back-N. 
# Congestion control is also included as well. 


import socket
import threading
import os
import hashlib
import sys
import time
from _thread import *
import re

def rudpServer(host, port):
   sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   sockServer.bind((host, port))
   print("RUDP server is on")

   countSeq = 0
   recvedAcks = set()
   while True:

       message, clientIP = sockServer.recvfrom(1024)

       #checkSum set up
       msgText = message.decode()
       msgContent = msgText.partition("\n")[2]
       print(msgContent)
       checkSum = hashlib.md5(msgContent.encode()).hexdigest()
       headerNums = [int(i) for i in message.split() if i.isdigit()]

       if(message.decode().startswith( 'Header Info ' )):
           sockServer.sendto("ACK".encode(), clientIP)
       elif(message.decode() == "File Transfer Finsihed"):
           print("File Transfer Finsihed")
           countSeq = 0
       elif(headerNums[0] in recvedAcks):
           sockServer.sendto(("ACK"+str(headerNums[0])).encode(), clientIP)
           print("duplicate acks and packet", headerNums[0], " is resent")
       elif(checkSum not in msgText):
           sockServer.sendto(("NAK"+str(headerNums[0])).encode(), clientIP)
       else:
           if countSeq == headerNums[0] and checkSum in msgText:
               print("packet", headerNums[0], "received at server and check sum: ", checkSum)
               recvedAcks.add(headerNums[0])
               sockServer.sendto(("ACK"+str(headerNums[0])).encode(), clientIP)
               countSeq += 1
               f = open("receivedFile.txt", "a")
               f.write(msgContent)
               f.close()

   sockServer.close()





def rudpClient(host, port, file):
   sockClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

   max_size = 150
   #File information group
   f = open(file, 'rb')
   package = f.read(max_size)
   fileSize = os.path.getsize(file)
   packSize = sys.getsizeof(package)

   numPackets = fileSize // max_size + 1
   checkSum = hashlib.md5(package).hexdigest()

   seqNum = 0
   headerRecved = False
   headerInfo = "Header Info " + str(numPackets) + " " + str(fileSize)




   #rdt_send header information
   while headerRecved == False:
       sockClient.sendto(headerInfo.encode(), (host, port))
       sockClient.settimeout(2.0)
       try:
           receivedDataHeader, serverAddr = sockClient.recvfrom(1024)
       except socket.timeout:
           sockClient.sendto(headerInfo.encode(), (host, port))
           print("Header resend after time out")
       timeOut = time.time() + 2
       while True:
           if(receivedDataHeader.decode() == "ACK"):
               headerRecved = True
               print("File header received by server")
               break
           if time.time() > timeOut:
               sockClient.sendto(headerInfo.encode(), (host, port))
               timeOut = time.time() + 2
               print("File header resend")

   #rdt_send packets information
   while numPackets > 0:

       packetHeader = "Packet Header: " + str(seqNum) + " " + str(checkSum) + str(packSize)
       dataGram = packetHeader + "\n" + package.decode()

       sockClient.sendto(dataGram.encode(), (host, port))
       timeOut = time.time() + 2

       sockClient.settimeout(2.0)
       try:
           receivedData, serverAddr = sockClient.recvfrom(1024)
       except socket.timeout:
           print("no message received and time out and resend packet")
           sockClient.sendto(dataGram.encode(), (host, port))
           print("packet", seqNum, "resend after time out")

       while True:
           if(receivedData.decode() == "ACK"+str(seqNum)):
               print("packet " + str(seqNum) + " received by server and check sum: ", checkSum)
               package = f.read(max_size)
               checkSum = hashlib.md5(package).hexdigest()
               packSize = sys.getsizeof(package)
               numPackets -= 1
               seqNum = seqNum + 1
               break
           else:
               if time.time() > timeOut:
                   sockClient.sendto(dataGram.encode(), (host, port))
                   timeOut = time.time() + 2
                   print("packet " + str(seqNum)+ " resend")
                   break
           if(receivedData.decode() == "NAK"+str(seqNum)):
               sockClient.sendto(dataGram.encode(), (host, port))
               print("NAK received, packet resend")
               timeOut = time.time() + 2
               break




   print("File Transfer Finished")
   sockClient.sendto("File Transfer Finsihed".encode(), (host, port))

   sockClient.close()




def rudpClientGBN(host, port, file):
    sockClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    max_size = 50
    window_size = 4
    f = open(file, 'rb')

    dataChunks = {}
    fileSize = os.path.getsize(file)
    numPackets = fileSize // max_size + 1
    seqNum = 0

    timerList = {}
    #pack the data chuncks with header
    for i in range(numPackets):
        timerList["timer"+str(i)] = time.time()
        packet = f.read(max_size)
        checkSum = hashlib.md5(packet).hexdigest()
        dataChunks["packet"+str(i)] = str(i) + " " + str(len(packet)) + " " + str(checkSum) + " " + "contents: " + str(packet)


    #send the first window of packets
    for i in range(window_size):
        timerList["timer"+str(i)] = time.time() + 2 #start timer for each packet being sent
        sockClient.sendto(dataChunks["packet"+str(i)].encode(), (host, port))
        seqNum += 1

    recvedAcks = set()
    while True:
        sockClient.settimeout(2.0)
        try:
            receivedData, serverAddr = sockClient.recvfrom(1024)
        except socket.timeout:
            sockClient.sendto(dataChunks["packet"+str(seqNum - window_size)].encode(), (host, port))
            print("Time out, packet", str(seqNum - window_size), " is resent")

        expectACK = "ACK"+ str(seqNum - window_size)

        #When data received correctly
        if(receivedData.decode() == expectACK):
            print(expectACK, " received")
            timerList["timer"+str(seqNum - window_size)] = time.time() + 2

            sockClient.sendto(dataChunks["packet"+str(seqNum - window_size)].encode(), (host, port))
            recvedAcks.add(receivedData.decode())
            if seqNum < len(dataChunks) + 4 :
                seqNum += 1

        #time out and still not receive expected packet
        elif (timerList["timer"+str(seqNum - window_size)] < time.time()) and (expectACK not in recvedAcks):
            print("timer"+str(seqNum - window_size), " time out ", recvedAcks)
            for i in range(window_size):
                if (seqNum + i) < len(dataChunks):
                    timerList["timer"+str(seqNum + i - window_size)] = time.time() + 2
                    sockClient.sendto(dataChunks["packet"+str(seqNum + i - window_size)].encode(), (host, port))
                else:
                    break


        #when duplicated ACKs received
        elif (receivedData.decode() in recvedAcks):
            print("Duplicated ACK: ", receivedData.decode())
            continue

        else:
            if(receivedData.decode() not in recvedAcks):
                print(receivedData.decode(), " received")
                recvedAcks.add(receivedData.decode())
            lastACK = "ACK"+ str(len(dataChunks))
            if(receivedData.decode() == lastACK):
                print("File Transfer Finished")
                break

    sockClient.close()





def rudpServerGBN(host, port):

    sockServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockServer.bind((host, port))
    print("UDP GBN server is on")

    countSeq = 0

    while True:
        message, clientIP = sockServer.recvfrom(1024)

        #checkSum set up
        msgText = message.decode()
        msgContent = msgText.partition("contents: ")[2]
        checkSum = hashlib.md5(msgContent.encode()).hexdigest()
        headerNums = [int(i) for i in message.split() if i.isdigit()]



        if(message.decode() == "File Transfer Finsihed"):
            countSeq = 0
        elif(countSeq != headerNums[0]):
            print("seq # is wrong and the headerNums is ", headerNums[0], " and seqNum is ", countSeq)
            sockServer.sendto(("ACK"+str(countSeq+1)).encode(), clientIP)
        else:
            print(msgContent)
            if countSeq == headerNums[0]:
                print("seq number is right")
                sockServer.sendto(("ACK"+str(headerNums[0])).encode(), clientIP)
                countSeq += 1
                f = open("receivedFile.txt", "a")
                f.write(msgContent)
                f.close()

    sockServer.close()















def rudpClientGBNCC(host, port, file):
   sockClient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

   max_size = 50
   window_size = 1
   f = open(file, 'rb')

   dataChunks = {}
   fileSize = os.path.getsize(file)
   numPackets = fileSize // max_size + 1
   seqNum = 0

   timerList = {}
   #pack the data chuncks with header
   for i in range(numPackets):
       timerList["timer"+str(i)] = time.time()
       packet = f.read(max_size)
       checkSum = hashlib.md5(packet).hexdigest()
       dataChunks["packet"+str(i)] = str(i) + " " + str(len(packet)) + " " + str(checkSum) + " " + "contents: " + str(packet)

   ssthresh = 8
   recvedAcks = set()
   expectedACKs = set()
   tripleAcks = 0


   while True:
       if len(expectedACKs) == 0:
           print("window size: ", window_size)
           for i in range(seqNum, seqNum + window_size):
               if i == len(dataChunks):
                   break
               else:
                   timerList["timer"+str(i)] = time.time() + 0.25 #start timer for each packet being sent
                   sockClient.sendto(dataChunks["packet"+str(i)].encode(), (host, port))
                   expectedACKs.add("ACK"+ str(i))
           seqNum += window_size
           if window_size >= ssthresh:
               window_size += 1
           else:
               window_size = window_size * 2


       receivedData, serverAddr = sockClient.recvfrom(1024)
       stringNum = re.findall(r'\d+', receivedData.decode())
       #send window-sized packets


       #when duplicated ACKs received
       if (receivedData.decode() in recvedAcks):
           tripleAcks += 1
           if tripleAcks == 3:
               print("Triple ACKs")
               ssthresh = window_size/2
               window_size = ssthresh
               tripleAcks = 0
           print("Duplicated ACK: ", receivedData.decode())


       #When data received correctly
       if(receivedData.decode() in expectedACKs):
           print(receivedData.decode(), " received")
           expectedACKs.remove(receivedData.decode())
           recvedAcks.add(receivedData.decode())

       #time out and still not receive expected packet
       if(timerList["timer"+stringNum[0]] < time.time()) and (receivedData.decode() not in recvedAcks):
           print("timer"+stringNum[0], " time out")
           ssthresh = window_size/2
           window_size = 1

       else:
           if(receivedData.decode() not in recvedAcks):
               print(receivedData.decode(), " received-s")
               recvedAcks.add(receivedData.decode())
           lastACK = "ACK"+ str(len(dataChunks)-1)
           if(receivedData.decode() == lastACK):
               print("File Transfer Finished")
               break

   sockClient.close()