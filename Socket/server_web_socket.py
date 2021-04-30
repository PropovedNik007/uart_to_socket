"""
Модуль ВебСервера рассылающего данные по подписке
Общий алгоритм работы сервера.
Сервер запускается и начинает принимать входящии подключения

При подключении ссылка на подключение сохраняется в словаре подключений
по IP и Port

После подключения от клиента ожидается запрос на данные в формате
{
    "request": "getSensorsData",
    "type": ["type_1", "type_2", "type_3",..."type_n" ],
}
где type массив из названий переменных на которые он подписывается.
Type  может принимать любую комбинацию из значений
["latitude","latitude_side","longitude_side","course","speed",
"number_of_satellites","height","DUT1","DUT2"]

При получении данных от Hub-а сервер рассылает всем подключеным
клиентам из словаря подключений это сообщение

Класс клиента фильтрует данные сообщения по подписаным значениям и
отправляет их клиенту в следующем формате
{
    "answer": "getSensorsData",
    "data": {
        "type_1":value_1,
        "type_2":value_2,
        "type_3":value_3,
        .
        .
        .
        "type_n":value_n,
    }
}
Type типы из запроса на подписку
Value значения полученные от Hub-а

При отключении клиента ссылка на подключение удаляется из словаря
подключений

При отключении сервера закрываются все подключения из словаря
"""

import asyncio
import websockets
import json
import signal
from websockets import WebSocketServerProtocol


class Web_Server_Parser():
    """
    Парсер сообщений от HUBа
    Извлекает значения GPS координат и значений датчиков топлива из сообщений от HUBа
    и сохраняет их в виде словаря
    """
    data_keys = [
        ("latitude", "string"),
        ("latitude_side", "string"),
        ("longitude", "string"),
        ("longitude_side", "string"),
        ("course", "uint"),
        ("speed", "uint"),
        ("number_of_satellites", "uint"),
        ("height", "uint"),
        ("DUT1", "uint"),
        ("DUT2", "uint")
    ]

    def __init__(self):
        '''
        Конструктор класса
        Подготавливает список callback-ов для каждого значения
        и инициализирует словарь значениями по умолчанию
        '''
        self.parser_callback = {x[0]:self.__getattribute__("parse_" + x[1]) 
            for x in Web_Server_Parser.data_keys}

        self._msg = {x[0]:"NA" for x in Web_Server_Parser.data_keys}

    @property
    def msg(self):
        return self._msg

    @msg.setter
    def msg(self, raw_msg):
        '''
        Setter свойства
        Парсит входную строку в соответствии с заданным форматом
        Если строка не соответствует формату возвращает словарь по умолчанию
        Если значение не соответствует формату или отсутствует ставит вместо него "NA"
        '''
        self._msg = {x[0]:"NA" for x in self.data_keys}

        if raw_msg[0] != '$' or raw_msg[-1] != '#':
            return
        
        raw_msg_list = raw_msg[1:-1].split(';')[:10]

        for i, msg_value in enumerate(raw_msg_list):
            key = self.data_keys[i][0]
            self._msg[key] = self.parser_callback[key](msg_value)

    def parse_uint(self, str_value):
        """
        Преобразование строки в UINT
        Преобразует строку в UINT
        Если сроку нельзя преобразовать в UINT
        или получается отрицательное число возвращает "NA"
        """
        try:
            return int(str_value) if int(str_value) >= 0 else "NA"
        except:
            return "NA"

    def parse_string(self, str_value):
        '''
        Преобразование строки в строку
        Возвращает исходную строку. 
        Метод необходим как заглушка в целях единства обработки значений разных типов
        '''
        return str_value


