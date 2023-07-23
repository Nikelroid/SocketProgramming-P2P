import sys
import threading
import asyncio
import base64

result = ""
logs = []


class EchoServerProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
         #print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        message = data.decode()
         #print('Data received: {!r}'.format(message))

         #print('Send: {!r}'.format(globfile[:50]) + "...")

        self.transport.write(globfile.encode())

         #print('Close the client socket')
        self.transport.close()


async def main_server(address):
    loop = asyncio.get_running_loop()

    server = await loop.create_server(
        lambda: EchoServerProtocol(), address[0], int(address[1]))

    async with server:
        await server.serve_forever()


class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost

    def connection_made(self, transport):
        transport.write(self.message.encode())
         #print('Data sent: {!r}'.format(self.message))

    def data_received(self, data):
        # #print('Data received: {!r}'.format(data.decode()[:50]+"...  size:"+str(len(data.decode()))))
        # #print(filesize)
        global pbar
        pbar.update()
        global received
        new = data.decode()
        received = received + new

    def connection_lost(self, exc):
         #print('The server closed the connection')
        self.on_con_lost.set_result(True)


async def main_client(address):
    global received
    received = ''
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = 'get ' + argumentList[1]  # name of the file

    transport, protocol = await loop.create_connection(
        lambda: EchoClientProtocol(message, on_con_lost), address[0], int(address[1]))

    #

    try:
        await on_con_lost
    finally:
        img_file = open("input-" + argumentList[1], 'wb')
        img_file.write(base64.b64decode(received))
        img_file.close()
        transport.close()


class EchoClientProtocolUDP:

    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport = None
        self.result = ""

    def connection_made(self, transport):
        self.transport = transport
         #print('Send:   ', self.message)
        self.transport.sendto(self.message.encode())

    def datagram_received(self, data, addr):
         #print("Received:", data.decode())
        global result
        result = data.decode()

         #print("Close the socket")
        self.transport.close()

    def error_received(self, exc):
         #print('Error received:', exc)
        pass

    def connection_lost(self, exc):
         #print("Connection closed")
        self.on_con_lost.set_result(True)


async def main_client_udp(status, destination, file_name, address):
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    if status == 'check':
        message = status + " " + file_name + " " + address + " " + str(0)
    else:
        message = status + " " + file_name + " " + address + " " + str(filesize)

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoClientProtocolUDP(message, on_con_lost),
        remote_addr=(destination[0], int(destination[1])))
    try:
        await on_con_lost
    finally:
        transport.close()


argumentList = sys.argv[1:]
import time





def keep_alive(status, address, filename):
    while (True):
        time.sleep(5)
        logs.append('peer-info-A signal sent to tracker ' + argumentList[2] + ' from peer ' + argumentList[3])
        asyncio.run(main_client_udp('alive', argumentList[2].split(":"), argumentList[1], argumentList[3]))


def run_server(status, address, filename):
    if status == 'share':

        global globfile
        with open(filename, "rb") as image2string:
            converted_image = base64.b64encode(image2string.read())
        globfile = converted_image.decode()
         #print('File Shared on ip ' + address.split(":")[0] + ' and ' + address.split(":")[1])
        logs.append('peer-info-File Shared on ip ' + address.split(":")[0] + ' and ' + address.split(":")[1])
        asyncio.run(main_server(address.split(":")))
    elif status == 'get':
        logs.append('peer-info-Server started on ip ' + address.split(":")[0] + ' and ' + address.split(":")[
            1] + ' and does not sharing any file.')
        globfile = filename
        asyncio.run(main_server(address.split(":")))
    else:
         #print("Can't recognize command.")
        return 0

def get_query():
    while (True):
        q = str(input('Input your query: '))
        if q == 'request logs':
            for log in logs:
                print(log)

t = threading.Thread(target=run_server, args=(argumentList[0], argumentList[3], argumentList[1]))
alive = threading.Thread(target=keep_alive, args=(argumentList[0], argumentList[3], argumentList[1]))
query = threading.Thread(target=get_query)

query.start()
t.start()
import os
import random

global filesize

from tqdm import tqdm

if argumentList[0] == 'share':
    filesize = os.path.getsize(argumentList[1])
    asyncio.run(main_client_udp('submit', argumentList[2].split(":"), argumentList[1], argumentList[3]))
     #print("inform UDP server in ip " + argumentList[2].split(":")[0] + " and " + argumentList[2].split(":")[1])
    logs.append(
        "peer-info-inform UDP server in ip " + argumentList[2].split(":")[0] + " and " + argumentList[2].split(":")[1])
    alive.start()

if argumentList[0] == 'get':
    asyncio.run(main_client_udp('check', argumentList[2].split(":"), argumentList[1], argumentList[3]))
    if (result == '404'):
        logs.append('peer-info-File ' + argumentList[1] + ' not found in tracker')
         #print('File not found.')
    else:
        newadds, size = result.split(" ")
        logs.append('peer-info-Response ' + result + ' received form tracker')
        newadd = random.choice(tuple(newadds.split("-")))
        filesize = size
        logs.append('peer-info-File will receive from ' + newadd)
         #print("File '+ argumentList[1] +' will receive from " + newadd)
        global pbar
        pbar = tqdm(total=int(int(size) * 1.45 / 32768))
        logs.append('peer-info-pbar started with ' + str(int(int(size) * 1.45 / 32768)) + ' steps')
        asyncio.run(main_client(newadd.split(":")))
        pbar.close()
         #print('File received successfully!')
        logs.append('peer-info-File ' + argumentList[1] + ' received successfully from ' + newadd)
        asyncio.run(main_client_udp('seed', argumentList[2].split(":"), argumentList[1], argumentList[3]))
         #print("inform UDP server in ip " + argumentList[2].split(":")[0] + " and " + argumentList[2].split(":")[1])
        logs.append(
            "peer-info-inform UDP server in ip " + argumentList[2].split(":")[0] + " and " + argumentList[2].split(":")[
                1])
        logs.append('peer-info-Peer ' + argumentList[3] + ' changed state to Seed')

        alive.start()

t.join()
