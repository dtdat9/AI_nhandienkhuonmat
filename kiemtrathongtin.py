import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

# ----------------- CẤU HÌNH -----------------
dataset_path = 'dataset'  # Thư mục chứa ảnh
thumbnail_size = (150, 150)  # Kích thước ảnh thu nhỏ
columns_in_gallery = 3  # Số ảnh mỗi hàng trong cửa sổ xem ảnh


# ----------------- HÀM HỖ TRỢ -----------------
def get_registered_people():
    """
    Quét thư mục dataset và trả về danh sách các người đã đăng ký dạng tuple (ID, Tên)
    Giả sử tên file có định dạng: Tên.ID.xxx.png
    """
    registered_people = set()
    if not os.path.exists(dataset_path):
        messagebox.showwarning("Thông báo", "Thư mục dataset không tồn tại.")
        return []

    for filename in os.listdir(dataset_path):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        parts = filename.split('.')
        if len(parts) >= 3:
            name = parts[0]
            person_id = parts[1]
            registered_people.add((person_id, name))
    # Sắp xếp theo tên và sau đó ID
    return sorted(list(registered_people), key=lambda x: (x[1], x[0]))


def get_images_for_person(person):
    """
    Trả về danh sách đường dẫn ảnh của người có thông tin (ID, Tên)
    """
    person_id, name = person
    image_files = []
    for filename in os.listdir(dataset_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            parts = filename.split('.')
            if len(parts) >= 3:
                file_name = parts[0]
                file_id = parts[1]
                if file_name == name and file_id == person_id:
                    image_files.append(os.path.join(dataset_path, filename))
    return image_files


def show_person_images(person):
    """
    Mở cửa sổ mới hiển thị bộ ảnh của người được chọn dưới dạng ảnh thu nhỏ.
    """
    person_id, name = person
    image_paths = get_images_for_person(person)

    if not image_paths:
        messagebox.showinfo("Thông báo", f"Không tìm thấy ảnh nào của {name} (ID: {person_id}).")
        return

    # Tạo cửa sổ Toplevel để hiển thị bộ ảnh
    top = tk.Toplevel()
    top.title(f"Bộ ảnh của {name} (ID: {person_id})")

    # Khung chứa các ảnh
    gallery_frame = ttk.Frame(top, padding=10)
    gallery_frame.pack(fill=tk.BOTH, expand=True)

    # Danh sách để lưu giữ tham chiếu ảnh (tránh bị thu gom rác)
    top.image_refs = []

    row, col = 0, 0
    for img_path in image_paths:
        try:
            pil_img = Image.open(img_path)
            pil_img.thumbnail(thumbnail_size)
            photo = ImageTk.PhotoImage(pil_img)
        except Exception as e:
            print(f"Lỗi mở ảnh {img_path}: {e}")
            continue

        lbl = ttk.Label(gallery_frame, image=photo)
        lbl.grid(row=row, column=col, padx=5, pady=5)
        top.image_refs.append(photo)  # Lưu tham chiếu

        col += 1
        if col >= columns_in_gallery:
            col = 0
            row += 1


def on_listbox_double_click(event):
    """
    Xử lý sự kiện double-click trên listbox.
    Phân tích chuỗi để lấy ID và tên, sau đó gọi hàm hiển thị bộ ảnh.
    """
    widget = event.widget
    selection = widget.curselection()
    if selection:
        index = selection[0]
        item_text = widget.get(index)  # Định dạng: "ID: {id}, Tên: {name}"
        try:
            parts = item_text.split(',')
            person_id = parts[0].split(':')[1].strip()
            name = parts[1].split(':')[1].strip()
            show_person_images((person_id, name))
        except Exception as e:
            print(f"Lỗi phân tích chuỗi '{item_text}': {e}")


# ----------------- GIAO DIỆN CHÍNH -----------------
def create_main_window():
    root = tk.Tk()
    root.title("Danh sách khuôn mặt đã đăng ký")
    root.geometry("400x400")

    # Khung chính với padding
    main_frame = ttk.Frame(root, padding=10)
    main_frame.pack(fill=tk.BOTH, expand=True)

    title_label = ttk.Label(
        main_frame,
        text="Danh sách những người đã đăng ký khuôn mặt",
        font=("Helvetica", 14, "bold")
    )
    title_label.pack(pady=10)

    # Listbox để hiển thị danh sách người dùng
    listbox = tk.Listbox(main_frame, font=("Helvetica", 12))
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    people = get_registered_people()
    if not people:
        listbox.insert(tk.END, "Không có dữ liệu người dùng nào.")
    else:
        for person in people:
            person_id, name = person
            listbox.insert(tk.END, f"ID: {person_id}, Tên: {name}")

    # Ràng buộc sự kiện double-click để mở cửa sổ xem ảnh
    listbox.bind("<Double-Button-1>", on_listbox_double_click)

    root.mainloop()


# ----------------- CHẠY CHƯƠNG TRÌNH -----------------
if __name__ == "__main__":
    create_main_window()
