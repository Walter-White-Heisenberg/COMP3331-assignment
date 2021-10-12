import sys
from socket import *
from _thread import *
import threading
import os
import time


#alive stands for the status of the forum
alive = True

#downloading or not
downloading = False

#the shutdown password
ST_pass = str()

#prepareration (gets the information of users' account info)
file = open("credentials.txt","r")
name_pass = {}
lineOfAcc = file.readline()
while lineOfAcc:
    tmp = lineOfAcc.split()
    name_pass[tmp[0]] = tmp[1]
    lineOfAcc = file.readline()
file.close()

#to record who's online
#"credentials.txt"
all_fname = []
online = []
cmd = ["CRT","MSG","DLT", "EDT", "LST", "RDT", "UPD", "DWN", "RMV","XIT", "SHT"]
#thread name : number ofcreated message (don't care if any message deleted cause we have message id)
thread = {}


#write a content with certain mode in a known file
def write_files(fname, content, mode):
    file = open(fname, mode)
    file.write(content)
    file.close()

#return if a string can be convert to integer
def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def change_line(fname, line_num, newmess):
    with open(fname, "r") as f:
        lines = f.readlines()
    with open(fname, "w") as f1:
        f1.write(lines[0])
        for line in lines[1:]:
            words = line.split()
            if (RepresentsInt(words[0]) and line_num != words[0]) or (RepresentsInt(words[0]) == False and " uploaded file " in line):
                f1.write(line)
            else:
                f1.write(newmess)
    f.close()

def find_message(fname, line_num):
    file = open(fname, "r")
    num = 0
    line = file.readline()
    while line:
        tmp = line.split()
        line = file.readline()
        words = line.split()
        if len(words) >0 and RepresentsInt(words[0]) and line_num == words[0]:
            file.close()
            return words[1:]
    file.close()
    return None

def recieve_file(c, filesize, filename):
    file = open(filename, "wb")
    while filesize > 0:
        file.write(c.recv(1024))
        filesize = filesize - 1024
    file.close()

def print_and_send(c,message):
    print(message)
    c.send(bytes(message, encoding = "utf8"))
    time.sleep(0.03)

