import socket
import threading
import time

activeConnections=[]                            #List of all clients connected to the server

def group_chat(conn, addr, name):
    print(addr)
    ip, port = addr
    
    while True:
        msg = conn.recv(2048).decode()
        print(f"{ip}: {msg}")

        if(msg == 'disconnect_request'):
            break

        if msg == 'sending_img':
            temp = conn.recv(2048).decode('utf-8', 'ignore')
            print('temp: ', temp)
            extension, size, sender_name = temp.split('\n')
            print('extension: ', extension)
            print('size: ', size)
            print('sender_name: ', sender_name)
            file = open(f"test{extension}",'wb')
            fileBytes = b""
            done = False

            while not done:
                data = conn.recv(2048)
                fileBytes += data
                print((len(fileBytes)/int(size))*100,' percent completed')

                if fileBytes[-5:] == b"<END>":
                    done = True

            file.write(fileBytes)
            file.close()

            for _, c, user_mode in activeConnections:
                if c == conn or user_mode != 'GROUP':
                    continue
                if extension in ['.mp4','.mkv','.txt','.pdf','.docx','.mp3','.csv','.ppt','.xlsx']:
                    c.send('sending_vid'.encode())
                else:
                    c.send('sending_img'.encode())
                c.send(temp.encode())
                time.sleep(1)
                c.sendall(fileBytes)
            continue

        for _, c, user_mode in activeConnections:
            if c == conn or user_mode != 'GROUP':
                continue

            c.send(msg.encode())

    try:
        activeConnections.remove((name,conn,'GROUP'))          #Remove client from List
    except Exception as e:
        print(e)

    conn.close()                            #Close Connection
    return

def private_chat(conn, addr, name, c):
    print(addr)
    ip, port = addr

    while True:
        msg = conn.recv(2048).decode()
        print(f"{ip}: {msg}")
        if(msg == 'disconnect_request'):
            break
        if msg == 'sending_img':
            temp = conn.recv(2048).decode('utf-8', 'ignore')
            print('temp: ', temp)
            extension, size, sender_name = temp.split('\n')
            print('extension: ', extension)
            file = open(f"test{extension}",'wb')
            fileBytes = b""
            done = False

            while not done:
                data = conn.recv(2048)
                fileBytes += data
                print((len(fileBytes)/int(size))*100,' percent completed')
                if fileBytes[-5:] == b"<END>":
                    done = True
            file.write(fileBytes)
            file.close()

            if extension in ['.mp4','.mkv','.txt','.pdf','.docx','.mp3','.csv','.ppt','.xlsx']:
                c.send('sending_vid'.encode())
            else:
                c.send('sending_img'.encode())
            c.send(temp.encode())
            c.sendall(fileBytes)
            continue
        c.send(msg.encode())

    try:
        activeConnections.remove((name,conn,'PRIVATE'))          #Remove client from List
    except Exception as e:
        print(e)

    conn.close()                            #Close Connection
    return

def initizalize(conn):
    msg = conn.recv(2048).decode()
    print(msg)
    _, name = msg.split('\n')
    found = False

    for user_name, _, _ in activeConnections:
        if name == user_name:
            found = True
            break

    if found:
        conn.send("RENAME".encode())
        print("Name already Exists")
        return (False,name,'')
    else:
        temp = ''
        for user_name, _, mode in activeConnections:
            if mode == 'PRIVATE':
                temp += f"{user_name}\n"
        if temp == '':
            temp = "no_user_online"
        conn.send(temp.encode())
        mode = conn.recv(2048).decode()
        print(mode)
        activeConnections.append((name, conn, mode))
        return (True, name, mode)

def start(conn,addr):
    flag, name, mode = initizalize(conn)
    if flag:
        if mode == 'GROUP':
            print("starting guest")
            thread = threading.Thread(target = group_chat, args = (conn, addr, name))
            thread.start()
        else:
            msg = conn.recv(1024).decode()
            req, u = msg.split('\n')
            private_conn = ''
            for user_name, c, _ in activeConnections:
                if u == user_name:
                    private_conn = c
                    break

            if req == 'REQUEST':
                private_conn.send(name.encode())
            private_thread = threading.Thread(target = private_chat, args = (conn,addr,name,private_conn))
            private_thread.start()
    return

ip = socket.gethostbyname(socket.gethostname())
port = 9999
print("IP: " + str(ip))

server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server.settimeout(1)                                    #To make server timeout after every 1 second to enable non blocking communication
server.bind((ip, port))
server.listen()
print("server started on port " + str(port) + "...")

while True:
    try:
        conn, addr = server.accept()
        thread = threading.Thread(target = start, args = (conn, addr))
        thread.start()
    except socket.timeout:
        continue
    except KeyboardInterrupt:                             #Check for keyboard interrupts else continue listening
        break

server.close()