# -*- coding: utf-8 -*-
import os
import cv2
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import shutil
# ---------------------- ĐƯỜNG DẪN ----------------------
BASE_DIR = "D:/Study/Nam3/NCKH/okok"

PATH_DATASET = os.path.join(BASE_DIR, "dataset")
PATH_RECOGNIZER = os.path.join(BASE_DIR, "recognizer/trainingData.yml")
PATH_DATABASE = os.path.join(BASE_DIR, "dulieudiemdanh.accdb")
PATH_DATABASE_TEMPLATE = os.path.join(BASE_DIR, "dulieudiemdanh_template.accdb")

# ---------------------- HÀM GỌI CÁC MODULE ----------------------
def tao_thong_tin():
    subprocess.run(["python", os.path.join(BASE_DIR, "getdata.py")])

def tao_chuong_trinh_huan_luyen():
    subprocess.run(["python", os.path.join(BASE_DIR, "taodulieuhuanluyen.py")])

def nhan_dien_khuon_mat():
    subprocess.run(["python", os.path.join(BASE_DIR, "nhandien.py")])

def xem_thong_tin_diem_danh():
    try:
        # Mở file Access (accdb) bằng ứng dụng mặc định (Access hoặc công cụ tương thích)
        os.startfile(PATH_DATABASE)
    except FileNotFoundError:
        print("File dulieudiemdanh.accdb không tồn tại.")

def reset_toan_bo():
    # Yêu cầu xác nhận trước khi reset toàn bộ dữ liệu
    confirm_reset = messagebox.askyesno("Xác nhận Reset",
        "Bạn có chắc chắn muốn reset toàn bộ dữ liệu?\n"
        "Cơ sở dữ liệu hiện tại sẽ được backup với tên 'dulieudiemdanh_backupp.accdb'.")
    if not confirm_reset:
        messagebox.showinfo("Hủy Reset", "Chức năng reset đã bị hủy.")
        return

    # Backup cơ sở dữ liệu hiện tại trước khi reset
    try:
        if os.path.exists(PATH_DATABASE):
            backup_path = os.path.join(os.path.dirname(PATH_DATABASE), "dulieudiemdanh_backupp.accdb")
            shutil.copy(PATH_DATABASE, backup_path)
            print(f"Đã backup cơ sở dữ liệu thành công tại {backup_path}")
            messagebox.showinfo("Backup thành công", f"Cơ sở dữ liệu đã được backup tại:\n{backup_path}")
        else:
            messagebox.showwarning("Backup", "Không tìm thấy cơ sở dữ liệu để backup.")
    except Exception as e:
        messagebox.showerror("Lỗi Backup", f"Lỗi khi backup cơ sở dữ liệu: {e}")
        return

    # Xóa tất cả ảnh trong thư mục dataset
    try:
        for filename in os.listdir(PATH_DATASET):
            file_path = os.path.join(PATH_DATASET, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("Đã xóa tất cả ảnh trong thư mục dataset.")
    except Exception as e:
        print(f"Lỗi khi xóa ảnh trong dataset: {e}")

    # Xóa file trainingData.yml
    try:
        if os.path.exists(PATH_RECOGNIZER):
            os.remove(PATH_RECOGNIZER)
            print("Đã xóa file trainingData.yml.")
    except Exception as e:
        print(f"Lỗi khi xóa file trainingData.yml: {e}")

    # Reset cơ sở dữ liệu Access:
    try:
        if os.path.exists(PATH_DATABASE):
            os.remove(PATH_DATABASE)
            print("Đã xóa file dulieudiemdanh.accdb.")
        # Tạo lại file Access từ file template
        shutil.copy(PATH_DATABASE_TEMPLATE, PATH_DATABASE)
        print("Đã tạo lại file dulieudiemdanh.accdb từ template.")
    except Exception as e:
        print(f"Lỗi khi reset cơ sở dữ liệu Access: {e}")

    # Đóng tất cả cửa sổ OpenCV
    cv2.destroyAllWindows()
    print("Đã reset camera và giao diện.")

    # Hiển thị thông báo đã reset trên màn hình
    messagebox.showinfo("Reset", "Đã reset toàn bộ dữ liệu!")

# ---------------------- GIAO DIỆN CHÍNH ----------------------
def main():
    root = tk.Tk()
    root.title("Chương trình nhận diện khuôn mặt")
    root.geometry("500x400")
    root.resizable(False, False)
    try:
        # Căn giữa cửa sổ nếu hệ điều hành hỗ trợ
        root.eval('tk::PlaceWindow . center')
    except Exception:
        pass

    # Sử dụng ttk với giao diện màu đơn giản
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TButton', font=('Helvetica', 12), padding=10)
    style.configure('TLabel', font=('Times New Roman', 16, 'bold'))

    # Tạo khung chính và căn giữa nội dung
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(expand=True, fill='both')
    main_frame.columnconfigure(0, weight=1)

    # Tiêu đề ứng dụng, căn giữa
    title_label = ttk.Label(main_frame, text="Chương trình nhận diện khuôn mặt", anchor="center")
    title_label.grid(row=0, column=0, pady=(0, 20))

    # Đặt kích thước button cố định để các button bằng nhau
    btn_width = 30

    btn_tao_thong_tin = ttk.Button(main_frame, text="Quản Lý Thông Tin", command=tao_thong_tin, width=btn_width)
    btn_tao_thong_tin.grid(row=1, column=0, sticky='ew', padx=5, pady=5)

    btn_tao_chuong_trinh = ttk.Button(main_frame, text="Tạo Chương Trình Huấn Luyện", command=tao_chuong_trinh_huan_luyen, width=btn_width)
    btn_tao_chuong_trinh.grid(row=2, column=0, sticky='ew', padx=5, pady=5)

    btn_nhan_dien = ttk.Button(main_frame, text="Nhận Diện Khuôn Mặt", command=nhan_dien_khuon_mat, width=btn_width)
    btn_nhan_dien.grid(row=3, column=0, sticky='ew', padx=5, pady=5)

    btn_xem_thong_tin = ttk.Button(main_frame, text="Xem Thông Tin Điểm Danh", command=xem_thong_tin_diem_danh, width=btn_width)
    btn_xem_thong_tin.grid(row=4, column=0, sticky='ew', padx=5, pady=5)

    btn_reset = ttk.Button(main_frame, text="Reset Toàn Bộ", command=reset_toan_bo, width=btn_width)
    btn_reset.grid(row=5, column=0, sticky='ew', padx=5, pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
