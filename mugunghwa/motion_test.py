import cv2
import time
import numpy as np
from openpose import pyopenpose as op

# OpenPose 설정
params = {
    "model_folder": "models/",
    "model_pose": "BODY_25",
    "net_resolution": "-1x368",
    "disable_blending": False
}

# OpenPose 초기화
op_wrapper = op.WrapperPython()
op_wrapper.configure(params)
op_wrapper.start()

# 카메라 열기
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not cap.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

print("게임 시작: 'c' 키를 누르면 게임 시작")
print("3초 안에 움직이면 'Game Over'!")

motion_threshold = 80  # 민감도

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("OpenPose", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('c'):
        print("[TTS] 무궁화 꽃이 피었습니다.")  # TTS로 대체예정
        print("[LCD] 술래가 당신을 보지 않고 있습니다.") # LCD로 대체예정

        # 5초 비차단 대기 루프
        wait_start = time.time()
        while time.time() - wait_start < 5:
            ret, frame = cap.read()
            if not ret:
                break

            remaining = int(5 - (time.time() - wait_start))
            cv2.putText(frame, f"Starting in {remaining}s", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.imshow("OpenPose", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        print("[LCD] 술래가 당신을 보고 있습니다!")  # LCD 출력 대신 텍스트
        print("3초간 움직이지 마십시오!")

        pose_sum = []
        start_time = time.time()
        while time.time() - start_time < 3:
            ret, frame = cap.read()
            if not ret:
                break

            datum = op.Datum()
            datum.cvInputData = frame
            datum_ptr = op.VectorDatum()
            datum_ptr.append(datum)
            op_wrapper.emplaceAndPop(datum_ptr)

            keypoints = datum_ptr[0].poseKeypoints
            if keypoints is None or len(keypoints.shape) < 3:
                continue

            person = keypoints[0][:, :2]  # (25, 2)
            pose_sum.append(person)


            cv2.putText(datum_ptr[0].cvOutputData, "Soolrae is watching...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            
            cv2.imshow("OpenPose", datum_ptr[0].cvOutputData)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # 움직임 분석
        moved = False
        for i in range(1, len(pose_sum)):
            diffs = np.linalg.norm(pose_sum[i] - pose_sum[i - 1], axis=1)
            mean_movement = np.mean(diffs)
            if mean_movement > motion_threshold:
                moved = True
                break

        if moved:
            print("Game Over: 움직임이 감지되었습니다.")
        else:
            print("Success: 움직이지 않았습니다.")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
