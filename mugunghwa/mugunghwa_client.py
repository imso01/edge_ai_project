import cv2
import time
import socket
import numpy as np
import pyrealsense2 as rs
from openpose import pyopenpose as op
from gtts import gTTS
import os
import random

# 음성 출력 함수 (TTS)
def speak(text, speed='normal'):
    tts = gTTS(text=text, lang='ko', slow=(speed == 'slow'))
    tts.save("output.mp3")

    if speed == 'fast':
        os.system("mpg123 --pitch +1 output.mp3")
    elif speed == 'slow':
        os.system("mpg123 output.mp3")
    else:
        os.system("mpg123 output.mp3")

# 거리 보정 함수
def get_stable_distance(depth_frame, x, y, window=2):
    depths = []
    width = depth_frame.get_width()
    height = depth_frame.get_height()
    for dx in range(-window, window + 1):
        for dy in range(-window, window + 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                d = depth_frame.get_distance(nx, ny)
                if 0.1 < d < 10.0:
                    depths.append(d)
    if depths:
        return sum(depths) / len(depths)
    else:
        return 0.0

# 서버 연결
def connect_to_server(host='127.0.0.1', port=5000):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall("KJH".encode())
        print("[서버 연결 성공 및 ID 전송 완료]")
        return s
    except Exception as e:
        print("[서버 연결 실패]:", e)
        return None

# OpenPose 초기화
params = {"model_folder": "models/", "model_pose": "BODY_25"}
op_wrapper = op.WrapperPython()
op_wrapper.configure(params)
op_wrapper.start()

# RealSense 카메라 초기화
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
pipeline.start(config)

motion_threshold = 50
victory_distance = 0.7

server_socket = connect_to_server()
if not server_socket:
    exit()

print("게임 시작 대기 중: 서버로부터 '무궁화' 명령을 기다립니다...")

try:
    while True:
        data = server_socket.recv(1024).decode().strip()
        if data == "무궁화":
            print("[서버] '무궁화' 수신됨. 게임 시작 가능.")
            break
        else:
            print("[서버 수신 대기 중] 현재 수신:", data)
except Exception as e:
    print("[서버 수신 오류]:", e)
    server_socket.close()
    exit()

print("게임 시작: 'c' 키를 누르면 게임 시작")
print("움직이지 않고 카메라에 가까이 다가가면 승리!")

try:
    while True:
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        datum = op.Datum()
        datum.cvInputData = color_image
        datums = op.VectorDatum()
        datums.append(datum)
        op_wrapper.emplaceAndPop(datums)

        cv2.imshow("OpenPose", datums[0].cvOutputData)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('c'):
            speed = random.choice(['fast', 'normal', 'slow'])
            speak("무궁화 꽃이 피었습니다", speed)
            print(f"[TTS] 속도 = {speed}")

            print("[LCD] 무궁화 꽃이 피었습니다.")

            wait_start = time.time()
            while time.time() - wait_start < 5:
                frames = pipeline.wait_for_frames()
                color_frame = frames.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data())
                remaining = int(5 - (time.time() - wait_start))
                cv2.putText(color_image, f"Starting in {remaining}s", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.imshow("OpenPose", color_image)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            print("[LCD] 술래가 당신을 보고 있습니다!")
            print("3초간 움직이지 마십시오!")

            pose_sum = []
            start_time = time.time()
            while time.time() - start_time < 3:
                frames = pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data())

                datum = op.Datum()
                datum.cvInputData = color_image
                datums = op.VectorDatum()
                datums.append(datum)
                op_wrapper.emplaceAndPop(datums)

                keypoints = datums[0].poseKeypoints
                if keypoints is None or len(keypoints.shape) < 3:
                    continue

                person = keypoints[0][:, :2]
                pose_sum.append(person)

                cv2.putText(datums[0].cvOutputData, "Soolrae is watching...", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                cv2.imshow("OpenPose", datums[0].cvOutputData)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            moved = False
            for i in range(1, len(pose_sum)):
                diffs = np.linalg.norm(pose_sum[i] - pose_sum[i - 1], axis=1)
                mean_movement = np.mean(diffs)
                if mean_movement > motion_threshold:
                    moved = True
                    break

            if moved:
                print("Game Over: 움직임이 감지되었습니다.")
                server_socket.sendall("Game Over".encode())
                continue
            else:
                print("움직이지 않음 확인. 전진 시작!")

            success_count = 0
            while True:
                frames = pipeline.wait_for_frames()
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data())

                datum = op.Datum()
                datum.cvInputData = color_image
                datums = op.VectorDatum()
                datums.append(datum)
                op_wrapper.emplaceAndPop(datums)

                keypoints = datums[0].poseKeypoints
                if keypoints is None or len(keypoints.shape) < 3:
                    continue

                person = keypoints[0]
                x = int((person[1][0] + person[8][0]) / 2)
                y = int((person[1][1] + person[8][1]) / 2)

                distance = get_stable_distance(depth_frame, x, y)

                if distance == 0.0:
                    print("거리 정보가 유효하지 않음, 다시 측정 중...")
                    success_count = 0
                    continue

                print(f"현재 거리: {distance:.2f}m")
                cv2.putText(datums[0].cvOutputData, "Move forward...", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                cv2.putText(datums[0].cvOutputData, f"Distance: {distance:.2f}m", (10, 65),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

                if distance < victory_distance:
                    success_count += 1
                    if success_count >= 2:
                        print("🎉 Victory! 도착했습니다.")
                        server_socket.sendall("Victory".encode())
                        break
                else:
                    success_count = 0

                cv2.imshow("OpenPose", datums[0].cvOutputData)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        elif key == ord('q'):
            break

finally:
    server_socket.close()
    pipeline.stop()
    cv2.destroyAllWindows()
