import json
import asyncio
from daemon.asynaprous import AsynapRous

# Khởi tạo webapp cho Peer hiện tại
app = AsynapRous()

# Giả lập danh sách peers lấy từ Tracker (bạn cần phối hợp với bạn làm Client-Server để cập nhật list này)
# Ví dụ: active_peers = [{"ip": "192.168.56.104", "port": 9001}, {"ip": "192.168.56.105", "port": 9002}]
active_peers = [] 

# ==========================================
# 1. PHÍA NHẬN (PEER AS SERVER) - Hứng tin nhắn
# ==========================================

@app.route('/send-peer', methods=['POST'])
def receive_direct_message(headers, body):
    """Xử lý khi có một peer khác gửi tin nhắn trực tiếp đến máy mình"""
    try:
        # Parse nội dung tin nhắn (giả định dùng JSON)
        data = json.loads(body)
        sender = data.get("sender_ip", "Unknown")
        msg = data.get("message", "")
        
        # TODO: Cập nhật tin nhắn này ra màn hình hiển thị (Giao diện)
        print(f"[Direct] Nhận từ {sender}: {msg}")
        
        return json.dumps({"status": "success", "info": "Đã nhận tin nhắn"})
    except Exception as e:
        return json.dumps({"status": "error", "info": str(e)})

@app.route('/broadcast-peer', methods=['POST'])
def receive_broadcast_message(headers, body):
    """Xử lý khi nhận được tin nhắn quảng bá từ mạng"""
    try:
        data = json.loads(body)
        sender = data.get("sender_ip", "Unknown")
        msg = data.get("message", "")
        
        # TODO: Cập nhật lên kênh chat chung
        print(f"[Broadcast] Nhận từ {sender}: {msg}")
        
        return json.dumps({"status": "success"})
    except Exception as e:
        return json.dumps({"status": "error", "info": str(e)})

# ==========================================
# 2. PHÍA GỬI (PEER AS CLIENT) - Gửi Non-blocking bằng Asyncio
# ==========================================

async def send_p2p_message(target_ip, target_port, message, endpoint="/send-peer"):
    """
    Hàm lõi để mở kết nối và gửi tin nhắn HTTP trực tiếp đến peer khác.
    Sử dụng non-blocking coroutine.
    """
    try:
        # Mở kết nối non-blocking
        reader, writer = await asyncio.open_connection(target_ip, target_port)
        
        # Chuẩn bị gói tin JSON
        payload = json.dumps({"sender_ip": "IP_CỦA_MÌNH", "message": message})
        
        # Đóng gói thành HTTP POST Request (Vì peer kia đang chạy AsynapRous nhận HTTP)
        http_request = (
            f"POST {endpoint} HTTP/1.1\r\n"
            f"Host: {target_ip}:{target_port}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(payload)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{payload}"
        )
        
        # Gửi dữ liệu đi
        writer.write(http_request.encode('utf-8'))
        await writer.drain() # Đợi đẩy hết dữ liệu đi mà không block chương trình
        
        # Đọc phản hồi (Tùy chọn, để biết bên kia đã nhận hay chưa)
        response = await reader.read(1024)
        
        # Đóng kết nối
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f"Lỗi gửi tin tới {target_ip}:{target_port} - {e}")

async def broadcast_message(message):
    """
    Gửi tin nhắn cho toàn bộ peer đang online.
    Sử dụng asyncio.gather để gửi song song (rất nhanh).
    """
    tasks = []
    for peer in active_peers:
        # Tạo task gửi cho từng peer
        task = send_p2p_message(peer["ip"], peer["port"], message, endpoint="/broadcast-peer")
        tasks.append(task)
    
    # Kích hoạt chạy đồng loạt tất cả các task
    if tasks:
        await asyncio.gather(*tasks)

@app.route('/local-send', methods=['POST'])
def trigger_send_from_ui(headers, body):
    """
    Giao diện web (JS) của bạn sẽ gọi API này để ra lệnh cho backend gửi tin đi.
    """
    data = json.loads(body)
    msg = data.get("message")
    chat_type = data.get("type") 

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if chat_type == 'broadcast':
        loop.run_until_complete(broadcast_message(msg))
    else:
        # Gửi direct (cần target_ip và target_port từ giao diện truyền xuống)
        target_ip = data.get("target_ip")
        target_port = data.get("target_port")
        loop.run_until_complete(send_p2p_message(target_ip, target_port, msg))

    return json.dumps({"status": "Đã xử lý tiến trình gửi"})

def create_p2p_app(ip, port):
    app.prepare_address(ip, port)
    app.run()
