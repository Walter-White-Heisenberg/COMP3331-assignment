import sys
from socket import *
import os
import time
from _thread import *
import threading

ip = str()
port = int()

class ClientHandle():
    def __init__(self, clientSocket, username):
        self.clientSocket = clientSocket
        self.recvData = None
        self.ifPrint = False
        self.username = username


    # a thread is opened for this function
    # which will keep calling this function to recv data from the server
    def recv(self):
        global port
        global ip
        if self.ifPrint: return
        self.recvData = self.clientSocket.recv(1024).decode('utf-8')
        reply = self.recvData
        # change recvdata to stop the loop
        if reply == 'GB':
            print("\nGoodbye. Server shutting down\n")
            self.recvData = 'Goodbye'
            self.clientSocket.close()
            return
        elif reply == "see u " + self.username:
            print("Good bye!\n\n\n")
            self.recvData = 'Goodbye'
        elif reply[0] == '!':
            return
        else:
            print(reply)
#keep recieving the data if the client is logging in while forum is not shutdown yet
def recv_until_close(cSocket, handler):
    while handler.recvData != 'Goodbye':
        try:
            handler.recv()
        except Exception:
            break

#same function in server, very handy
def recieve_file(c, filesize, filename):
    file = open(filename, "wb")
    while filesize > 0:
        file.write(c.recv(1024))
        filesize = filesize - 1024
    file.close()

#help user loggin in but not precessing any command
def joinForum(handler):
    handler.username = input('Enter username:')
    handler.clientSocket.send(bytes(handler.username, encoding = "utf8"))
    i = 1 
    try:
        while i and handler.recvData != 'Goodbye':
            #We wait to receive the message from the server, store it in reply
            reply = handler.clientSocket.recv(1024)
            reply = str(reply.decode('utf8'))
            print("From Server: ", reply)
            #We wait to receive the reply from the server, store it in reply
            if reply == handler.username + " already logged in":
                handler.username = input('Enter username:')

                handler.clientSocket.send(bytes(handler.username, encoding = "utf8"))
            elif reply == "wrong password" or reply == "Client created" or reply == "Client connected":
                if reply == "Client created":
                    mess = 'Enter the new password:'
                else:
                    mess = 'Enter pasword:'
                print(reply)
                password = input(mess)
                handler.clientSocket.send(bytes(password, encoding = "utf8"))
            else:
                i = 0
        print('Welcome to the forum')
        #to deal with the possibility that server close down while user is logging in
    except ConnectionAbortedError:
        print("\nGoodbye. Server shutting down\n")
        handler.recvData = 'Goodbye'
        pass


#process the serval complex command (UDP, DWL) with the given handler, and send the usual command to server
def commander(handler):
    i = 1
    while handler.recvData != 'Goodbye':
        print("\n\n")
        command = input('Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT, SHT:')
        if len(command) == 0:
            print("type something")
            continue
        cmd = command.split()
        handler.clientSocket.send(bytes(command, encoding = "utf8"))
        time.sleep(0.03)
        if cmd[0] == 'UPD':
            if(len(cmd) != 3):
                print("Wrong number of arguments")
            elif os.path.exists(cmd[2]) == False:
                print("Can't find file with path/name as " + cmd[1])
            else:
                if handler.recvData == "!No":
                    print("input thread is invalid")
                    continue
                filesize = os.stat(cmd[2]).st_size
                handler.clientSocket.send(bytes("!" + str(filesize), encoding = "utf8"))
                print("Sending the size of file before sending the file")
                time.sleep(0.03)

                # start send file's data
                with open(cmd[2], 'rb') as f:
                    sent = 0
                    while sent != filesize:
                        data = f.read(1024)
                        handler.clientSocket.sendall(data)
                        # wait for server to receive data
                        time.sleep(0.01)
                        sent += len(data)
                print("the file sent successfully")
        elif cmd[0] == 'DWN':
            if(len(cmd) != 3):
                print("Wrong number of arguments")
            else:
                if "!No" in handler.recvData:
                    print(handler.recvData[4:])
                    continue
                else:
                    size_or_fail = handler.recvData
                    handler.ifPrint = True
                    print("Start reciving the file")
                    recieve_file(handler.clientSocket, int(size_or_fail), cmd[2])
                    print(command[2] + " downloaded successfully")
                    handler.ifPrint = False


def start(ip, port):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    #This line creates the client’s socket. The first parameter indicates the address family; in particular,AF_INET indicates that the underlying network is using IPv4. The second parameter indicates that the socket is of type SOCK_STREAM,which means it is a TCP socket (rather than a UDP socket, where we use SOCK_DGRAM). 
    clientSocket.connect((ip,port))
    #Before the client can send data to the server (or vice versa) using a TCP socket, a TCP connection must first be established between the client and server. The above line initiates the TCP connection between the client and server. The parameter of the connect( ) method is the address of the server side of the connection. After this line of code is executed, the three-way handshake is performed and a TCP connection is established between the client and server.
    
    handler = ClientHandle(clientSocket,"")
    joinForum(handler)
    # create thread for reciving cmds
    start_new_thread(recv_until_close, (clientSocket, handler,))
    # create thread for processing cmds
    start_new_thread(commander, (handler,))

    while handler.recvData != 'Goodbye':
        continue
        
    handler.clientSocket.close()
    # Close the socket
    try:
        #connect to the server to run the main loop again so that the shutdown process can be run properly
        clientSocket = socket(AF_INET, SOCK_STREAM)
        #This line creates the client’s socket. The first parameter indicates the address family; in particular,AF_INET indicates that the underlying network is using IPv4. The second parameter indicates that the socket is of type SOCK_STREAM,which means it is a TCP socket (rather than a UDP socket, where we use SOCK_DGRAM). 
        clientSocket.connect((ip,port))
        clientSocket.close()
    except :
        pass





if __name__ == "__main__":  
    if len(sys.argv) != 3:
        print("please type arguments as server_IP and server_port")
    else :
        ip = sys.argv[1]
        port = int(sys.argv[2])
        start(ip, port)