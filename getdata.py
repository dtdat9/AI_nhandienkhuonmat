import os
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import queryDB as db  # Module tùy chỉnh để xử lý cơ sở dữ liệu

# -------------------- CẤU HÌNH --------------------
DATASET_PATH = 'dataset'
THUMBNAIL_SIZE = (150, 150)  # Kích thước ảnh thu nhỏ khi xem bộ ảnh
COLUMNS_IN_GALLERY = 3       # Số ảnh mỗi hàng trong cửa sổ xem ảnh
MAX_SAMPLE_IMAGES = 20       # Số ảnh tối đa cho mỗi người

# -------------------- CHỨC NĂNG XỬ LÝ --------------------
def save_to_db():
    """Lưu thông tin người dùng vào cơ sở dữ liệu."""
    id_people = entry_id.get().strip()
    name = entry_name.get().strip()
    student_code = entry_student_code.get().strip()

    if not (id_people and name and student_code):
        messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin!")
        return

    try:
        db.insert_or_update(id_people, name, student_code)
        messagebox.showinfo("Thông báo", "Thông tin đã được lưu vào cơ sở dữ liệu!")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi lưu thông tin: {str(e)}")

def start_capture():
    """Bắt đầu chụp ảnh khuôn mặt và lưu vào thư mục dataset."""
    id_people = entry_id.get().strip()
    name = entry_name.get().strip()
    if not id_people or not name:
        messagebox.showwarning("Cảnh báo", "Vui lòng nhập đầy đủ thông tin ID và Tên!")
        return

    # Xác nhận rằng người dùng đã chuẩn bị trước khi chụp ảnh
    ready = messagebox.askyesno("Xác nhận",
        "Trước khi bắt đầu chụp ảnh, hãy đảm bảo:\n"
        "- Ngồi ngay ngắn, đối diện camera\n"
        "- Đủ ánh sáng và không có vật cản\n\n"
        "Bạn đã sẵn sàng?")
    if not ready:
        messagebox.showinfo("Thông báo", "Chức năng chụp ảnh đã bị hủy.")
        return

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        messagebox.showerror("Lỗi", "Không thể mở camera.")
        return

    # Đặt độ phân giải cho camera
    cam.set(3, 1280)
    cam.set(4, 720)

    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    sampleNum = 0

    if not os.path.exists(DATASET_PATH):
        os.makedirs(DATASET_PATH)

    print("[INFO] Bắt đầu chụp ảnh khuôn mặt...")
    while True:
        ret, img = cam.read()
        if not ret:
            messagebox.showerror("Lỗi", "Không thể truy cập camera.")
            break

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            sampleNum += 1
            # Định dạng file: <Tên>.<ID>.<sampleNum>.jpg
            face_filename = os.path.join(DATASET_PATH, f"{name}.{id_people}.{sampleNum}.jpg")
            cv2.imwrite(face_filename, gray[y:y+h, x:x+w])
            print(f"Đã lưu: {face_filename}")

        cv2.imshow("Camera", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if sampleNum >= MAX_SAMPLE_IMAGES:
            messagebox.showinfo("Thông báo", f"Đã lưu đủ {MAX_SAMPLE_IMAGES} ảnh cho người dùng.")
            print("[INFO] Đã lưu đủ ảnh cho người dùng.")
            break

    print("[INFO] Đóng chương trình...")
    cam.release()
    cv2.destroyAllWindows()
    refresh_list()  # Cập nhật lại danh sách trong tab Danh Sách sau khi chụp ảnh

def get_registered_people():
    """
    Quét thư mục dataset và trả về danh sách các người đã đăng ký dạng tuple (ID, Tên).
    Giả sử tên file có định dạng: <Tên>.<ID>.<sampleNum>.jpg
    Sắp xếp theo thứ tự tăng dần của ID.
    """
    registered_people = {}
    if not os.path.exists(DATASET_PATH):
        return []
    for filename in os.listdir(DATASET_PATH):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            parts = filename.split('.')
            if len(parts) >= 3:
                name = parts[0]
                id_people = parts[1]
                registered_people[(id_people, name)] = True
    # Sắp xếp theo ID tăng dần (chuyển sang số nguyên nếu có thể)
    try:
        sorted_people = sorted(list(registered_people), key=lambda x: int(x[0]))
    except ValueError:
        # Nếu ID không phải số thì sắp xếp theo kiểu chuỗi
        sorted_people = sorted(list(registered_people), key=lambda x: x[0])
    return sorted_people

def refresh_list():
    """Cập nhật lại Treeview trong tab Danh Sách."""
    for item in tree.get_children():
        tree.delete(item)
    people = get_registered_people()
    for (id_people, name) in people:
        tree.insert("", "end", values=(id_people, name))

def show_person_images(event):
    """Hiển thị bộ ảnh của người được chọn khi double-click vào mục trong Treeview."""
    selected_item = tree.selection()
    if selected_item:
        item = tree.item(selected_item)
        id_people, name = item['values']
        images = []
        # Lấy danh sách ảnh của người đó
        for filename in os.listdir(DATASET_PATH):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                parts = filename.split('.')
                if len(parts) >= 3:
                    file_name = parts[0]
                    file_id = parts[1]
                    if file_name == name and file_id == str(id_people):
                        images.append(os.path.join(DATASET_PATH, filename))
        if not images:
            messagebox.showinfo("Thông báo", f"Không tìm thấy ảnh cho {name} (ID: {id_people}).")
            return
        # Tạo cửa sổ mới để hiển thị bộ ảnh
        top = tk.Toplevel(root)
        top.title(f"Bộ ảnh của {name} (ID: {id_people})")
        canvas = tk.Canvas(top)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(top, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)
        frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        photos = []  # Lưu tham chiếu ảnh để tránh bị thu gom rác
        row, col = 0, 0
        for img_path in images:
            try:
                pil_img = Image.open(img_path)
                pil_img.thumbnail(THUMBNAIL_SIZE)
                photo = ImageTk.PhotoImage(pil_img)
                photos.append(photo)
                lbl = ttk.Label(frame, image=photo)
                lbl.grid(row=row, column=col, padx=5, pady=5)
                col += 1
                if col >= COLUMNS_IN_GALLERY:
                    col = 0
                    row += 1
            except Exception as e:
                print(f"Lỗi mở ảnh {img_path}: {e}")
        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        top.photos = photos  # Giữ tham chiếu ảnh

# -------------------- GIAO DIỆN CHÍNH --------------------
root = tk.Tk()
root.title("Chương trình Nhận Diện Khuôn Mặt")
root.geometry("600x500")

style = ttk.Style(root)
style.theme_use("clam")  # Sử dụng giao diện chuyên nghiệp, rõ ràng

# Sử dụng Notebook để phân chia các chức năng
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# ----- Tab 1: Đăng Ký -----
tab_register = ttk.Frame(notebook)
notebook.add(tab_register, text="Đăng Ký")

frame_form = ttk.Frame(tab_register, padding=10)
frame_form.pack(fill=tk.X, pady=10)

label_id = ttk.Label(frame_form, text="Nhập ID:")
label_id.grid(row=0, column=0, sticky=tk.W, pady=5)
entry_id = ttk.Entry(frame_form)
entry_id.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

label_name = ttk.Label(frame_form, text="Nhập Tên:")
label_name.grid(row=1, column=0, sticky=tk.W, pady=5)
entry_name = ttk.Entry(frame_form)
entry_name.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)

