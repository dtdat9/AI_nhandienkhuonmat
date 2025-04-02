# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os
import queryDB as db
import time
import datetime
import tkinter as tk
from tkinter import messagebox
import pyodbc  # Thư viện kết nối tới Access

# ---------------------- CẤU HÌNH ----------------------
ORIG_WIDTH = 732
ORIG_HEIGHT = 720
LEFT_DISPLAY_WIDTH = 500
scale_factor = LEFT_DISPLAY_WIDTH / ORIG_WIDTH
LEFT_DISPLAY_HEIGHT = int(ORIG_HEIGHT * scale_factor)
RIGHT_WIDTH = 500
STATUS_IMAGE_SIZE = 500  # 500x500 cho ảnh trạng thái
BUTTON_HEIGHT = 100      # Vùng nút "Tắt" có chiều cao 100 pixel
COMPOSITE_WIDTH = LEFT_DISPLAY_WIDTH + RIGHT_WIDTH  # 500 + 500 = 1000
COMPOSITE_HEIGHT = 600  # Chiều cao cố định

BACKGROUND_COLOR = (250, 250, 250)     # Nền trắng tinh
ACCENT_COLOR = (220, 20, 60)           # Màu đỏ thẫm
TEXT_COLOR = (0, 0, 0)
BASE_DIR = "D:/Study/Nam3/NCKH/okok"
PATH_DATABASE = os.path.join(BASE_DIR, "dulieudiemdanh.accdb")
CASCADE_PATH = "haarcascade_frontalface_default.xml"
TRAINING_DATA_PATH = "recognizer/trainingData.yml"
FONT_PATH = "fonts/Roboto-Regular.ttf"  # Đường dẫn font TTF (nếu có)

shutdown_flag = False

# ---------------------- THAM SỐ CHO CHẾ ĐỘ NHẬN DIỆN ----------------------
# detection_mode: "automatic" (mặc định) hoặc "manual"
detection_mode = "automatic"
# Dùng chế độ tự động để test
detection_mode = "automatic"
paused = False
pending_profile = None
frozen_frame = None
recent_info = []

# ---------------------- KHỞI TẠO FONT ----------------------
try:
    ft = cv2.freetype.createFreeType2()
    ft.loadFontData(fontFileName=FONT_PATH, id=0)
    use_freetype = True
    print("Sử dụng freetype cho font chữ.")
except Exception as e:
    use_freetype = False

# ---------------------- HÀM HỖ TRỢ ----------------------
def load_images(directory):
    images = {}
    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            img = cv2.imread(os.path.join(directory, filename))
            if img is not None:
                images[filename] = img
    return images

def init_camera():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        print("Không thể mở camera.")
        exit()
    return cam

def write_to_access(db_path, id_val, ma_sv, ho_va_ten, ngay_diem_danh):
    """
    Chèn dữ liệu điểm danh vào bảng DiemDanh trong cơ sở dữ liệu Access.
    Bảng DiemDanh có các trường: ID, MaSV, HoVaTen, NgayDiemDanh.
    ID được nhập từ hệ thống (không tự động tăng).
    """
    conn_str = (
        r'Driver={Microsoft Access Driver (*.mdb, *.accdb)};'
        r'DBQ=' + db_path + ';'
    )
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        sql = "INSERT INTO DiemDanh (ID, MaSV, HoVaTen, NgayDiemDanh) VALUES (?, ?, ?, ?)"
        # Giả sử profile trả về: (ID, HoVaTen, MaSV)
        params = (id_val, ma_sv, ho_va_ten, ngay_diem_danh)
        print("Đang chèn dữ liệu:", params)
        cursor.execute(sql, params)
        conn.commit()
        cursor.close()
        conn.close()
        print("Lưu thông tin vào Access thành công.")
    except Exception as e:
        print("Lỗi khi ghi dữ liệu vào Access:", e)

def draw_text(img, text, pos, font_scale, color, thickness):
    if use_freetype:
        ft.putText(img, text, pos, int(font_scale), color, thickness, cv2.LINE_AA, False)
    else:
        scale = font_scale / 30.0
        cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)

def draw_text_with_shadow(img, text, pos, font_scale, color, thickness):
    offset = (2, 2)
    draw_text(img, text, (pos[0] + offset[0], pos[1] + offset[1]), font_scale, (0, 0, 0), thickness + 1)
    draw_text(img, text, pos, font_scale, color, thickness)

