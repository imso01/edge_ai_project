import cv2
import time
import socket
from ultralytics import YOLO

def connect_to_server(host='172.27.239.133', port=5000):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall("LSY".encode())  # ID 전송
        print("[서버 연결 성공 및 ID 전송 완료]")
        return s
    except Exception as e:
        print("[서버 연결 실패]:", e)
        return None

# ✅ 서버 먼저 연결
server_socket = connect_to_server()
if not server_socket:
    exit()

# ✅ YOLO 로딩
model = YOLO('runs/detect/train2/weights/best.pt')
cap = cv2.VideoCapture(0)

last_print_time = 0
print_interval = 10

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, imgsz=640, conf=0.5, verbose=False)[0]
    names = model.names

    if len(results.boxes) > 0:
        cls_id = int(results.boxes.cls[0])
        name = names[cls_id]

        current_time = time.time()
        if current_time - last_print_time > print_interval:
            print(f"✅ 감지된 동물: {name}")
            try:
                # 🔁 소켓으로 동물 이름 보내기
                server_socket.sendall(name.encode())
                print("[✅ 서버로 전송 완료]")
            except Exception as e:
                print("🚨 서버 전송 실패:", e)

            last_print_time = current_time

    cv2.imshow("Animal Detector", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ✅ 정리
cap.release()
cv2.destroyAllWindows()
server_socket.close()