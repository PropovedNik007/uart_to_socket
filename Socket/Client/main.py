import socket
import errno
import serial
import time
import datetime
import struct
import crc16
import json


if __name__ == '__main__':

    sock = socket.socket()
    sock.connect(('localhost', 9090))
    sock.send(b"gblh")
    # ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=0.01)
    preamble = b'\x5A\x5A'
    size = 10
    device_type = 255
    device_id = 255
    mess = 0
    body = struct.pack('BBBB', size, device_type, device_id, mess)
    crc = (crc16.crc16xmodem(body))
    postamble = b'\x7a\x7a'

    request = struct.pack('2sBBBBH2s', preamble, size, device_type, device_id, mess, crc, postamble)
    # ser.write(request)
    print(request)
    print(struct.unpack('2sBBBBH2s', request))
    time.sleep(1)

    # ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
    for i in range(0, 255):
        preamble = b'\x5A\x5A'
        size = 10
        device_type = i
        device_id = i
        mess = 1
        body = struct.pack('BBBB', size, device_type, device_id, mess)
        crc = (crc16.crc16xmodem(body))
        postamble = b'\x7a\x7a'
        request1 = struct.pack('2sBBBBH2s', preamble, size, device_type, device_id, mess, crc, postamble)
        # ser.write(request1)
        print(request1)
        print("UART", struct.unpack('2sBBBBH2s', request1))
        time.sleep(0.04)
        # sock.sendall(bytes(request1, encoding="utf-8"))
        sock.sendall(request1)
        # sock.send()

        data = sock.recv(1024)
    # sock.close()

        print(data)
