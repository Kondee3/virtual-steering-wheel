import socket
import time
import threading

class UDPRecv(threading.Thread):
    def __init__(self, IpAddressToRecv, IpPortToRecv):
        threading.Thread.__init__(self)
        self.__UDP_IP_Recv = str(IpAddressToRecv)
        self.__UDP_PORT_Recv = IpPortToRecv
        self.__recvSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__recvSock.bind((self.__UDP_IP_Recv, self.__UDP_PORT_Recv))
        self.__recvBuffer = []
        self.__recvNewData = False
        self.start()

    def ReadRawData(self):
        if self.__recvNewData:
            self.__recvNewData = False
            return self.__recvBuffer
        else:
            return []

    def ReadIntData(self):
        data = self.ReadRawData()
        int_values = [x for x in data]
        return int_values

    def run(self):
        while True:
            try:
                data, addr = self.__recvSock.recvfrom(8192)
                if len(data) > 0:
                    self.__recvBuffer = bytearray(data)
                    self.__recvNewData = True
            except:
                None
            time.sleep(0.01)