def draw_info_overlay(area, font_scale):
    overlay = area.copy()
    h, w = area.shape[:2]
    overlay_height = 100
    cv2.rectangle(overlay, (0, h - overlay_height), (w, h), (255, 255, 255), -1)
    alpha = 0.75
    area[h - overlay_height:h, 0:w] = cv2.addWeighted(
        overlay[h - overlay_height:h, 0:w],
        alpha,
        area[h - overlay_height:h, 0:w],
        1 - alpha,
        0
    )
    header = "Attendance Information: "
    header_pos = (20, h - overlay_height + 30)
    draw_text_with_shadow(area, header, header_pos, font_scale, TEXT_COLOR, 2)
    if not recent_info:
        draw_text_with_shadow(area, "No Attendance Information", (20, h - overlay_height + 70), font_scale - 5, TEXT_COLOR, 1)
    else:
        # recent_info: (HoVaTen, MaSV, timestamp)
        ho_va_ten, ma_sv, timestamp = recent_info[0]
        time_str = datetime.datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        info_line = f"{ma_sv} | {ho_va_ten} | {time_str}"
        draw_text_with_shadow(area, info_line, (20, h - overlay_height + 70), font_scale - 5, TEXT_COLOR, 1)

def draw_status_area(canvas, status_img):
    status_img = cv2.resize(status_img, (STATUS_IMAGE_SIZE, STATUS_IMAGE_SIZE))
    canvas[0:STATUS_IMAGE_SIZE, 0:RIGHT_WIDTH] = status_img
    cv2.rectangle(canvas, (0, 0), (RIGHT_WIDTH - 1, STATUS_IMAGE_SIZE - 1), (200, 200, 200), 2)

