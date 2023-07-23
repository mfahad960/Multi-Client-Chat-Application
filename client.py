import socket
import threading
import math
import os
from datetime import datetime
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd, messagebox
from PIL import ImageTk, Image
from datetime import datetime

images = []
time_now = datetime.now()
u_time = time_now.strftime("%H:%M")

#send messages to server
def send_msg(msg, count):
    try:
        if(len(msg) != 0):
            formatted_msg = f"{datetime.now().strftime('%H:%M')}\n\t{name.get()}\n\t{msg}"
            client.send(formatted_msg.encode())
            user_time, user_name, user_data = formatted_msg.split('\n\t')

            if chat_box != None:
                chat_box.config(state = NORMAL)
                chat_box.insert(END, " " * 45)
                chat_box.insert(END, f"{user_time}\n")
                chat_box.insert(END, " " * 45)
                chat_box.insert(END, f"Me: {user_data}\n\n")
                chat_box.config(state = DISABLED)

            count[0] += 1
            msgInput.delete(0, END)                                  #Clear the message input entry bar
    except Exception as ex:
        print(ex)
        connectionStatus.set("Disconnected")                         #Server and client are disconnected
    return

#Receive messages from server
def recv_msg(addr, count):
    print(addr)
    typing_msg = StringVar()

    while True:
        msg = client.recv(4096).decode('utf-8', 'ignore')

        #If Server Disconnects
        if not msg:
            break
        
        #show typing status
        if msg[-6:] == "TYPING":
            typing_msg.set(msg)
            if chat_box != None:
                chat_box.config(state = NORMAL)
                chat_box.insert(END, f"{typing_msg.get()}\n")
                chat_box.config(state = DISABLED)
            continue
        
        if msg == 'sending_vid':
            temp = client.recv(1024).decode()
            extension, size, sender_name = temp.split('\n')
            file = open(f"{name.get()}{count[0]+1}{extension}", 'wb')
            fileBytes = b""
            done = False
            percent = StringVar()

            #chat_box.config(state = NORMAL)
            #chat_box.insert(END, f"{sender_name}: \n\n")
            #chat_box.insert(END, percent.get())

            while not done:
                data = client.recv(4096)
                fileBytes += data
                current_percent = math.floor((len(fileBytes)/int(size))*100)
                print(current_percent, ' percent completed')
                percent.set(f"{current_percent} % Downloaded")
                if fileBytes[-5:] == b"<END>":
                    done = True

            file.write(fileBytes)
            filename = file.name
            file.close()

            if extension in ['.mp4','.mkv']:
                text = f'{sender_name} sent a video'
                count[0] += 1
            elif extension in ['.txt','.pdf','.docx','.csv','.ppt','.xlsx']:
                text = f'{sender_name} sent a document'
                count[0] += 1
            elif extension in ['.mp3']:
                text = f'{sender_name} sent an audio'
                count[0] += 1
            else: 
                messagebox.showerror("Error", "File type not supported!")

            chat_box.config(state = NORMAL)
            chat_box.insert(END, f'{u_time}:\n')
            chat_box.insert(END, f'{text}\n', 'link')
            chat_box.tag_config("link", foreground="blue", underline=True)
            chat_box.tag_bind("link", "<Button-1>", lambda e : open_link_file(filename))
            chat_box.config(state = DISABLED)
            continue

        if msg == 'sending_img':
            temp = client.recv(1024).decode()
            print(temp)
            extension, size, sender_name = temp.split('\n')
            file = open(f"{name.get()}{count[0]+1}{extension}",'wb')
            fileBytes = b""
            done = False
            
            while not done:
                data = client.recv(4096)
                fileBytes += data
                if fileBytes[-5:] == b"<END>":
                    done = True

            file.write(fileBytes)
            filename = file.name
            file.close()

            chat_box.config(state = NORMAL)
            chat_box.insert(END, f'{u_time}:\n')
            chat_box.insert(END, f"{sender_name}: \n\n")
            chat_box.config(state = DISABLED)

            image = Image.open(filename)
            desired_width, desired_height = image_res(image)
            # Resize the image
            resized_image = image.resize((desired_width, desired_height), Image.LANCZOS)
            images.append(ImageTk.PhotoImage(resized_image))
            chat_box.image_create(END, image = images[-1])
            chat_box.image = images[-1]
            count[0] += 1
            count[0] += 1
            continue

        if msg != 'sending_img' and msg != 'sending_vid':
            if(len(msg.split('\n\t')) > 1):
                user_time, user_name, user_data = msg.split('\n\t')
                if chat_box != None:
                    chat_box.config(state = NORMAL)
                    chat_box.insert(END, f"{user_time}\n{user_name}: {user_data}\n\n")
                    chat_box.config(state = DISABLED)

        count[0] += 1
        if(msg == 'disconnect_request'):                #Server Disconnects
            break

    client.close()
    return

ip = socket.gethostbyname(socket.gethostname())
port = 9999
addr = (ip, port)

def main():
    ip = socket.gethostbyname(socket.gethostname())
    port = 9999
    print("IP: " + str(ip))
    print("Port: " + str(port))
    addr = (ip, port)
    global client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(addr)
        client.send(f'NAME\n{name.get()}'.encode())
        msg=client.recv(1024).decode()
        print('msg on 79', msg)
        if msg == 'RENAME':
            disconnect()
            messagebox.showerror("Error", "Username already exists, use a different username or try again later.")
            return
        else:
            root.title(f"Multi-User Chat Application - {name.get()}")
            if pvt_btn != None:
                pvt_btn.config(state = NORMAL)
            if msg == 'no_user_online':
                message.set("No User Currently Online!")
                #Label(main_frame, text = "No User Currently Online!").grid(row = 2, column = 0)
                return
            active_users = msg.split('\n')
            active_users.pop()
            message.set("Users Online:")
            i = 3
            for user in active_users:
                Label(main_frame, text = str(user), font=("Arial", 10)).grid(row = i, column = 0)
                ttk.Button(main_frame, text = "Private Chat", command = lambda:chat_window(addr, user)).grid(row = i, column = 1)
                i += 1
    except Exception as e:
        print(e)
        connectionStatus.set("No Port open on the specified Ip Address and Port")
    return

def listening(addr):
    client.send(b"PRIVATE")
    notification_thread = threading.Thread(target = request, args = (addr,))
    notification_thread.start()

def start():
    mainThread = threading.Thread(target = main, args = ())       #New Thread to deal with client-Server communication
    mainThread.start()
    return

def open_link_file(filename):
    os.startfile(filename)
    return

def request(addr):
    msg = client.recv(4096).decode()
    Label(main_frame, text = f"{msg} wants to private chat: ", font=("Arial", 10)).grid(row = 5, column = 0)
    ttk.Button(main_frame, text = "Accept", command = lambda: chat_window(addr, msg, "ACCEPT")).grid(column = 1, row = 5)
    return

def disconnect():
    try:
        client.send("disconnect_request".encode())
        connectionStatus.set("Disconnected")
    except:
        pass
    return

def image_res(image):
    #calculate aspect ratio
    text_width = chat_box.winfo_width()-25
    text_height = chat_box.winfo_height()-25
    image_width, image_height = image.size
    aspect_ratio = min(text_width / image_width, text_height / image_height)
    desired_width = int(image_width * aspect_ratio)
    desired_height = int(image_height * aspect_ratio)

    return desired_width, desired_height

def browse_files(msg, count):
    file = fd.askopenfile(mode='rb')
    formatted_msg = f"{datetime.now().strftime('%H:%M')}\n\t{name.get()}\n\t{msg}"
    user_time, user_name, user_data = formatted_msg.split('\n\t')
    if file is not None:
        client.send('sending_img'.encode())
        size = os.path.getsize(file.name)
        _, extension = os.path.splitext(file.name)
        print('extension: ', extension)
        print('size: ', size)
        print('sender_name: ', name.get())
        client.send(f"{extension}\n{size}\n{name.get()}".encode())
        #time.sleep(1)
        data = file.read()
        client.sendall(data)
        client.send(b"<END>")
        filename = file.name
        file.close()
        if extension in ['.mp4','.mkv']:
            text = 'You sent a video'
            chat_box.config(state = NORMAL)
            chat_box.insert(END, " " * 45)
            chat_box.insert(END, f'{user_time}:\n')
            chat_box.insert(END, " " * 45)
            chat_box.insert(END, f'Me: ')
            chat_box.insert(END, f'{text}\n', 'link')
            chat_box.tag_config("link", foreground="blue", underline=True)
            chat_box.tag_bind("link", "<Button-1>", lambda e : open_link_file(filename))
            chat_box.config(state = DISABLED)
            count[0] += 1
            return
        elif extension in ['.txt','.pdf','.docx','.mp3','.csv','.ppt','.xlsx']:
            text = 'You sent a document'
            chat_box.config(state = NORMAL)
            chat_box.insert(END, " " * 45)
            chat_box.insert(END, f'{user_time}:\n')
            chat_box.insert(END, " " * 45)
            chat_box.insert(END, f'Me: ')
            chat_box.insert(END, f'{text}\n', 'link')
            chat_box.tag_config("link", foreground="blue", underline=True)
            chat_box.tag_bind("link", "<Button-1>", lambda e : open_link_file(filename))
            chat_box.config(state = DISABLED)
            count[0] += 1
            return
        elif extension in ['.mp3']:
            text = 'You sent an audio'
            chat_box.config(state = NORMAL)
            chat_box.insert(END, " " * 45)
            chat_box.insert(END, f'{user_time}:\n')
            chat_box.insert(END, " " * 45)
            chat_box.insert(END, f'Me: ')
            chat_box.insert(END, f'{text}\n', 'link')
            chat_box.tag_config("link", foreground="blue", underline=True)
            chat_box.tag_bind("link", "<Button-1>", lambda e : open_link_file(filename))
            chat_box.config(state = DISABLED)
            count[0] += 1
            return
        
        chat_box.config(state = NORMAL)
        chat_box.insert(END, " " * 45)
        chat_box.insert(END, f'{user_time}:\n')
        chat_box.insert(END, " " * 45)
        chat_box.insert(END, f'Me: ')
        chat_box.config(state = DISABLED)

        image = Image.open(filename)
        desired_width, desired_height = image_res(image)

        # Resize the image
        resized_image = image.resize((desired_width, desired_height), Image.LANCZOS)
        images.append(ImageTk.PhotoImage(resized_image))
        chat_box.image_create(END, image = images[-1])
        chat_box.image = images[-1]
        count[0] += 1
        count[0] += 1

def group_chat(addr, chat_box):
    client.send("GROUP".encode())
    connectionStatus.set("Connected")
    group_chat_thread = threading.Thread(target = recv_msg, args = (addr, count))       #New Thread to deal with client-Server communication
    group_chat_thread.start()

def private_chat(user, addr, req, chat_box):
    client.send(f'{req}\n{user}'.encode())
    connectionStatus.set("Connected")
    private_chat_thread = threading.Thread(target = recv_msg, args = (addr, count))
    private_chat_thread.start()

def back():
    global main_frame
    chat_frame.grid_forget()
    button_frame.grid_forget()
    main_frame.grid(row = 0, column = 0, sticky = (N, W, E, S))
    return

def close():
    disconnect()
    root.destroy()

def typing_status(event):
    client.send(f"{name.get()} is TYPING".encode())
    return

def scroll_text(event, chat_box):
    chat_box.yview_scroll(int(-1*(event.delta/120)), "units")

def chat_window(addr, user = None, req = "REQUEST"):
    main_frame.grid_forget()
    global chat_frame
    global msgInput
    global chat_box
    global count
    global button_frame

    chat_frame = ttk.Frame(root)
    chat_frame.grid(row = 0, column = 0, padx = 5, pady = 5)

    chat_box = Text(chat_frame, height = 25, width = 60)  # Increase the height and width of the text box
    chat_box.grid(row = 0, column = 0, sticky = "nsew")
    chat_box.config(state = DISABLED)

    scrollbar = Scrollbar(chat_frame)
    scrollbar.grid(row=0, column=1, sticky="ns")
    scrollbar.config(command=chat_box.yview)
    chat_box.config(yscrollcommand=scrollbar.set)

    msg_frame = Frame(chat_frame)
    msg_frame.grid(row=1, column=0, padx=5, pady=5)
    msg = StringVar()
    Label(msg_frame, text = "Enter your message: ", font=("Arial", 10)).grid(row = 0, column=0, padx=5, pady=5)
    msgInput = ttk.Entry(msg_frame, width = 60, textvariable = msg)
    msgInput.grid(row = 1, column = 0, padx=5, pady=5)
    msgInput.bind("<Return>",lambda event:send_msg(msg.get(), count, chat_box))
    msgInput.bind("<Key>", typing_status)
    
    button_frame = Frame(root)
    button_frame.grid(row=2, column=0, pady=5)

    send_button = ttk.Button(button_frame, text="Send", command = lambda:send_msg(msg.get(), count))
    send_button.grid(row=0, column=0, padx=2, pady=5)

    file_button = ttk.Button(button_frame, text="Add File", command = lambda:browse_files(msg.get(), count))
    file_button.grid(row=0, column=1, padx=2, pady=5)

    disconnect_button = ttk.Button(button_frame, text="Disconnect", command = disconnect)
    disconnect_button.grid(row=0, column=2, padx=2, pady=5)

    back_button = ttk.Button(button_frame, text="Back", command = lambda:back())
    back_button.grid(row=0, column=3, padx=2, pady=5)

    close_button = ttk.Button(button_frame, text="Close", command = close)
    close_button.grid(row=0, column=4, padx=2, pady=5)

    if user == None:
        group_chat(addr, chat_box)
    else:
        private_chat(user, addr, req, chat_box)

root = Tk()
global connectionStatus
connectionStatus = StringVar()
connectionStatus.set("Disconnected")
root.title("Multi-User Chat Application")
root.geometry("685x540")
main_frame = Frame(root)
main_frame.grid(column = 0, row = 1)

style = ttk.Style()
style.configure("TButton", font=("Arial", 10), padding=2)
style.configure("TButton", foreground="black", background="#4CAF45", width=10)

Label(main_frame, text = "Enter Username: ", font=("Arial", 10)).grid(row = 0, column = 0, sticky = W, pady = 8, padx = 4)
name = StringVar()
message = StringVar()
message.set('Users Online: None')
user_list = Label(main_frame, textvariable = message, font=("Arial", 10)).grid(column = 0, row = 1, sticky = W, pady = 8, padx = 4)

username = ttk.Entry(main_frame, width = 40, textvariable = name)
username.grid(row = 0, column = 1, sticky = W, pady = 8, padx = 4)
username.bind("<Return>", lambda event:start(count))

grp_btn = ttk.Button(main_frame, text="Group Chat", command = lambda:chat_window(addr), state=NORMAL).grid(row = 0, column = 4, sticky = W, pady = 8, padx = 4)
pvt_btn = ttk.Button(main_frame, text="Private Chat", command = lambda:listening(addr), state=NORMAL).grid(row = 0, column = 3, sticky = W, pady = 8, padx = 4)
ent_btn = ttk.Button(main_frame, text = "Enter", command = lambda: start()).grid(row = 0, column = 2, sticky = W, pady = 2, padx = 2)

count = [1]
root.protocol("WM_DELETE_WINDOW", close)
root.mainloop()