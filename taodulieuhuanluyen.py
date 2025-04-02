# -*- coding: utf-8 -*-
import os
import cv2
import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# ---------------------- CẤU HÌNH ----------------------
dataset_path = 'dataset'  # Thư mục chứa ảnh khuôn mặt huấn luyện
recognizer_save_path = 'recognizer/trainingData.yml'

# ---------------------- KHỞI TẠO NHẬN DẠNG ----------------------
recognizer = cv2.face.LBPHFaceRecognizer_create()


# ---------------------- HÀM LẤY ẢNH VÀ ID ----------------------
def getImagesAndLabels(path, progress_callback=None):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    faces, IDs = [], []
    total = len(imagePaths)

    for idx, imagePath in enumerate(imagePaths, start=1):
        try:
            faceImg = Image.open(imagePath).convert('L')
            faceNp = np.array(faceImg, 'uint8')
            # Giả sử tên file định dạng "user.1.jpg" -> lấy ID ở phần tử thứ 2
            filename = os.path.split(imagePath)[-1]
            parts = filename.split('.')
            if len(parts) >= 3:
                ID = int(parts[1])
                faces.append(faceNp)
                IDs.append(ID)
        except Exception as e:
            # Bỏ qua ảnh không hợp lệ
            print(f"Lỗi với file {imagePath}: {e}")
            continue

        if progress_callback:
            progress_callback(idx, total)

    return IDs, faces


# ---------------------- HÀM HUẤN LUYỆN ----------------------
def trainData(progress_callback):
    IDs, faces = getImagesAndLabels(dataset_path, progress_callback)
    if faces and IDs:
        recognizer.train(faces, np.array(IDs))
        os.makedirs(os.path.dirname(recognizer_save_path), exist_ok=True)
        recognizer.save(recognizer_save_path)


# ---------------------- HUẤN LUYỆN TRONG LUỒNG RIÊNG ----------------------
def start_training(progress_bar, percent_label, start_button):
    start_button.config(state=tk.DISABLED)

    def update_progress(current, total):
        progress_bar["value"] = current
        percent = int((current / total) * 100)
        percent_label.config(text=f"{percent}%")
        progress_bar.update_idletasks()

    def task():
        trainData(update_progress)
        start_button.config(state=tk.NORMAL)
        # Hiển thị thông báo thành công
        messagebox.showinfo("Thông báo", "Đã huấn luyện và lưu dữ liệu thành công!")

    threading.Thread(target=task, daemon=True).start()


# ---------------------- GIAO DIỆN HUẤN LUYỆN ----------------------
def create_gui():
    root = tk.Tk()
    root.title("Huấn luyện Nhận dạng Khuôn mặt")
    root.geometry("600x300")
    root.option_add("*Font", "Arial 12")

    title_label = ttk.Label(root, text="Huấn luyện Nhận dạng Khuôn mặt", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)

    progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate")
    progress_bar.pack(fill=tk.X, padx=20, pady=10)

    percent_label = ttk.Label(root, text="0%")
    percent_label.pack(pady=(0, 10))

    start_button = ttk.Button(root, text="Bắt đầu huấn luyện",
                              command=lambda: start_training(progress_bar, percent_label, start_button))
    start_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    create_gui()
