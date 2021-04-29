import asyncio
import websockets
import signal
import json


class Websocket_client(object):
    '''
    Websocket клиент обеспечивающий:
        - соединение с сервером и переподключение в случае необходимости
        - прием сообщений из очереди queue_send и отправку их на сервер
        - завершение работы при обнаружении команды "exit" в очереди queue_send
        - прием ответов от сервера и отправку их в queue_recv 
    '''
    def __init__(self, adrr, timeout=1.0):
        """
        queue_send - очередь отправляемых сообщений
        queue_recv - очередь принятых сообщений
        adrr - адрес Websocket сервера
        timeout = время ожидания соединения с сервером
        """
        self.adrr = adrr
        self.timeout = timeout
        self.request = {
            "request": "getSensorsData",
            "type": ["latitude","latitude_side","longitude_side","course","speed","number_of_satellites","height","DUT1","DUT2"],
        }
        self.request["type"] = ["DUT1","DUT2"]
    
    async def send_recive_loop(self):
        """
        Цикл приемки о отправки сообщений
        """
        loop = asyncio.get_event_loop()
        stop = loop.create_future()
        loop.add_signal_handler(signal.SIGINT, stop.set_result, None)

        self.websocket = None
        task_recv = None
        ret = -1

        while not stop.done():

            # Если нет соединения соединиться
            if self.websocket is None:
                try:
                    self.websocket = await asyncio.wait_for(websockets.connect(self.adrr), timeout=self.timeout)
                    # asyncio.create_task(self.send_msg("{\n\"gtp\": \"uuid\"\n}"))
                    await self.send_msg(json.dumps(self.request))
                except Exception as e:
                    if len(e.args) == 0:
                        print(f"Timeout error ('{self.adrr}')")
                    else:
                        print(e)
                    self.websocket = None
                    await asyncio.sleep(1)
                    continue
            
            try:
                msg = await self.websocket.recv()
                print(json.loads(msg))
            except Exception as e:
                self.websocket.close()
                self.websocket = None
                print(e)
        
        # Перед выходом отменить активные задачи и закрыть соединение
        print("exit")
        # if task_recv is not None: task_recv.cancel()
        if self.websocket is not None: await self.websocket.close()

        return ret

    async def send_msg(self, msg):
        '''
        Отправить сообщение
        '''
        try:
            await self.websocket.send(msg)
        except Exception as e:
            print(e)
            await self.websocket.close()
            self.websocket = None

        return msg

    async def recv_msg(self):
        '''
        Получить сообщение и отправить его в очередь принятых сообщений queue_recv
        '''
        try:
            msg = await self.websocket.recv()
            print(msg)
        except Exception as e:
            self.websocket = None
            print(e)



tcp_client = Websocket_client('ws://192.168.1.50:4000')

try:
    asyncio.run(tcp_client.send_recive_loop())
except KeyboardInterrupt:
    print("KeyboardInterrupt")
finally:
#     if tcp_client.protocol:
    print("KeyboardInterrupt11")
    # asyncio.run(tcp_client.close())