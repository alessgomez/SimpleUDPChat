import socket
import threading
import queue
import json

messages = queue.Queue()
clients = []

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind(('127.0.0.1', 12345))
print(f'Connected to server {server.getsockname()}!')

def receive():
    while True:
        try:
            message, address = server.recvfrom(1024)
            messages.put((message, address))
        except:
            pass

def broadcast():
    while True:
        while not messages.empty():
            message, address = messages.get()
            print(message.decode())

            bool = False
            for client in clients:
                if address in client:
                    bool = True
            
            if not bool:
                clients.append([address])
            
            try:
                jMessage = json.loads(message)
                
                match jMessage['command']:
                    case 'join':
                        try:
                            server.sendto(message, address)
                        except:
                            print('Join Command Server Error')
                    
                    case 'register':
                        try:
                            name = jMessage['handle']
                            exists = False
                            registered = False

                            for client in clients:
                                if name in client and client[0] != address:
                                    exists = True
                                elif client[0] == address and (name in client or len(client) == 2):
                                    registered = True

                            if not exists and not registered:
                                clients[clients.index([address])].append(name)
                                server.sendto(message, address)
                            elif exists and not registered:
                                server.sendto('{"command":"error", "message":"Registration failed. Handle or alias already exists."}'.encode(), address)
                            elif (exists and registered) or (not exists and registered):
                                server.sendto('{"command":"error", "message":"You have already registered."}'.encode(), address)
                        except:
                            print('Register Command Server Error')

                    case 'all':
                        try:
                            for client in clients:
                                if len(client) == 2:
                                    server.sendto(message, client[0])
                        except:
                            print('All Command Server Error')
                    
                    case 'msg':
                        try:
                            recipient = jMessage['handle']
                            msg = json.dumps(jMessage['message'])
                            recExists = False

                            for client in clients:
                                if recipient in client:
                                    recAdd = client[0]
                                    recExists = True
                                
                                if address in client:
                                    sender = client[1]
                            
                            if recExists:
                                server.sendto(('{"command":"msg", "handle":"From ' + sender + '", "message":' + msg + '}').encode(), recAdd)
                                server.sendto(('{"command":"msg", "handle":"To ' + recipient + '", "message":' + msg + '}').encode(), address)
                            else:
                                server.sendto('{"command":"error", "message":"Handle or alias not found."}'.encode(), address)
                        except:
                            print('Msg Command Server Error')

                    case 'leave':
                        try:
                            server.sendto(message, address)

                            toRemove = [address]

                            for client in clients:
                                if address in client:
                                    if len(client) == 2:
                                        toRemove.append(client[1])
                            
                            clients.remove(toRemove)
                        except:
                            print('Leave Command Server Error')

                    case 'error':
                        server.sendto(message, address)
            except:
                pass

t1 = threading.Thread(target = receive)
t2 = threading.Thread(target = broadcast)

t1.start()
t2.start()