class Web_Server_Protocol(WebSocketServerProtocol):
    """
    Класс для работы с клиентами Вебсервера
    Создается экземпляр для каждого подключения
    Обеспечивает прием запроса
    Вызов callback при подключении и отключении клиентов
    И отправку сообщений с фильтрацией по запрашиваемым типам
    """
    def __init__(self, web_server, *args, **kwargs):
        """
        Конструктор класса
        -----------------
        web_server указатель на экземпляр класса Web_Server Обеспечивающий работу с подключеными клиентами
        """
        super().__init__(*args, **kwargs)
        self.web_server = web_server
        self.request_filter = None

    @staticmethod
    async def request_handler(ws:WebSocketServerProtocol, uri: str)->None:
        """
       Обработчик запросов от клиентов
       Принимает запрос от клиента и устанавливает фильтр значений отправляемых по подписке
        -----------------
        ws - указатель на экземпляр класса WebSocketServerProtocol
        uri - путь
        """
        try:
            async for message in ws:
                data = json.loads(message)
                if data.get("request","") == "getSensorsData":
                    ws.request_filter = data.get("type", [])
                await ws.send(message)
        except:
            await asyncio.sleep(1)
            return

    def connection_made(self, transport):
        """
       Callback функция вызываемая при установке соединения
       Прокидывает вызов базовому классу для корректного завершения соединения
       и вызывает callback функцию Web_Server.connection_made сохраняющее
       указатель на WebSocketServerProtocol этого соединения в список
        -----------------
        transport - указатель на экземпляр класса asyncio.Protocol
        """
        WebSocketServerProtocol.connection_made(self, transport)
        self.web_server.connection_made(self)

    def connection_lost(self, exc):
        """
       Callback функция вызываемая при разрыве соединения
       Прокидывает вызов базовому классу для корректного завершения разъединения
       и вызывает callback функцию Web_Server.connection_lost удаляющее
       указатель на WebSocketServerProtocol этого соединения из списока
        -----------------
        exc - ???
        """
        websockets.WebSocketClientProtocol.connection_lost(self, exc)
        self.web_server.connection_lost(self, exc)

    async def send(self, msg):
        """
        Корутина отправки сообщения
        Принимает на вход сообщение от HUBа в распарсеном виде, проводит фильтрацию
        по подписаным типам, заворачивает в json и отправляет потребителю
        -----------------
        msg - Словарь содержащий сообщение от HUBа в распарсеном виде
        """
        answer = {
            "answer": "dfgdfgdf"
        }
        await websockets.WebSocketClientProtocol.send(self, json.dumps(answer))

    @property
    def request_filter(self):
        '''
        _request_filter свойство ответственное за хранение фильтров
        '''
        return self._request_filter

    @request_filter.setter
    def request_filter(self, msg):
        self._request_filter = msg


class Web_Server():
    '''
    Класс для работы c Вебсервером по рассылающим данные по подписке
    Инкапсулирует в себя:
    Функции создания и остановки сервера
    Атоматическую запись и удаление подключеных клиентов в словарь подключений
    Функцию отправкки сообщения всем клиентам из словаря подключений
    '''
    count = 0

    def __init__(self, clients = None):
        '''
        Конструктор класса
        -----------------
        clients - Источник данных. Для получения необходимо зарегистрировать в нем
        callback функцию
        '''
        self.tcp_client = None if clients is None else clients[0] 

        self.ws = dict()

        # self.msg_parser = Web_Server_Parser()

        self.ip, self.port = None, None


    async def serve(self, ip, port):
        '''
        Создать сервер
        -----------------
        ip, port - ip и port где создается сервер
        '''
        self.ip, self.port = ip, port
        try:
            self.start_server = await websockets.serve(
                Web_Server_Protocol.request_handler,
                ip, port, 
                create_protocol=self.get_protocol
            )

            if self.tcp_client is not None:
                print("GPS_DUT_WebSocket_Server. При создании сервера не указан источник данных")
                self.tcp_client.register_GPS_DUT_client(f"{ip}:{port}", self.send2all)
        except Exception as e:
            await self.stop_serve()
            raise(e)

    async def stop_serve(self):
        """
        Остановить сервер
        """
        if self.tcp_client is not None:
            self.tcp_client.unregister_GPS_DUT_client(f"{self.ip}:{self.port}")
        self.ip, self.port = None, None

        self.start_server.close()

        while len(self.ws) != 0:
            await asyncio.sleep(0.1)

    def connection_made(self, ws):
        '''
        Зарегистрировать клиента в словарь подключений
        Callback функция вызываема при подключении нового клиента
        -----------------
        ws - ссылка на подключение
        '''
        peername = ws.transport.get_extra_info('peername')
        self.ws[str(peername)] = ws
        print(f"Connection {peername} established")

    def connection_lost(self, ws, exc):
        """
        Удалить клиента из словаря подключений
        Callback функция вызываема при отключении клиента
        -----------------
        ws - ссылка на подключение
        exc -
        """
        peername = ws.transport.get_extra_info('peername')
        self.ws.pop(str(peername), None)
        print(f"Lost connection {peername}")

    def send2all(self, msg):
        '''
        Рассылает сообщение по клиентам из словаря подключений
        Callback функция вызываема при получении новых данных от HUB-а
        -----------------
        msg - строка сообщения
        '''
        # self.msg_parser.msg = msg
        for ws in self.ws.values():
            asyncio.create_task(ws.send(msg))

    def get_protocol(self, *args, **kwargs):
        return Web_Server_Protocol(self, *args, **kwargs)


async def main():

    server = Web_Server()
    # await server.serve("192.168.1.91", 4000)
    await server.serve("192.168.1.50", 4000)


    loop = asyncio.get_event_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

    i = 0
    while not stop.done():

        message = f"$5543.17322;N;03738.16101;E;0;0;12;134;NA;{i};11#"
        server.send2all(message)


        # for ws in server.ws.values():
        #     asyncio.create_task(ws.send(msg))



        ip, port = server.ip, server.port
        server.start_server = await websockets.serve(
            Web_Server_Protocol.request_handler,
            ip, port,
            create_protocol=server.get_protocol
        )
        i += 1
        await asyncio.sleep(1)
    
    await server.stop_serve()
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass