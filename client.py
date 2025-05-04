import socket
import threading
import json
import tkinter as tk
from tkinter import filedialog, scrolledtext, font
from tkinter import ttk
import cv2 # type: ignore
import base64
import sys
import time
from PIL import Image, ImageTk # type: ignore
import numpy as np # type: ignore
import random

usercount = 1
username = f"User{usercount}"
s = socket.socket()
videopath = None
streaming = False
viewing = False
running = True

def connect():
    global s
    s = socket.socket()
    try:
        s.connect(('localhost', 5000))
        return True
    except:
        return False
    
def send(msg):
    data = json.dumps(msg).encode()
    length = len(data).to_bytes(4, 'big')
    s.sendall(length + data)

def recv():
    length = int.from_bytes(s.recv(4), 'big')
    data = s.recv(length).decode()
    return json.loads(data)

def startapp():
    global username, usercount
    startwin = tk.Tk()
    startwin.title("StreamNest")
    startwin.geometry("600x400")
    startwin.configure(bg="#0e0e10")
    startwin.update_idletasks()

    width = startwin.winfo_width()
    height = startwin.winfo_height()
    x = (startwin.winfo_screenwidth() // 2) - (width // 2)
    y = (startwin.winfo_screenheight() // 2) - (height // 2)

    startwin.geometry(f'{width}x{height}+{x}+{y}')
    titlefont = font.Font(family="Helvetica", size=28, weight="bold")
    title = tk.Label(startwin, text="StreamNest", font=titlefont, bg="#0e0e10", fg="#9147ff")
    title.pack(pady=(80, 10))

    descfont = font.Font(family="Helvetica", size=12)
    desc = tk.Label(startwin, text="Share your videos with friends in real-time", font=descfont, bg="#0e0e10", fg="#a19fa1")
    desc.pack(pady=(0, 40))

    userframe = tk.Frame(startwin, bg="#0e0e10")
    userframe.pack(pady=10)
    userlabel = tk.Label(userframe, text="Username:", font=("Helvetica", 10), bg="#0e0e10", fg="#a19fa1")
    userlabel.pack(side=tk.LEFT, padx=5)
    userentry = tk.Entry(userframe, width=20, font=("Helvetica", 10), bg="#18181b", fg="white", insertbackground="white")
    userentry.insert(0, username)
    userentry.pack(side=tk.LEFT, padx=5)

    btnframe = tk.Frame(startwin, bg="#0e0e10")
    btnframe.pack(pady=30)
    buttonstyle = {"font": ("Helvetica", 10), "width": 15, "height": 2, "cursor": "hand2"}
    
    def openstream():
        global username
        username = userentry.get() if userentry.get().strip() else username
        startwin.destroy()
        mainapp("stream")
    
    def openjoin():
        global username
        username = userentry.get() if userentry.get().strip() else username
        startwin.destroy()
        mainapp("join")
    
    streambtn = tk.Button(btnframe, text="Start Streaming", bg="#9147ff", fg="white", command=openstream, **buttonstyle)
    streambtn.pack(side=tk.LEFT, padx=10)
    joinbtn = tk.Button(btnframe, text="Join Stream", bg="#9147ff", fg="white", command=openjoin, **buttonstyle)
    joinbtn.pack(side=tk.LEFT, padx=10)
    statusmsg = tk.Label(startwin, text="Connecting to server...", font=("Helvetica", 8), bg="#0e0e10", fg="#a19fa1")
    statusmsg.pack(side=tk.BOTTOM, pady=10)

    if connect():
        statusmsg.config(text="Connected to server")
    else:
        statusmsg.config(text="Failed to connect to server. Please restart the application.", fg="#ff0000")
        streambtn.config(state=tk.DISABLED)
        joinbtn.config(state=tk.DISABLED)
    startwin.mainloop()

def mainapp(mode):
    global videopath, streaming, viewing, running, username
    send({"name": username})
    root = tk.Tk()
    root.title(f"StreamNest - {username}")
    root.geometry("1000x700")
    root.configure(bg="#0e0e10")

    headerframe = tk.Frame(root, bg="#18181b", height=60)
    headerframe.pack(fill=tk.X)
    logo = tk.Label(headerframe, text="StreamNest", font=("Helvetica", 18, "bold"), bg="#18181b", fg="#9147ff")
    logo.pack(side=tk.LEFT, padx=20, pady=10)
    contentframe = tk.Frame(root, bg="#0e0e10")
    contentframe.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    videoframe = tk.Frame(contentframe, bg="#18181b", width=700)
    videoframe.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
    videoframe.pack_propagate(False)
    videoborder = tk.Frame(videoframe, bg="#18181b", bd=1, relief=tk.SOLID)
    videoborder.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    videolabel = tk.Label(videoborder, bg="black")
    videolabel.pack(fill=tk.BOTH, expand=True)

    controlframe = tk.Frame(videoframe, height=50, bg="#18181b")
    controlframe.pack(fill=tk.X, padx=10, pady=(0, 10))
    chatframe = tk.Frame(contentframe, bg="#18181b", width=280)
    chatframe.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
    chatframe.pack_propagate(False)
    chattitle = tk.Label(chatframe, text="Live Chat", font=("Helvetica", 12, "bold"), bg="#18181b", fg="#9147ff")
    chattitle.pack(pady=(10, 5))
    chatbox = scrolledtext.ScrolledText(chatframe, height=30, bg="#0e0e10", font=("Helvetica", 9), fg="white", insertbackground="white")
    chatbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
    chatbox.config(state='disabled')
    chatinput = tk.Entry(chatframe, font=("Helvetica", 10), bg="#0e0e10", fg="white", insertbackground="white")
    chatinput.pack(fill=tk.X, padx=10, pady=(0, 5))
    sendbtn = tk.Button(chatframe, text="Send", bg="#9147ff", fg="white", font=("Helvetica", 9), height=1, cursor="hand2")
    
    sendbtn.pack(fill=tk.X, padx=10, pady=(0, 10))
    statusframe = tk.Frame(root, bg="#18181b", height=25)
    statusframe.pack(fill=tk.X, side=tk.BOTTOM)
    statuslbl = tk.Label(statusframe, text="Not connected", font=("Helvetica", 8), bg="#18181b", fg="#a19fa1")
    statuslbl.pack(side=tk.LEFT, padx=10)
    userlbl = tk.Label(statusframe, text=f"Logged in as: {username}", font=("Helvetica", 8), bg="#18181b", fg="#a19fa1")
    userlbl.pack(side=tk.RIGHT, padx=10)
    
    def select():
        global videopath
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mkv")])
        if path:
            videopath = path
            statuslbl.config(text=f"Selected: {path.split('/')[-1]}")
            filelbl.config(text=f"File: {path.split('/')[-1]}")
    
    def start():
        if not videopath:
            statuslbl.config(text="Select a video first")
            return
        send({"type": "start"})
    
    def stop():
        global streaming
        send({"type": "stop"})
        streaming = False
        streambtn.config(text="Start Stream", bg="#9147ff")
        statuslbl.config(text="Streaming stopped")
    
    def stream():
        global streaming
        cap = cv2.VideoCapture(videopath)
        while streaming and running:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            h, w = frame.shape[:2]
            ratio = min(videolabel.winfo_width()/w, videolabel.winfo_height()/h)
            newsize = (int(w*ratio), int(h*ratio))
            frame = cv2.resize(frame, newsize)
            rgbframe = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgbframe)
            imgtk = ImageTk.PhotoImage(image=img)
            videolabel.imgtk = imgtk
            videolabel.config(image=imgtk)
            sendframe = cv2.resize(frame, (640, 480))
            _, buf = cv2.imencode('.jpg', sendframe, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64 = base64.b64encode(buf).decode()
            send({"type": "video", "data": b64})
            time.sleep(0.03)
        cap.release()
    
    def toggle():
        global streaming
        if not streaming:
            start()
        else:
            stop()
    
    def chat(event=None):
        msg = chatinput.get()
        if msg.strip():
            send({"type": "chat", "msg": msg})
            chatinput.delete(0, tk.END)
    
    def updatevideo(img):
        imgtk = ImageTk.PhotoImage(image=img)
        videolabel.imgtk = imgtk
        videolabel.config(image=imgtk)
    
    def endstream():
        send({"type": "endstream"})
        
    def listen():
        global streaming, viewing
        while running:
            try:
                msg = recv()
                t = msg.get("type")
                if t == "status":
                    active = msg.get("active", False)
                    if active:
                        if not streaming:
                            statuslbl.config(text="Someone is streaming")
                            if mode == "stream":
                                streambtn.config(state=tk.DISABLED)
                            viewing = True
                    else:
                        statuslbl.config(text="No active streams")
                        if mode == "stream":
                            streambtn.config(state=tk.NORMAL)
                        viewing = False
                        videolabel.config(image="")
                elif t == "start":
                    if msg.get("ok"):
                        streaming = True
                        streambtn.config(text="Stop Stream", bg="#ff0000")
                        statuslbl.config(text="Streaming started")
                        threading.Thread(target=stream, daemon=True).start()
                    else:
                        statuslbl.config(text="Cannot stream: Another user is streaming")
                elif t == "video" and viewing:
                    b64 = msg.get("data")
                    if b64:
                        jpg_bytes = base64.b64decode(b64)
                        np_img = np.frombuffer(jpg_bytes, dtype=np.uint8)
                        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img = Image.fromarray(frame)
                        root.after(0, updatevideo, img)
                elif t == "chat":
                    sender = msg.get("name", "anon")
                    text = msg.get("msg", "")
                    chatbox.config(state='normal')
                    if sender == username:
                        chatbox.insert(tk.END, f"{sender}: ", "self")
                    else:
                        chatbox.insert(tk.END, f"{sender}: ", "other")
                    chatbox.insert(tk.END, f"{text}\n")
                    chatbox.yview(tk.END)
                    chatbox.config(state='disabled')
            except Exception as e:
                print(f"Error: {e}")
                break
    
    def close():
        global running
        running = False
        if streaming:
            stop()
        try:
            s.close()
        except:
            pass
        root.destroy()

    if mode == "stream":
        filebtn = tk.Button(controlframe, text="Select Video", bg="#9147ff", fg="white", font=("Helvetica", 9), command=select, width=15, cursor="hand2")
        filebtn.pack(side=tk.LEFT, padx=10, pady=5)
        filelbl = tk.Label(controlframe, text="No file selected", bg="#18181b", font=("Helvetica", 9), fg="white")
        filelbl.pack(side=tk.LEFT, padx=5, pady=5)
        streambtn = tk.Button(controlframe, text="Start Stream", bg="#9147ff", fg="white", font=("Helvetica", 9), command=toggle, width=15, cursor="hand2")
        streambtn.pack(side=tk.RIGHT, padx=10, pady=5)
    chatbox.tag_config("self", foreground="#9147ff", font=("Helvetica", 9, "bold"))
    chatbox.tag_config("other", foreground="#00b5ad", font=("Helvetica", 9, "bold"))
    sendbtn.config(command=chat)
    chatinput.bind("<Return>", chat)
    root.protocol("WM_DELETE_WINDOW", close)
    threading.Thread(target=listen, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    startapp()