import socket
import threading
import json
import random
import tkinter
import tkinter.scrolledtext

class Client:
    def __init__(self):
        self.gui_done = False
        self.username = ""
        self.tempname = ""
        self.server = ('127.0.0.1', 12345)
        self.joined = False

        gui_thread = threading.Thread(target = self.gui_loop)
        receive_thread = threading.Thread(target = self.receive)

        gui_thread.start()
        receive_thread.start()
    
    def gui_loop(self):
        self.win = tkinter.Tk()
        self.win.title('Message Board')
        self.win.config(bg = 'lightgray')

        self.chat_label = tkinter.Label(self.win, text = 'WELCOME TO THE MESSAGE BOARD!', bg = 'lightgray')
        self.chat_label.config(font = ('Book Antiqua', 12, 'bold'))
        self.chat_label.pack(padx = 20, pady = 5)

        self.text_area = tkinter.scrolledtext.ScrolledText(self.win)
        self.text_area.pack(padx = 20, pady = 5)
        self.text_area.config(state = 'disabled', background = 'beige', font = ('Courier New', 10, 'bold'))

        self.msg_label = tkinter.Label(self.win, text = 'Message:', bg = 'lightgray')
        self.msg_label.config(font = ('Book Antiqua', 12, 'bold', 'italic'))
        self.msg_label.pack(padx = 20, pady = 5)

        self.input_area = tkinter.Text(self.win, height = 3)
        self.input_area.pack(padx = 20, pady = 5)

        self.send_button = tkinter.Button(self.win, text = 'Send', command = self.write)
        self.send_button.config(font = ('Helvetica', 11))
        self.send_button.pack(padx = 20, pady = 5)

        self.gui_done = True
        
        self.win.protocol('WM_DELETE_WINDOW', self.stop)

        self.win.mainloop()

    def write(self):
        messageSegments = self.input_area.get('1.0', 'end').split()

        match messageSegments[0]:
            case '/?':
                spiel = 'Here is the list of commands you can use, as well as their syntax:\n' \
                        + '/join <server_ip_add> <port> - Connects you to the server application\n' \
                        + '/leave - Disconnects you from the server application you are currently joined to\n' \
                        + '/register <handle> - Registers your unique handle or alias in the application\n' \
                        + '/all <message> - Broadcasts your message to all connected users\n' \
                        + '/msg <handle> <message> - Sends a direct message to a single user'

                self.displayClientMsg(spiel)

            case '/join':
                if not self.joined:
                    try:
                        paramsCorrect = len(messageSegments) == 3

                        if paramsCorrect and (messageSegments[1], int(messageSegments[2])) == self.server:
                            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            self.sock.bind((messageSegments[1], random.randint(8000, 9000)))
                            self.sock.sendto('{"command":"join"}'.encode(), self.server)
                            self.joined = True
                        elif not paramsCorrect:
                            self.displayClientMsg('ERROR: Command parameters do not match or is not allowed.')
                        elif paramsCorrect and (messageSegments[1], int(messageSegments[2])) != self.server:
                            self.displayClientMsg('ERROR: Connection to the Message Board Server has failed! Please check IP Address and Port Number.')
                    except:
                        self.displayClientMsg('ERROR: Connection to the Message Board Server has failed! Please check IP Address and Port Number.')
                else:
                    self.displayClientMsg('ERROR: You have already joined the Message Board Server.')
            
            case '/register':
                try:
                    paramsCorrect = len(messageSegments) == 2

                    if paramsCorrect:
                        self.tempname = messageSegments[1]
                        self.sock.sendto(('{"command":"register", "handle":"' + self.tempname + '"}').encode(), self.server)
                    else:
                        self.sock.sendto('{"command":"error", "message":"Command parameters do not match or is not allowed."}'.encode(), self.server)
                except:
                    self.displayClientMsg('ERROR: Command failed. Please connect to the server first.')

            case '/all':
                try:
                    paramsCorrect = len(messageSegments) >= 2 
                    
                    for idx, segment in enumerate(messageSegments[1:]):
                        if '"' in segment:
                            messageSegments[idx + 1] = segment.replace('"', '\\"')

                    if paramsCorrect and self.username != "":
                        msg = f'{self.username}: ' + ' '.join(messageSegments[1:])
                        self.sock.sendto(('{"command":"all", "message":"' + msg + '"}').encode(), self.server)
                    elif not paramsCorrect:
                        self.sock.sendto('{"command":"error", "message":"Command parameters do not match or is not allowed."}'.encode(), self.server)
                    elif self.username == "":
                        self.sock.sendto('{"command":"error", "message":"Please register a handle first."}'.encode(), self.server)
                except:
                    self.displayClientMsg('ERROR: Command failed. Please connect to the server first.')
            
            case '/msg':
                try:
                    paramsCorrect = len(messageSegments) >= 3

                    for idx, segment in enumerate(messageSegments[2:]):
                        if '"' in segment:
                            messageSegments[idx + 2] = segment.replace('"', '\\"')

                    if paramsCorrect and self.username != "":
                        recipient = messageSegments[1]
                        msg = ' '.join(messageSegments[2:])
                        self.sock.sendto(('{"command":"msg", "handle":"' + recipient + '", "message":"' + msg + '"}').encode(), self.server)
                    elif not paramsCorrect:
                        self.sock.sendto('{"command":"error", "message":"Command parameters do not match or is not allowed."}'.encode(), self.server)
                    elif self.username == "":
                        self.sock.sendto('{"command":"error", "message":"Please register a handle first."}'.encode(), self.server)
                except:
                    self.displayClientMsg('ERROR: Command failed. Please connect to the server first.')
            
            case '/leave':
                try:
                    paramsCorrect = len(messageSegments) == 1

                    if paramsCorrect:
                        self.sock.sendto('{"command":"leave"}'.encode(), self.server)
                    else:
                        self.sock.sendto('{"command":"error", "message":"Command parameters do not match or is not allowed."}'.encode(), self.server)
                except:
                    self.displayClientMsg('ERROR: Disconnection failed. Please connect to the server first.')

            case _:
                self.displayClientMsg('ERROR: Command not found.')
        
        self.input_area.delete('1.0', 'end')

    def stop(self):
        if self.joined:
            self.sock.close()
            self.joined = False
        self.win.destroy()
        exit()

    def receive(self):
        while True:
            try:
                message, _ = self.sock.recvfrom(1024)
                
                jMessage = json.loads(message)

                match jMessage['command']:
                    case 'join':
                        self.displayClientMsg('Connection to the Message Board Server is successful!')

                    case 'register':
                        self.username = jMessage['handle']
                        self.displayClientMsg(f'Welcome, {jMessage["handle"]}!')

                    case 'all':
                        self.displayClientMsg(jMessage['message'])

                    case 'msg':
                        self.displayClientMsg(f'[{jMessage["handle"]}]: {jMessage["message"]}')

                    case 'leave':
                        self.displayClientMsg('Connection closed. Thank you!')
                        self.joined = False
                        self.sock.close()

                    case 'error':
                        self.displayClientMsg(f'ERROR: {jMessage["message"]}')
            except:
                pass

    def displayClientMsg(self, message):
        if self.gui_done:
            self.text_area.config(state = 'normal')
            self.text_area.insert('end', message + '\n\n')
            self.text_area.yview('end')
            self.text_area.config(state = 'disabled')
client = Client()