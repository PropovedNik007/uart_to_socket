import errno
import os
import json
import serial
import time
import struct
import crc16
import numpy as np


class Packet(object):
    def __init__(self, preamble, size, type_pack, mess, crc, postamble,  ser, timeout=1):
        self.ser = ser
        self.timeout = timeout
        self.preamble = preamble
        self.size = size
        self.type_pack = type_pack
        self.mess = mess
        self.crc = crc
        self.postamble = postamble

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

    def serial_read(self, request, ser):
        # Запросим данные
        self.send_cmd(request, ser)
        # Считаем количество байт в структуре заголовка
        head, cnt = self.read_bytes(4)
        print('length', cnt)

        length = self.get_head_length(head)

        # Считаем структуру заголовка

        ret = self.read_bytes(length - 4)
        head += ret[0]
        print('head', ret[1])

        # Извлечем из структуры размер передаваемого кадра в байтах
        data_size = self.get_data_size(head)

        # Считаем кадр
        start_time = time.time()
        data, cnt = self.read_bytes(data_size)
        print('data', cnt)
        print('readBytes', time.time() - start_time)

        return data, head

    def send_cmd(self, q, ser):
        ser.write(q)
        # q = bytes(q)
        # while True:
        #     try:
        #         # ret = os.write(self.cmd, q)
        #         ret = ser.write(q)
        #     except IOError as e:
        #         print(e.strerror)
        #         raise Exception("Error writing uart")
        #
        #     if ret == 0:
        #         time.sleep(self.timeout)
        #         continue
        #
        #     if ret != 24:
        #         raise Exception("Error writing uart")
        #     return True

    def read_bytes(self, num_bytes, fr=4096):
        """
        Считать num_bytes байтов из serial. Данные считываются блоками размера
        min(fr, num_bytes)
        --------------------------------
        num_bytes - размер считываемых данных
        fr - размер блока
        """

        recive_bytes = b''
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
                raise Exception("Error reading pipe")  # Остальные ошибки

            if len(rcv) == 0:
                time.sleep(self.timeout)
                continue

            # if len(recive_frame) != read_bytes: # Ошибка чтения данных
            #     raise Exception("Error reading pipe")

            num_bytes -= len(rcv)
            recive_bytes += rcv

            if num_bytes <= 0:
                break

        return recive_bytes, cnt

    def get_head_length(self, head):
        """
        Размер заголовка в байтах
        """
        return int.from_bytes(head[:4], 'little')

    def get_result(self, head):
        """
        Тип ответа
        """
        return int.from_bytes(head[4:8], 'little')

    def get_data_size(self, head):
        """
        Размер данных кадра в байтах
        """
        return int.from_bytes(head[16:20], 'little')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8-sig') as file:
        _conf = json.load(file)
        uart_cfg = _conf.get('UART')
        uart_port_read = uart_cfg['port_read']
        uart_port_write = uart_cfg['port_write']
        uart_baudrate = uart_cfg['baudrate']
        uart_timeout = uart_cfg['timeout']

    ser = serial.Serial(port=uart_port_read,  baudrate=uart_baudrate, timeout=uart_timeout)
    ser_write = serial.Serial(port=uart_port_write,  baudrate=uart_baudrate, timeout=uart_timeout)
    preamble = b'\x5A\x5A'
    size = 10
    device_type = 255
    device_id = 255
    mess = 0
    body = struct.pack('BBBB', size, device_type, device_id, mess)
    crc = (crc16.crc16xmodem(body))
    postamble = b'\x7a\x7a'

    request = struct.pack('2sBBBBH2s', preamble, size, device_type, device_id, mess, crc, postamble)
    ser_write.write(request)
    print("UART write", struct.unpack('2sBBBBH2s', request))
    print("UART", request)
    time.sleep(0.04)

    # for i in range(0, 255):
    #     preamble = b'\x5A\x5A'
    #     size = 10
    #     device_type = i
    #     device_id = i
    #     mess = 1
    #     body = struct.pack('BBBB', size, device_type, device_id, mess)
    #     crc = (crc16.crc16xmodem(body))
    #     postamble = b'\x7a\x7a'
    #     request1 = struct.pack('2sBBBBH2s', preamble, size, device_type, device_id, mess, crc, postamble)
    #     ser.write(request1)
    #     print(request1)
    #     print("UART", struct.unpack('2sBBBBH2s', request1))
    #     time.sleep(0.1)
