import socket
import time
import threading

class UDPSend(threading.Thread):
    def __init__(self, IpAddressToSend, IpPortToSend):
        threading.Thread.__init__(self)
        self.__UDP_IP_Send = str(IpAddressToSend)
        self.__UDP_PORT_Send = IpPortToSend
        self.__sendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sendBuffer = []
        self.__sendFlag = False
        self.start()

    def UpdateSendingIP(self, data):
        self.__UDP_IP_Send = str(data)

    def UpdateSendingPORT(self, data):
        self.__UDP_PORT_Send = str(data)

    def SendDataByUDPInThreadINT(self, databuffer):
        self.__sendBuffer = []
        self.__sendBuffer = bytearray(databuffer)
        self.__sendFlag = True

    def SendDataByUDPInThreadBYTE(self, databuffer):
        self.__sendBuffer = []
        self.__sendBuffer = databuffer
        self.__sendFlag = True
    def run(self):
        while True:
                if self.__sendFlag:
                    self.__sendSock.sendto(self.__sendBuffer, (self.__UDP_IP_Send, self.__UDP_PORT_Send))
                    self.__sendFlag = False
                time.sleep(0.001)

