import errno
import socket
import serial
import time
import datetime
import struct
import crc16
import json
import os


class Packet(object):

    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8-sig') as file:
            _conf = json.load(file)
            uart_cfg = _conf.get('UART')
            uart_port_read = uart_cfg['port_read']
            uart_port_write = uart_cfg['port_write']
            uart_baudrate = uart_cfg['baudrate']
            uart_timeout = uart_cfg['timeout']
            socket_cfg = _conf.get('SOCKET')
            socket_port = socket_cfg['port']
            socket_ip = socket_cfg['ip']
        self.port = uart_port_read
        self.port_write = uart_port_write
        self.baudrate = uart_baudrate
        self.timeout = uart_timeout
        self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        self.ser_write = serial.Serial(port=self.port_write, baudrate=self.baudrate, timeout=self.timeout)
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
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
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

    def serial_read(self, ser):

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
            # byte = ser.read(1)
            while ser.read(1) != self.preamble[:1]:
            # while byte != self.preamble[:1]:
            #     if byte != b'':
            #         print("not", byte)
                time.sleep(0.01)
            if ser.read(1) == self.preamble[1:2]:
                # print("Preamble")
                return self.preamble
        return None


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8-sig') as file:
        _conf = json.load(file)
        uart_cfg = _conf.get('UART')
        uart_port_read = uart_cfg['port_read']
        uart_port_write = uart_cfg['port_write']
        uart_baudrate = uart_cfg['baudrate']
        uart_timeout = uart_cfg['timeout']

        socket_cfg = _conf.get('SOCKET')
        socket_port = socket_cfg['port']
        socket_ip = socket_cfg['ip']
    # ser = serial.Serial(port="/dev/ttyUSB0", bytesize=8, stopbits=1, timeout=1.0)
    ser = serial.Serial(port=uart_port_read, baudrate=uart_baudrate, timeout=uart_timeout)
    ser_write = serial.Serial(port=uart_port_write, baudrate=uart_baudrate, timeout=uart_timeout)

    sock = socket.socket()
    sock.connect((socket_ip, socket_port))

    # sock.close()

    while ser:
        pack_cmd = Packet()
        if not pack_cmd.serial_read(ser):
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
                "DeviceId": pack_cmd.device_id,
                "Data": pack_cmd.mess,
            }
            socket_data = json.dumps(output)

            # # Connect to server and send data
            sock.sendall(bytes(socket_data, encoding="utf-8"))
            time.sleep(0.01)
            # # Receive data from the server and shut down
            received = sock.recv(1024)
            received = received.decode("utf-8")
            received = json.loads(received)
            device_type = received.get("DeviceType")
            device_id = received.get("DeviceId")
            mess = received.get("Data")

            preamble = b'\x5A\x5A'
            size = 10
            body = struct.pack('BBBB', size, device_type, device_id, mess)
            crc = (crc16.crc16xmodem(body))
            postamble = b'\x7a\x7a'

            request = struct.pack('2sBBBBH2s', preamble, size, device_type, device_id, mess, crc, postamble)
            # ser_write = serial.Serial(port=uart_port_write, baudrate=uart_baudrate, timeout=uart_timeout)
            ser_write.write(request)
            # ser.write(request)
            #
            print("Socket Sent:     {}".format(socket_data))
            print("Socket Received: {}".format(received))
            print("UART write:      {}".format(request))

            time.sleep(0.01)
            # ser.write(request)
            continue
    sock.close()



