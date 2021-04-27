import errno
import socket
import serial
import time
import datetime
import struct
import crc16
import json


class Packet(object):
    def __init__(self):
        self.port = "/dev/ttyUSB0"
        self.baudrate = 115200
        self.timeout = 0.01
        self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        self.preamble = b'\x5A\x5A'
        self.size = 10
        self.device_type = 255
        self.device_id = 255
        self.mess = 0
        self.body = struct.pack('BBBB', self.size, self.device_type, self.device_id, self.mess)
        self.crc = (crc16.crc16xmodem(self.body))
        self.postamble = b'\x7A\x7a'

    def open(self):
        self.ser = None

        try:
            self.ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=self.timeout)
            print("Open serial UART")
        except Exception as e:
            print(e)
            raise Exception("Error opening input serial UART")

        return self.ser

    def close(self, ser):
        if self.ser:
            self.ser.close()

    def __del__(self):
        self.close(ser)

    def serial_read(self):

        # Ищем преамбулу
        head = self.start_package(ser)
        if head is None:
            print("PREAMBLE")
            return 0

        self.preamble = self.get_preamble(head)
        # self.preamble = head
        # print(head)

        package = head
        size = self.read_bytes(1)
        self.size = int.from_bytes(size, 'little')
        package += size
        # self.size = self.get_size(body)
        remainder = self.read_bytes(self.size - len(package))
        self.postamble = self.get_postamble(remainder)
        if not self.postamble:
            print("POST")
            return 0
        else:
            self.device_type = self.get_device_type(remainder)
            self.device_id = self.get_device_id(remainder)
            self.mess = self.get_mess(remainder)
            self.body = struct.pack('BBBB', self.size, self.device_type, self.device_id, self.mess)
            self.crc = self.get_crc(remainder)
            crc = (crc16.crc16xmodem(self.body))
            # print("CRC", self.crc)
            # print("CRC", crc)
            if self.crc != crc:
                print("CRC", self.crc)
                print("CRC", crc)
                return 0

        return object

    def read_bytes(self, num_bytes):
        """
        Считать num_bytes байтов из serial. Данные считываются блоками размера
        min(fr, num_bytes)
        --------------------------------
        num_bytes - размер считываемых данных
        fr - размер блока
        """

        recive_bytes = b''
        # recive_bytes = ''
        cnt = 0
        while True:

            cnt += 1
            read_bytes = num_bytes  # min(num_bytes,fr)
            try:
                rcv = ser.read(read_bytes)
            except IOError as e:
                if e.errno == errno.EWOULDBLOCK:  # Данные ешще не готовы
                    time.sleep(self.timeout)
                    continue
                print(e.strerror)
                raise Exception("Error reading com")  # Остальные ошибки

            if len(rcv) == 0:
                time.sleep(0.01)
                continue

            num_bytes -= len(rcv)
            recive_bytes += rcv

            if num_bytes <= 0:
                break

        return recive_bytes

    def get_preamble(self, head):
        # return int.from_bytes(head[:2], 'little')
        preamble = head[:2].hex()
        if preamble == '5a5a':
            return preamble
        else:
            return 0

    def get_device_type(self, remainder):
        # return int.from_bytes(remainder[0], 'little')
        return remainder[0]

    def get_device_id(self, remainder):
        # return int.from_bytes(remainder[1:2], 'little')
        return remainder[1]

    def get_mess(self, remainder):
        # return int.from_bytes(remainder[2:3], 'little')
        # return remainder[2]
        return int.from_bytes(remainder[2:-4], 'little')

    def get_crc(self, remainder):
        # return int.from_bytes(remainder[3:5], 'little')
        return int.from_bytes(remainder[-4:-2], 'little')

    def get_postamble(self, remainder):
        # postamble = remainder[5:7].hex()
        postamble = remainder[-2:].hex()
        if postamble == '7a7a':
            return postamble
        else:
            return 0

    def start_package(self, ser):
        while True:
            while ser.read(1) != self.preamble[:1]:
                time.sleep(0.01)
            if ser.read(1) == self.preamble[1:2]:
                # print("Preamble")
                return self.preamble
        return None


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # ser = serial.Serial(port="/dev/ttyUSB0", bytesize=8, stopbits=1, timeout=1.0)
    ser = serial.Serial(port="/dev/ttyUSB0", baudrate=115200, timeout=0.01)
    # preamble = b'5A5A'
    # size = bytes(8)
    # type_pack = b'01'
    # mess = b'00'
    # crc = (crc16.crc16xmodem(size + type_pack + mess))
    # postamble = preamble
    # pack_cmd = Packet(preamble, size, type_pack, mess, crc, postamble)
    # pack_cmd.open()
    # request = struct.unpack('2sBBBBH2s', rcv)
    # request = struct.pack('2sBBBBH2s', rcv)

    sock = socket.socket()
    sock.connect(('localhost', 9090))

    # sock.close()

    while ser:
        pack_cmd = Packet()
        if not pack_cmd.serial_read():
            time.sleep(0.01)
            continue
        else:
            # print("body", pack_cmd.body)
            print(
                pack_cmd.preamble,
                pack_cmd.size,
                pack_cmd.device_type,
                pack_cmd.device_id,
                pack_cmd.mess,
                pack_cmd.crc,
                pack_cmd.postamble,
            )
            now = datetime.datetime.now()
            now.strftime("%d-%m-%Y %H:%M")
            output = {
                "Time": now.isoformat(),
                "DeviceType": pack_cmd.device_type,
                "DeviceId,": pack_cmd.device_id,
                "Data": pack_cmd.mess,
            }
            socket_data = json.dumps(output)
            print("SOCKET send", socket_data)

            # # Connect to server and send data
            sock.sendall(bytes(socket_data, encoding="utf-8"))
            # data = sock.recv(1024)
            # # Receive data from the server and shut down
            # received = sock.recv(1024)
            # received = received.decode("utf-8")
            #
            # print("Sent:     {}".format(socket_data))
            # print("Received: {}".format(received))

            time.sleep(0.01)
            continue
    sock.close()


