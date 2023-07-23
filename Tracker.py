import sys
import time
import asyncio
import threading

filenames = []
sources = []
sizes = []
lastsignals = []
sources_list = []

logs = []


def dead(i):
    dead_address = sources_list[i]
    for ii in range(len(sources)):
        b = False
        for jj in range(len(sources[ii])):
            if dead_address == sources[ii][jj]:
                logs.append('peer-alive-info-Peer ' + dead_address + " poped from peers list.")
                sources[ii].pop(jj)

                if len(sources[ii]) == 0:
                    logs.append('file-' + filenames[ii] + '-info-Peer ' + dead_address + ' dead and file ' + filenames[
                        ii] + ' removed. (cant find another host)')
                    sources.pop(ii)
                    filenames.pop(ii)
                    sizes.pop(ii)

                b = True
                break
        if b:
            break
    sources_list.pop(i)
    lastsignals.pop(i)


def keep_alive():
    while (True):
        # print(sources)
        # print(filenames)
        # print('_________')
        time.sleep(10)
        for sig in range(len(lastsignals)):
            if time.time() - lastsignals[sig] > 15:
                logs.append('peer-alive-info-Unfortunately peer ' + sources_list[sig] + " dead.")
                dead(sig)
                break


alive = threading.Thread(target=keep_alive)
alive.start()


def submit(filename, source, size):
    if not filename in filenames:
        filenames.append(filename)
        sizes.append(size)
        sources.append([source])
        sources_list.append(source)
        lastsignals.append(time.time())
        logs.append('file-' + filename + '-info-File added with host ' + source)
        return 'File Added.'
    else:
        for i in range(len(filenames)):
            if filename == filenames[i]:
                if not source in sources[i]:
                    sources[i].append(source)
                    sources_list.append(source)
                    lastsignals.append(time.time())
                    logs.append('file-' + filename + '-info-File exists with host ' + source)
                    return 'File Exists. Server Added.'
                else:
                    logs.append('file-' + filename + '-info-File exists, host ' + source + ' exists.')
                    return 'Server Exists.'


import random


def get(filename):
    if filename in filenames:
        for i in range(len(filenames)):
            if filename == filenames[i]:
                outputsources = ''
                for q in sources[i]:
                    outputsources += (q + '-')
                logs.append('file-' + filename + '-info-Hosts ' + outputsources[:-1] + ' found for share this file.')
                return outputsources[:-1] + " " + sizes[i]

    else:
        logs.append('file-' + filename + '-info-Not found')
        return '404'


def al(source):
    if source in sources_list:
        for i in range(len(sources_list)):
            if source == sources_list[i]:
                lastsignals[i] = time.time()
                logs.append('peer-alive-info-Host ' + source + 'last signal updated')
                return 'done'
    else:
        logs.append('peer-alive-info-Cant find host ' + source + 'for update last signal')
        return '405'


class EchoServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        status, filename, source, size = data.decode().split(' ')
        output = '404'
        if status == 'seed':
            logs.append(
                'peer-seed-info-peer ' + source + ' received file: ' + filename + ' , size: ' + size + ' successfuly')
            logs.append(
                'peer-submit-info-A peer with address ' + source + ' submitted: ' + filename + ' , size: ' + size)
            logs.append('file-' + filename + '-info-File submitted: ' + filename + ' , size: ' + size)
            output = submit(filename, source, size)
        elif status == 'submit':
            logs.append(
                'peer-submit-info-A peer with address ' + source + ' submitted: ' + filename + ' , size: ' + size)
            logs.append('file-' + filename + '-info-File submitted: ' + filename + ' , size: ' + size)
            output = submit(filename, source, size)
        elif status == 'check':
            logs.append('peer-check-info-A peer with address ' + source + ' request ' + filename)
            output = get(filename)
        elif status == 'alive':
            logs.append('peer-alive-info-A signal received form ' + source + " , it's still alive")
            output = al(source)

        # print('Received %r from %s' % (data.decode(), addr))
        # print('Send %r to %s' % (output, addr))
        self.transport.sendto(output.encode(), addr)


async def main_server(address):
    # print("tracker-info-Starting UDP server in ip " + address[0] + " and " + address[1])

    loop = asyncio.get_running_loop()

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoServerProtocol(),
        local_addr=(address[0], int(address[1])))

    try:
        await asyncio.sleep(3600)
    finally:
        transport.close()


def get_query():
    while (True):
        q = str(input('Input your query: '))
        if q == 'request logs':
            for log in logs:
                print(log)
        elif q == 'file_logs':
            q = str(input('Input file name: '))
            for log in logs:
                if log.split('-')[0] == 'file':
                    if q == 'all':
                        print(log)
                    else:
                        if log.split('-')[1] == q:
                            print(log)


add = sys.argv[1].split(":")
query = threading.Thread(target=get_query)
query.start()
asyncio.run(main_server(add))
