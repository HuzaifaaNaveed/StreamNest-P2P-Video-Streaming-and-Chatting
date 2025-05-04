import socket
import threading
import json
import time
clients = []
streamer = None
lock = threading.Lock()

def send(sock, msg):
    data = json.dumps(msg).encode()
    length = len(data).to_bytes(4, 'big')
    sock.sendall(length + data)

def recv(sock):
    length = int.from_bytes(sock.recv(4), 'big')
    data = sock.recv(length).decode()
    return json.loads(data)

def sendall(msg, skip=None):
    for c in clients:
        if c != skip:
            try:
                send(c, msg)
            except:
                pass

def handle(sock, addr):
    global streamer
    try:
        clients.append(sock)
        print(f"{addr} joined")
        send(sock, {"type": "status", "active": streamer is not None})
        name = recv(sock).get("name", "anon")
        print(f"User {name} connected from {addr}")
        sendall({"type": "chat", "name": "Server", "msg": f"{name} has joined"})
        while True:
            msg = recv(sock)
            t = msg.get("type")
            if t == "start":
                with lock:
                    if not streamer:
                        streamer = sock
                        send(sock, {"type": "start", "ok": True})
                        sendall({"type": "status", "active": True})
                        print(f"{name} started streaming")
                        sendall({"type": "chat", "name": "Server", "msg": f"{name} started streaming"})
                    else:
                        send(sock, {"type": "start", "ok": False})
            elif t == "stop":
                with lock:
                    if streamer == sock:
                        streamer = None
                        sendall({"type": "status", "active": False})
                        print(f"{name} stopped streaming")
                        sendall({"type": "chat", "name": "Server", "msg": f"{name} stopped streaming"})
            elif t == "video":
                if sock == streamer:
                    sendall({"type": "video", "data": msg["data"]}, skip=None)
            elif t == "chat":
                chatmsg = msg.get("msg", "")
                print(f"Chat: {name}: {chatmsg}")
                sendall({"type": "chat", "name": name, "msg": chatmsg}, skip=None)
    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        if sock in clients:
            clients.remove(sock)
        if sock == streamer:
            streamer = None
            sendall({"type": "status", "active": False})
            print(f"Streamer {name} disconnected")
            sendall({"type": "chat", "name": "Server", "msg": f"{name} has left"})
        else:
            print(f"User {name} disconnected")
            sendall({"type": "chat", "name": "Server", "msg": f"{name} has left"})
        try:
            sock.close()
        except:
            pass

def run():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 5000))
    s.listen(5)
    print("StreamNest Server running on port 5000")
    print("Waiting for connections...")
    try:
        while True:
            c, a = s.accept()
            threading.Thread(target=handle, args=(c, a), daemon=True).start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        for client in clients[:]:
            try:
                client.close()
            except:
                pass
        s.close()
        print("Server stopped")

if __name__ == "__main__":
    run()