label_student_code = ttk.Label(frame_form, text="Nhập Mã Sinh Viên:")
label_student_code.grid(row=2, column=0, sticky=tk.W, pady=5)
entry_student_code = ttk.Entry(frame_form)
entry_student_code.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)

frame_form.columnconfigure(1, weight=1)

frame_buttons = ttk.Frame(tab_register, padding=10)
frame_buttons.pack(fill=tk.X)

btn_save = ttk.Button(frame_buttons, text="Lưu Thông Tin", command=save_to_db)
btn_save.grid(row=0, column=0, padx=5, pady=5)

btn_capture = ttk.Button(frame_buttons, text="Bắt Đầu Chụp Ảnh", command=start_capture)
btn_capture.grid(row=0, column=1, padx=5, pady=5)

btn_exit = ttk.Button(frame_buttons, text="Thoát", command=root.quit)
btn_exit.grid(row=0, column=2, padx=5, pady=5)

# ----- Tab 2: Danh Sách -----
tab_list = ttk.Frame(notebook)
notebook.add(tab_list, text="Danh Sách")

frame_list = ttk.Frame(tab_list, padding=10)
frame_list.pack(fill=tk.BOTH, expand=True)

tree = ttk.Treeview(frame_list, columns=("ID", "Tên"), show="headings", selectmode="browse")
tree.heading("ID", text="ID")
tree.heading("Tên", text="Tên")
tree.pack(fill=tk.BOTH, expand=True)

scrollbar_tree = ttk.Scrollbar(frame_list, orient="vertical", command=tree.yview)
tree.configure(yscroll=scrollbar_tree.set)
scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)

btn_refresh = ttk.Button(tab_list, text="Làm mới danh sách", command=refresh_list)
btn_refresh.pack(pady=5)

# Ràng buộc sự kiện double-click để xem bộ ảnh của người được chọn
tree.bind("<Double-1>", show_person_images)

# Khởi tạo danh sách ngay khi chạy
refresh_list()

root.mainloop()