def draw_shutdown_button(canvas):
    margin = 20
    x1, y1 = margin, STATUS_IMAGE_SIZE + margin
    x2, y2 = RIGHT_WIDTH - margin, COMPOSITE_HEIGHT - margin
    cv2.rectangle(canvas, (x1, y1), (x2, y2), ACCENT_COLOR, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 0), 2)
    text = "OFF"
    text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
    text_w, text_h = text_size
    pos = (x1 + (x2 - x1 - text_w) // 2, y1 + (y2 - y1 + text_h) // 2)
    draw_text_with_shadow(canvas, text, pos, 30, (255, 255, 255), 2)

def draw_system_title(canvas):
    text = "Face Recognition System"
    text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
    text_w, _ = text_size
    pos = ((COMPOSITE_WIDTH - text_w) // 2, 50)
    draw_text_with_shadow(canvas, text, pos, 30, ACCENT_COLOR, 2)

def draw_detection_mode_button(canvas):
    x1, y1 = COMPOSITE_WIDTH - 150, 10
    x2, y2 = COMPOSITE_WIDTH - 10, 50
    cv2.rectangle(canvas, (x1, y1), (x2, y2), ACCENT_COLOR, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 0), 2)
    text = " Mode or Method"
    text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    text_w, text_h = text_size
    pos = (x1 + (150 - text_w) // 2, y1 + (40 + text_h) // 2)
    draw_text_with_shadow(canvas, text, pos, 24, (255, 255, 255), 2)

def draw_confirm_button(canvas):
    btn_width, btn_height = 200, 60
    x1 = (COMPOSITE_WIDTH - btn_width) // 2
    y1 = (COMPOSITE_HEIGHT - btn_height) // 2
    x2 = x1 + btn_width
    y2 = y1 + btn_height
    cv2.rectangle(canvas, (x1, y1), (x2, y2), ACCENT_COLOR, -1)
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (0, 0, 0), 2)
    text = "Confirm"
    text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
    text_w, text_h = text_size
    pos = (x1 + (btn_width - text_w) // 2, y1 + (btn_height + text_h) // 2)
    draw_text_with_shadow(canvas, text, pos, 30, (255, 255, 255), 2)
    return (x1, y1, x2, y2)

def choose_detection_mode():
    global detection_mode, paused
    temp_root = tk.Tk()
    temp_root.withdraw()
    res = messagebox.askyesno("Chọn phương thức", "Bạn có muốn sử dụng chế độ Thủ công?\n(Yes: Thủ công, No: Tự động)")
    if res:
        detection_mode = "manual"
    else:
        detection_mode = "automatic"
    paused = False
    temp_root.destroy()

def mouse_callback(event, x, y, flags, param):
    global shutdown_flag, paused, pending_profile, detection_mode, frozen_frame, recent_info
    if event == cv2.EVENT_LBUTTONDOWN:
        margin = 20
        btn_shutdown_x1 = LEFT_DISPLAY_WIDTH + margin
        btn_shutdown_y1 = STATUS_IMAGE_SIZE + margin
        btn_shutdown_x2 = COMPOSITE_WIDTH - margin
        btn_shutdown_y2 = COMPOSITE_HEIGHT - margin
        if btn_shutdown_x1 <= x <= btn_shutdown_x2 and btn_shutdown_y1 <= y <= btn_shutdown_y2:
            shutdown_flag = True
            print("Nhận lệnh tắt từ nút 'Tắt'.")
            return
        dm_x1, dm_y1 = COMPOSITE_WIDTH - 150, 10
        dm_x2, dm_y2 = COMPOSITE_WIDTH - 10, 50
        if dm_x1 <= x <= dm_x2 and dm_y1 <= y <= dm_y2:
            choose_detection_mode()
            print("Đã chọn phương thức nhận diện:", detection_mode)
            return
        if paused:
            btn_width, btn_height = 200, 60
            c_x1 = (COMPOSITE_WIDTH - btn_width) // 2
            c_y1 = (COMPOSITE_HEIGHT - btn_height) // 2
            c_x2 = c_x1 + btn_width
            c_y2 = c_y1 + btn_height
            if c_x1 <= x <= c_x2 and c_y1 <= y <= c_y2:
                if pending_profile is not None:
                    # Giả sử pending_profile trả về: (ID, HoVaTen, MaSV)
                    id_val = pending_profile[0]
                    ho_va_ten = pending_profile[1]
                    ma_sv = pending_profile[2]
                    current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    write_to_access(PATH_DATABASE, id_val, ma_sv, ho_va_ten, current_time_str)
                    recent_info.insert(0, (ho_va_ten, ma_sv, time.time()))
                    print("Đã xác nhận nhận diện và lưu thông tin!")
                paused = False
                pending_profile = None
                frozen_frame = None
                return

def main():
    global shutdown_flag, recent_info, paused, pending_profile, frozen_frame, detection_mode

    cam = init_camera()
    img_mode_dict = load_images('image')
    for key in ['danhnhandien.png', 'checkingthanhcong.png']:
        if key not in img_mode_dict:
            print(f"Thiếu {key} trong thư mục 'image'.")
            exit()
    img_danh_nhan_dien = img_mode_dict['danhnhandien.png']
    img_checking_thanh_cong = img_mode_dict['checkingthanhcong.png']

    choose_detection_mode()
    print("Phương thức nhận diện ban đầu:", detection_mode)

    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINING_DATA_PATH)
    recent_info = []

    cv2.namedWindow("Face Recognition System")
    cv2.setMouseCallback("Face Recognition System", mouse_callback)

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Không đọc được hình từ camera.")
            break
        if shutdown_flag:
            print("Nhận lệnh tắt.")
            break

        if not paused:
            detection_frame = cv2.resize(frame, (ORIG_WIDTH, ORIG_HEIGHT))
            gray = cv2.cvtColor(detection_frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            recognized = False
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y+h, x:x+w]
                id_pred, confidence = recognizer.predict(roi_gray)
                print("Confidence:", confidence)
                if confidence < 40:
                    profile = db.get_profile(id_pred)
                    if profile:
                        print("Profile nhận được:", profile)
                        if detection_mode == "automatic":
                            # Giả sử profile trả về: (ID, HoVaTen, MaSV)
                            id_val = profile[0]
                            ho_va_ten = profile[1]
                            ma_sv = profile[2]
                            current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            write_to_access(PATH_DATABASE, id_val, ma_sv, ho_va_ten, current_time_str)
                            recent_info.insert(0, (ho_va_ten, ma_sv, time.time()))
                            recognized = True
                            cv2.rectangle(detection_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            break
                        elif detection_mode == "manual":
                            pending_profile = profile
                            recognized = True
                            cv2.rectangle(detection_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            frozen_frame = detection_frame.copy()
                            paused = True
                            break
        else:
            detection_frame = frozen_frame if frozen_frame is not None else cv2.resize(frame, (ORIG_WIDTH, ORIG_HEIGHT))

        display_feed = cv2.resize(detection_frame, (LEFT_DISPLAY_WIDTH, int(ORIG_HEIGHT * scale_factor)))
        left_area = np.full((COMPOSITE_HEIGHT, LEFT_DISPLAY_WIDTH, 3), BACKGROUND_COLOR, dtype=np.uint8)
        feed_height = display_feed.shape[0]
        left_area[0:feed_height, 0:LEFT_DISPLAY_WIDTH] = display_feed
        draw_info_overlay(left_area, 24)

        right_area = np.full((COMPOSITE_HEIGHT, RIGHT_WIDTH, 3), BACKGROUND_COLOR, dtype=np.uint8)
        status_img = img_checking_thanh_cong.copy() if recognized else img_danh_nhan_dien.copy()
        draw_status_area(right_area, status_img)
        draw_shutdown_button(right_area)

        composite = np.hstack((left_area, right_area))
        draw_system_title(composite)
        if recognized:
            notif_text = "Recognition Successful!"
            notif_color = (0, 128, 0)
        else:
            notif_text = "Recognition in Progress!"
            notif_color = (0, 0, 255)
        draw_text_with_shadow(composite, notif_text, (20, 100), 30, notif_color, 2)
        draw_detection_mode_button(composite)
        if paused:
            draw_confirm_button(composite)

        cv2.imshow("Face Recognition System", composite)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