def threaded(c, ST_pass): 
    global alive
    i = 0
    username = str()
    password = str()
    message = str()
    while alive:  
        reply = c.recv(1024)
        reply = str(reply.decode('utf8'))
        if i == 0:
            if reply in online:
                message = reply + " already logged in"
            elif reply in name_pass:
                message = "Client connected"
                i = 1
            else :
                message = "Client created"
                i = 2
            username = reply
            print_and_send(c,message)
        elif i == 1:
            if reply == name_pass[username]:    
                message = "login successfully"
                online.append(username)
                i = 3
            else:
                message = "wrong password"
            print_and_send(c,message)
        elif i == 2:
            name_pass[username] = reply
            write_files("credentials.txt", "\n" + username + " " + reply, "a+")
            message = "registration successful"
            online.append(username)
            i = 3
            print_and_send(c,message)
        else:
            command = reply.split()
            if len(command) == 0:
                continue
            elif command[0] in cmd:
                print(username + " issued " + command[0] + " command")
            message = ""
            if command[0] == "CRT":
                if len(command) != 2:
                    message = "wrong number of arguments"
                elif command[1] in thread:
                    print("Thread " + command[1] + " already exists")
                    message = "Thread already exists"
                else:
                    write_files(command[1], username + "\n","w")
                    thread[command[1]] = 0
                    all_fname.append(command[1])
                    print("Thread " + command[1] + " created")
                    message = "Thread created successfully"
                c.send(bytes(message, encoding = "utf8"))
            elif command[0] == "MSG":
                if len(command) < 3:
                    message = "wrong number of arguments"
                elif command[1] in thread:
                    thread[command[1]] = thread[command[1]] + 1
                    write_files(command[1], str(thread[command[1]]) + " " + username + ": " + " ".join(command[2:]) + "\n" , "a+")
                    message = "Message posted to " + command[1] + " successfully"
                else:
                    message = "Thread doesn't exist"
                print_and_send(c,message)
            elif command[0] == "DLT" or command[0] == "EDT":
                if (command[0] == "DLT" and len(command) != 3) or (command[0] == "EDT" and len(command) < 4):
                    message = "wrong number of arguments"
                else:
                    verb = "edit"
                    past_v = "edited"
                    if command[0] == "DLT":
                        verb = "delete"
                        past_v = "deleted"
                    if command[1] not in thread:
                        message = "Thread " + command[1] + " doesn't exist"
                    else:
                        del_mess = find_message(command[1], command[2])
                        if del_mess is None:
                            message = "Can't find the message with id " + command[2]
                        else:
                            poster = del_mess[0]
                            if username + ":" != poster:
                                message = "Only the original poster can " + verb +" his message"
                            else:
                                if command[0] == "DLT":
                                    change_line(command[1], command[2], "")
                                else:
                                    new_mess = str(command[2]) + " " + username + ": " + " ".join(command[3:]) + "\n"
                                    change_line(command[1], command[2], new_mess)
                                message = "the message with id " + str(command[2]) + " has been " + past_v
                print_and_send(c,message)
            elif command[0] == "LST":
                if len(command) == 1:
                    if len(thread) != 0:
                        message = "The list of active threads:\n"
                        for t in thread:
                            message = "   " + message + t + "\n"
                        print("list of thread already sent to client " + username)
                    else:
                        message = "No active threads yet"
                        print(message)
                else:
                    message = "wrong number of arguments"
                    print(message)
                c.send(bytes(message, encoding = "utf8"))
            elif command[0] == "RDT":
                if len(command) == 2:
                    if command[1] in thread:
                        with open(command[1], "r") as f:
                            lines = f.readlines()
                        if len(lines) < 2:
                            message = "No message or file in the thread yet"
                        else:
                            message = "\n"
                            for line in lines[1:]:
                                message = message + line
                            print("Content from " + command[1] + " delivered to " + username + " successfully")
                        f.close()
                    else:
                        print("Thread doesn't exist")
                        message = "Thread doesn't exist"
                else:
                    message = "wrong number of arguments"
                    print(message)
                c.send(bytes(message, encoding = "utf8"))
            elif command[0] == "RMV":
                if len(command) != 2:
                    message = "wrong number of arguments"
                elif command[1] not in thread:
                        message = "Thread doesn't exist"
                else:
                    creater = open(command[1], "r").readline()
                    if username not in creater:
                        message = "Only the creater of thread can remove it"
                    else :
                        thread.pop(command[1], None)
                        os.remove(command[1])
                        for fname in all_fname:
                            if command[1] + "-" in fname:
                                if os.path.exists(fname):
                                    os.remove(fname)
                                all_fname.remove(fname)
                        message = "Thread removed successfully"
                print_and_send(c,message)
            #in UPD, the length of command is already verified in client side
            elif command[0] == "UPD":
                if command[1] not in thread:
                    c.send(bytes("!No", encoding = "utf8"))
                    time.sleep(0.03)
                else:
                    c.send(bytes("!Yes", encoding = "utf8"))
                    time.sleep(0.03)
                    size_or_fail = c.recv(1024)
                    size_or_fail = str(size_or_fail.decode('utf8'))
                    print(size_or_fail)
                    if size_or_fail[0] in "!":
                        print("\n\nFile size in bytes: ", size_or_fail[1:])
                        filename = command[1] + "-" + command[2]
                        recieve_file(c, int(size_or_fail[1:]), filename)
                        all_fname.append(filename)
                        write_files(command[1], username + " uploaded file " + command[2] + " to " + command[1] + "\n" , "a+")
                        c.send(bytes(command[2] + " uploaded successfully", encoding = "utf8"))
                    else:
                        print_and_send(c,"failed to recieved")
                        continue
            elif command[0] == "DWN":
                if command[1] not in thread:
                    c.send(bytes("!No, can't find corresponding thread", encoding = "utf8"))
                    time.sleep(0.03)
                elif os.path.exists(command[1] + "-" + command[2]) == False:
                    c.send(bytes("!No, can't find corresponding file in the thread", encoding = "utf8"))
                    time.sleep(0.03)
                else:
                    filesize = os.stat(command[1] + "-" + command[2]).st_size
                    c.send(bytes(str(filesize), encoding = "utf8"))
                    time.sleep(0.03)
                    with open(command[1] + "-" + command[2], 'rb') as f:
                        sent = 0
                        while sent <= filesize:
                            data = f.read(1024)
                            c.sendall(data)
                            # wait for server to receive data
                            time.sleep(0.01)
                            sent += len(data)
                    print("the file sent successfully")
            elif command[0] == "XIT":
                if len(command) != 1:
                    message = "wrong number of arguments"
                else:
                    message = "see u " + username
                    online.remove(username)
                c.send(bytes(message, encoding = "utf8"))
                break
            elif command[0] == "SHT":
                if len(command) != 2:
                    message = "wrong number of arguments"
                elif command[1] != ST_pass:
                    message = "The shut-down password is wrong "
                else :
                    alive = False
                    message = "GB"
                print_and_send(c,message)
            else:
                c.send(bytes("Invalid command", encoding = "utf8"))
        print("\n\n")
    #close the connectionSocket. Note that the serverSocket is still alive waiting for new clients to connect, we are only closing the connectionSocket.
    c.close()



def excute(port, password):
    global alive 
    #Define connection (socket) parameters
    #Address + Port no
    #Server would be running on the same host as Client
    # change this port number if required
    serverSocket = socket(AF_INET, SOCK_STREAM)
    #This line creates the server’s socket. The first parameter indicates the address family; in particular,AF_INET indicates that the underlying network is using IPv4.The second parameter indicates that the socket is of type SOCK_STREAM,which means it is a TCP socket (rather than a UDP socket, where we use SOCK_DGRAM).

    serverSocket.bind(('127.0.0.1', port))
    #The above line binds (that is, assigns) the port number 12000 to the server’s socket. In this manner, when anyone sends a packet to port 12000 at the IP address of the server (localhost in this case), that packet will be directed to this socket.

    print("waiting for connection")

    serverSocket.listen(10)
    #The serverSocket then goes in the listen state to listen for at mostclient connection requests. 
    clients = []
    while alive:


        # When a client knocks on this door, the program invokes the accept( ) method for serverSocket, 
        # which creates a new socket in the server, called connectionSocket, dedicated to this particular client. 
        # The client and server then complete the handshaking, creating a TCP connection between the client’s clientSocket and the server’s connectionSocket. 
        # With the TCP connection established, the client and server can now send bytes to each other over the connection. With TCP, 
        # all bytes sent from one side not are not only guaranteed to arrive at the other side but also guaranteed to arrive in order
        try:
            connectionSocket, addr = serverSocket.accept()
            clients.append(connectionSocket)

            # Start a new thread and return its identifier 
            start_new_thread(threaded, (connectionSocket,password))
        except:

            break
    
    for cl in clients:
        try:
            cl.send(bytes("GB", encoding = "utf8"))
        except OSError:
            continue

    for file in all_fname:
        if(os.path.exists(file)):
            os.remove(file)

    print("Server shutting down")
    serverSocket.close()


if __name__ == "__main__":  
    if len(sys.argv) != 3:
        print("please type arguments as server_port and admin_password")
    else :
        excute(int(sys.argv[1]), sys.argv[2])