import socket
import datetime
import json
import os
import time

if __name__ == '__main__':

    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf-8-sig') as file:
        _conf = json.load(file)
        socket_cfg = _conf.get('SOCKET')
        socket_port = socket_cfg['port']
        socket_ip = socket_cfg['ip']

    sock = socket.socket()
    sock.bind(('', socket_port))
    # sock.bind((socket_ip, socket_port))
    sock.listen(1)
    conn, addr = sock.accept()

    print('connected:', addr)

    while True:
        received_data = conn.recv(1024)
        if not received_data:
            break

        print("Socket Received:     {}".format(received_data))
        # conn.send(data.upper())
        now = datetime.datetime.now()
        now.strftime("%d-%m-%Y %H:%M")
        sent_data = {
            "Time": now.isoformat(),
            "DeviceType": 111,
            "DeviceId": 111,
            "Data": 1
        }
        socket_data = json.dumps(sent_data)
        socket_data = bytes(socket_data, encoding="utf-8")
        conn.send(socket_data)
        print("Socket Sent:     {}".format(socket_data))
        time.sleep(0.04)

    # conn.close()
    sock.close()
