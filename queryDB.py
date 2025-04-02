import sqlite3
import datetime
from tkinter import messagebox


# Hàm kết nối với cơ sở dữ liệu
def connect_database():
    try:
        # Kết nối tới tệp cơ sở dữ liệu SQLite
        conn = sqlite3.connect('attendance.db')
        return conn
    except sqlite3.Error as err:
        print(f"Error: {err}")
        return None


# Hàm xử lý check-in và check-out
def check_in_and_checkout(id_people):
    # Lấy thời gian hiện tại
    cur_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cur_date = datetime.datetime.now().strftime('%Y-%m-%d')

    # Kết nối cơ sở dữ liệu
    conn = connect_database()
    if not conn:
        messagebox.showerror("Database Error", "Could not connect to the database.")
        return None

    cursor = conn.cursor()

    # Truy vấn để kiểm tra xem đã có dữ liệu check-in trong ngày chưa
    query = "SELECT * FROM attendance WHERE idPeople = ? AND DATE(timeCheckIn) = ?"
    cursor.execute(query, (id_people, cur_date))
    records = cursor.fetchall()

    # Biến để kiểm tra xem đã có bản ghi nào cho người dùng trong ngày chưa
    is_record_exist = len(records) > 0

    # Nếu chưa có bản ghi nào, thực hiện check-in
    if not is_record_exist:
        query = "INSERT INTO attendance (idPeople, timeCheckIn, timeCheckOut) VALUES (?, ?, ?)"
        cursor.execute(query, (id_people, cur_time, None))
        check = True
        print("Check-in successful.")
    # Nếu đã có bản ghi, thực hiện check-out
    else:
        query = "UPDATE attendance SET timeCheckOut = ? WHERE idPeople = ? AND DATE(timeCheckIn) = ?"
        cursor.execute(query, (cur_time, id_people, cur_date))
        check = False
        print("Check-out successful.")

    # Lưu thay đổi và đóng kết nối
    conn.commit()
    cursor.close()
    conn.close()
    return check


# Hàm tìm kiếm thông tin người dùng theo ID
def get_profile(id_people):
    conn = connect_database()
    if not conn:
        messagebox.showerror("Database Error", "Could not connect to the database.")
        return None

    cursor = conn.cursor()
    query = "SELECT * FROM people WHERE id = ?"
    cursor.execute(query, (id_people,))
    records = cursor.fetchall()

    profile = None
    if records:
        profile = records[0]

    # Đóng kết nối
    cursor.close()
    conn.close()
    return profile


# Hàm thêm hoặc cập nhật thông tin người dùng
def insert_or_update(id_people, name, student_code):
    conn = connect_database()
    if not conn:
        messagebox.showerror("Database Error", "Could not connect to the database.")
        return None

    cursor = conn.cursor()

    # Kiểm tra xem bản ghi đã tồn tại hay chưa
    cursor.execute("SELECT * FROM people WHERE id = ?", (id_people,))
    record = cursor.fetchone()

    if record:
        # Nếu bản ghi tồn tại, cập nhật thông tin
        cursor.execute("UPDATE people SET name = ?, student_code = ? WHERE id = ?", (name, student_code, id_people))
        print(f"Cập nhật tên và mã sinh viên cho ID {id_people}: {name}, {student_code}")
    else:
        # Nếu bản ghi không tồn tại, thêm mới
        cursor.execute("INSERT INTO people (id, name, student_code) VALUES (?, ?, ?)", (id_people, name, student_code))
        print(f"Thêm mới người với ID {id_people}: {name}, {student_code}")

    # Lưu thay đổi và đóng kết nối
    conn.commit()
    cursor.close()
    conn.close()
