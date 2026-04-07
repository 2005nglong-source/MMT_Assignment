import asyncio
import json
import threading
from daemon.asynaprous import AsynapRous
from daemon.request import Request

app = AsynapRous()
# Danh sách lưu thông tin các peer (IP, Port)
peers = [] 

@app.route('/chat', methods=['POST'])
async def handle_incoming_chat(headers, body):
    """Hàm này sẽ được gọi khi có peer khác gửi tin nhắn tới[cite: 423]."""
    data = json.loads(body)
    print(f"\n[Tin nhắn từ {data['sender']}]: {data['msg']}")
    print("Nhập tin nhắn của bạn: ", end='', flush=True)
    return {'status': 'success'}import socket

HOST = "127.0.0.1"

# ====== CONFIG ======
PORT = int(input("Enter your port: "))

# Nhập danh sách peer khác (vd: 127.0.0.1:5002,127.0.0.1:5003)
peer_input = input("Enter peers (ip:port, comma separated): ")

peers = []
if peer_input:
    for p in peer_input.split(","):
        ip, port = p.split(":")
        peers.append((ip.strip(), int(port.strip())))

# ====== SERVER (RECEIVE MESSAGE) ======
def handle_client(conn, addr):
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            msg = json.loads(data.decode())

            print(f"\n[{msg['from']}]: {msg['message']}")
    except:
        pass
    finally:
        conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    print(f"🚀 Listening on {PORT}...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


# ====== CLIENT (SEND MESSAGE) ======
def send_to_peer(peer, message_data):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(peer)
        s.send(json.dumps(message_data).encode())
        s.close()
    except:
        print(f"⚠️ Cannot connect to {peer}")


def send_message():
    name = input("Enter your name: ")

    while True:
        msg = input("You: ")

        if msg.lower() == "exit":
            print("Exiting...")
            break

        message_data = {
            "from": f"{name}:{PORT}",
            "message": msg
        }

        # Broadcast tới tất cả peers
        for peer in peers:
            threading.Thread(target=send_to_peer, args=(peer, message_data), daemon=True).start()


# ====== MAIN ======
if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    send_message()
