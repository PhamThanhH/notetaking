from tkinter import *
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import json
import os
import hashlib
import uuid

# ==== FILES ====
users_file = "users.json"
notes_file = "notes.json"
notes_ids = []
selected_index = 0
current_user = None
current_role = None

# ==== UTILS ====
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(users_file):
        users = []
    else:
        try:
            with open(users_file, "r", encoding="utf-8-sig") as f:
                users = json.load(f)
        except json.JSONDecodeError:
            users = []

    if not any(user["username"] == "admin" for user in users):
        users.append({
            "username": "admin",
            "password": hash_password("admin123"),
            "role": "admin"
        })
        save_users(users)

    return users

def save_users(users):
    with open(users_file, "w", encoding="utf-8-sig") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def load_notes():
    global notes_ids
    if not os.path.exists(notes_file):
        return []
    try:
        with open(notes_file, "r", encoding="utf-8-sig") as f:
            notes = json.load(f)
    except json.JSONDecodeError:
        notes = []

    notes_ids.clear()
    if current_role == "admin":
        filtered_notes = notes
    else:
        filtered_notes = [note for note in notes if note.get("owner") == current_user]
    notes_ids.extend([note["id"] for note in filtered_notes])
    return filtered_notes

def save_notes(notes):
    with open(notes_file, "w", encoding="utf-8-sig") as f:
        json.dump(notes, f, indent=4, ensure_ascii=False)

def get_note_by_id(note_id):
    try:
        with open(notes_file, "r", encoding="utf-8-sig") as f:
            notes = json.load(f)
    except json.JSONDecodeError:
        return None
    for note in notes:
        if note['id'] == note_id:
            return note
    return None

# ==== DELETE USER ====
def delete_user(username, refresh_callback=None):
    global current_user, current_role
    if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa tài khoản '{username}' và tất cả ghi chú liên quan không?"):
        return

    users = load_users()
    users = [user for user in users if user['username'] != username]
    save_users(users)

    if os.path.exists(notes_file):
        try:
            with open(notes_file, "r", encoding="utf-8-sig") as f:
                notes = json.load(f)
        except json.JSONDecodeError:
            notes = []
        notes = [note for note in notes if note.get("owner") != username]
        save_notes(notes)

    if current_user == username:
        logout()

    messagebox.showinfo("Xóa người dùng", f"Đã xóa người dùng '{username}' và các ghi chú liên quan.")
    if refresh_callback:
        refresh_callback()

# ==== REGISTER ====
def register():
    register_window = Toplevel()
    register_window.title("Đăng Ký")
    register_window.geometry("400x250")
    register_window.resizable(False, False)

    try:
        bg_label = Label(register_window, image=background_img)
        bg_label.place(relwidth=1, relheight=1)
    except NameError:
        register_window.configure(bg="white")

    Label(register_window, text="Tài khoản:", font=("Helvetica", 12), bg="#ffffff").place(x=150, y=30)
    entry_user = Entry(register_window, font=("Helvetica", 12), width=30)
    entry_user.place(x=80, y=60)

    Label(register_window, text="Mật khẩu:", font=("Helvetica", 12), bg="#ffffff").place(x=150, y=100)
    entry_pass = Entry(register_window, show="*", font=("Helvetica", 12), width=30)
    entry_pass.place(x=80, y=130)

    def save_register():
        username = entry_user.get().strip()
        password = entry_pass.get()
        if not username or not password:
            messagebox.showerror("Lỗi", "Không được để trống")
            return
        if username.lower() == "admin":
            messagebox.showerror("Lỗi", "Không thể đăng ký tài khoản 'admin'")
            return
        users = load_users()
        for user in users:
            if user["username"] == username:
                messagebox.showerror("Lỗi", "Tài khoản đã tồn tại")
                return
        users.append({"username": username, "password": hash_password(password), "role": "user"})
        save_users(users)
        messagebox.showinfo("Thành công", "Đăng ký thành công")
        register_window.destroy()

    Button(register_window, text="Đăng ký", font=("Helvetica", 12), command=save_register).place(x=160, y=180)

# ==== LOGIN ====
def login():
    global current_user, current_role
    username = user_entry.get()
    password = pass_entry.get()
    users = load_users()
    for user in users:
        if user["username"] == username and user["password"] == hash_password(password):
            current_user = user["username"]
            current_role = user.get("role", "user")
            login_window.withdraw()
            show_note_app()
            return
    messagebox.showerror("Lỗi", "Sai tài khoản hoặc mật khẩu")

# ==== LOGOUT ====
def logout():
    global current_user, current_role
    current_user = None
    current_role = None
    window.withdraw()
    user_entry.delete(0, END)
    pass_entry.delete(0, END)
    login_window.deiconify()

# ==== ADMIN PANEL ====
def show_admin_panel(frame):
    for widget in frame.winfo_children():
        widget.destroy()

    users = load_users()
    row = 0
    for user in users:
        if user['username'] == 'admin':
            continue
        def make_view_button(u):
            return Button(frame, text="Xem ghi chú", command=lambda: view_user_notes(u))
        Label(frame, text=user['username'], font=("Helvetica", 12)).grid(row=row, column=0, padx=-0, pady=2)
        Button(frame, text="Xóa tài khoản", command=lambda u=user['username']: delete_user(u, lambda: show_admin_panel(frame))).grid(row=row, column=1, padx=5)
        make_view_button(user['username']).grid(row=row, column=2, padx=5)
        row += 1

# ==== XEM GHI CHÚ NGƯỜI DÙNG (ADMIN) ====
def view_user_notes(username):
    notes = []
    if os.path.exists(notes_file):
        try:
            with open(notes_file, "r", encoding="utf-8-sig") as f:
                all_notes = json.load(f)
                notes = [note for note in all_notes if note.get("owner") == username]
        except json.JSONDecodeError:
            notes = []

    view_window = Toplevel()
    view_window.title(f"Ghi chú của {username}")
    view_window.geometry("400x300")

    listbox = Listbox(view_window, font=("Helvetica", 12))
    listbox.pack(fill=BOTH, expand=True, padx=0, pady=0)

    for note in notes:
        listbox.insert(END, f"[{note['id']}] {note['title']}")

    def show_note_content(event):
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            note = notes[index]

            content_window = Toplevel()
            content_window.title(f"Nội dung ghi chú: {note['title']}")
            content_window.geometry("400x300")

            text_area = Text(content_window, wrap=WORD, font=("Helvetica", 12))
            text_area.pack(fill=BOTH,side=TOP, expand=True, padx=0, pady=0)
            text_area.insert(END, note.get("content", "Không có nội dung"))
            text_area.config(state=DISABLED)

            def delete_this_note():
                if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa ghi chú này không?"):
                    try:
                        with open(notes_file, "r", encoding="utf-8-sig") as f:
                            all_notes = json.load(f)
                    except json.JSONDecodeError:
                        all_notes = []
                    all_notes = [n for n in all_notes if n["id"] != note["id"]]
                    save_notes(all_notes)
                    messagebox.showinfo("Đã xóa", "Ghi chú đã được xóa.")
                    content_window.destroy()
                    view_window.destroy()
                    view_user_notes(username)

            Button(content_window, text="Xóa ghi chú này", fg="red", command=delete_this_note).pack(pady=5)

    listbox.bind("<Double-1>", show_note_content)


# ==== MAIN UI ====
def show_note_app():
    window.deiconify()
    window.title("Ứng dụng Ghi chú")
    window.geometry("1000x500")

    top_frame = Frame(window)
    scroll_list = Scrollbar(top_frame)
    scroll_list.pack(side=RIGHT)

    global list_notes, note_title, note_text, btn_edit, btn_delete
    list_notes = Listbox(top_frame, height=15, width=40)
    list_notes.bind('<<ListboxSelect>>', onselect)
    list_notes.pack(side=LEFT, padx=(0, 0), pady=(0, 2))
    scroll_list.config(command=list_notes.yview)
    list_notes.config(yscrollcommand=scroll_list.set, cursor="hand2", bg="#fff5e6",
                      highlightbackground="grey", bd=0, selectbackground="#c9b922")
    top_frame.pack(side=LEFT, padx=(0, 5))

    right_frame = Frame(window)
    note_title = Entry(right_frame, width=39, font="Helvetica 13")
    note_title.insert(END, "Title")
    note_title.config(background="#F4F6F7", highlightbackground="grey")
    note_title.pack(side=TOP, pady=(0, 5), padx=(0, 2))

    scroll_text = Scrollbar(right_frame)
    scroll_text.pack(side=RIGHT)
    note_text = Text(right_frame, height=7, width=40, font="Helvetica 13")
    note_text.pack(side=TOP, padx=(0, 2), pady=(0, 5))
    note_text.insert(END, "Notes")
    scroll_text.config(command=note_text.yview)
    note_text.config(yscrollcommand=scroll_text.set, bg="#F4F6F7", highlightbackground="grey")

    button_frame = Frame(right_frame)
    btn_add = Button(button_frame, text="Add", command=save_note, image=photo_add)
    btn_edit = Button(button_frame, text="Update", command=update_note, state=DISABLED, image=photo_edit)
    btn_delete = Button(button_frame, text="Delete", command=delete_note, state=DISABLED, image=photo_delete)
    btn_logout = Button(button_frame, text="Đăng Xuất", command=logout)
    btn_add.grid(row=0, column=0, padx=2)
    btn_edit.grid(row=0, column=1, padx=2)
    btn_delete.grid(row=0, column=2, padx=2)
    btn_logout.grid(row=0, column=3, padx=2)
    button_frame.pack(pady=2)

    right_frame.pack(side=LEFT, fill=BOTH)

    if current_role == "admin":
        bottom_frame = Frame(window)
        bottom_frame.pack(side=BOTTOM)

        admin_frame = Frame(bottom_frame, bd=1, relief=SUNKEN)
        admin_frame.pack(padx=3, pady=0)


        Label(admin_frame, text="Tài khoản người dùng:", font=("Helvetica", 14, "bold")).pack(pady=(1, 0))
        user_list = Listbox(admin_frame, font=("Helvetica", 12), width=20, height=5)
        user_list.pack(padx=0, side=BOTTOM, pady=0, expand=True)
        for user in load_users():
            if user["username"] != "admin":
                user_list.insert(END, user["username"])

        def delete_user():
            selected_user_idx = user_list.curselection()
            if not selected_user_idx:
                messagebox.showerror("Lỗi", "Vui lòng chọn tài khoản để xoá")
                return
            username_to_delete = user_list.get(selected_user_idx)
            if messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn xoá tài khoản '{username_to_delete}'?"):
                users = load_users()
                users = [u for u in users if u["username"] != username_to_delete]
                save_users(users)
                if os.path.exists(notes_file):
                    with open(notes_file, "r", encoding="utf-8-sig") as f:
                        notes = json.load(f)
                    notes = [n for n in notes if n["owner"] != username_to_delete]
                    save_notes(notes)
                user_list.delete(selected_user_idx)
                if current_user != username_to_delete:
                    init_notes()
                messagebox.showinfo("Thành công", f"Đã xoá tài khoản '{username_to_delete}'")

        Button(admin_frame, text="Xoá tài khoản", command=delete_user).pack(pady=0)
        admin_frame.pack(side=LEFT, fill=X, padx=0, pady=0)

    init_notes()

# ==== NOTE ACTIONS ====
def init_notes():
    list_notes.delete(0, END)
    notes = load_notes()
    for note in notes:
        list_notes.insert(END, note['title'])

def onselect(evt):
    global selected_index
    if not list_notes.curselection():
        return
    selected_index = int(list_notes.curselection()[0])
    display_note(selected_index)

def display_note(index):
    note_title.delete(0, END)
    note_text.delete('1.0', END)
    note_id = notes_ids[index]
    note = get_note_by_id(note_id)
    if note:
        note_title.insert(END, note['title'])
        note_text.insert(END, note['note'])
    btn_edit.config(state=NORMAL)
    btn_delete.config(state=NORMAL)

def save_note():
    title = note_title.get().strip()
    content = note_text.get("1.0", END).strip()
    if not title or not content:
        messagebox.showerror("Lỗi", "Bạn phải nhập tiêu đề và nội dung")
        return
    notes = load_notes()
    for n in notes:
        if n["title"] == title and current_role == "user":
            messagebox.showerror("Lỗi", "Tiêu đề đã tồn tại")
            return
    all_notes = []
    if os.path.exists(notes_file):
        with open(notes_file, "r", encoding="utf-8-sig") as f:
            all_notes = json.load(f)
    new_id = max([n['id'] for n in all_notes], default=0) + 1
    new_note = {
        "id": new_id,
        "title": title,
        "note": content,
        "owner": current_user
    }
    all_notes.append(new_note)
    save_notes(all_notes)
    list_notes.insert(END, title)
    notes_ids.append(new_note['id'])
    # Xóa trắng phần nhập để người dùng có thể nhập ghi chú tiếp
    note_title.delete(0, END)
    note_text.delete('1.0', END)
    note_title.focus_set()
    # Vô hiệu hóa nút sửa và xóa vì chưa chọn ghi chú nào
    btn_edit.config(state=DISABLED)
    btn_delete.config(state=DISABLED)

def update_note():
    global selected_index
    title = note_title.get().strip()
    content = note_text.get("1.0", END).strip()
    if not title or not content:
        messagebox.showerror("Lỗi", "Bạn phải nhập tiêu đề và nội dung")
        return
    note_id = notes_ids[selected_index]
    with open(notes_file, "r", encoding="utf-8-sig") as f:
        notes = json.load(f)
    for n in notes:
        if n['id'] == note_id:
            if current_role != "admin" and n['owner'] != current_user:
                messagebox.showerror("Lỗi", "Bạn không có quyền sửa ghi chú này")
                return
            n['title'] = title
            n['note'] = content
            break
    save_notes(notes)
    list_notes.delete(selected_index)
    list_notes.insert(selected_index, title)

    # Xóa trắng phần nhập để nhập tiếp
    note_title.delete(0, END)
    note_text.delete('1.0', END)
    note_title.focus_set()

    # Vô hiệu hóa nút sửa và xóa vì chưa chọn ghi chú nào
    btn_edit.config(state=DISABLED)
    btn_delete.config(state=DISABLED)


def delete_note():
    global selected_index
    if not list_notes.curselection():
        messagebox.showerror("Lỗi", "Bạn chưa chọn ghi chú")
        return
    if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn xoá ghi chú này?"):
        note_id = notes_ids[selected_index]
        with open(notes_file, "r", encoding="utf-8-sig") as f:
            notes = json.load(f)
        for note in notes:
            if note["id"] == note_id:
                if current_role != "admin" and note["owner"] != current_user:
                    messagebox.showerror("Lỗi", "Bạn không có quyền xoá ghi chú này")
                    return
        notes = [n for n in notes if n['id'] != note_id]
        save_notes(notes)
        del notes_ids[selected_index]
        list_notes.delete(selected_index)
        note_title.delete(0, END)
        note_text.delete('1.0', END)
        btn_edit.config(state=DISABLED)
        btn_delete.config(state=DISABLED)

# ==== MAIN WINDOW ====
window = tk.Tk()
window.withdraw()

bg_img_raw = Image.open("background.png")
bg_img_resized = bg_img_raw.resize((400, 250))
background_img = ImageTk.PhotoImage(bg_img_resized)

photo_add = PhotoImage(file="add.gif")
photo_edit = PhotoImage(file="edit.gif")
photo_delete = PhotoImage(file="delete.gif")

login_window = Toplevel(window)
login_window.title("Đăng Nhập")
login_window.geometry("400x250")
login_window.resizable(False, False)

bg_label_login = Label(login_window, image=background_img)
bg_label_login.place(relwidth=1, relheight=1)

Label(login_window, text="Tài khoản:", font=("Helvetica", 12), bg="#ffffff").place(x=150, y=30)
user_entry = Entry(login_window, font=("Helvetica", 12), width=30)
user_entry.place(x=80, y=60)

Label(login_window, text="Mật khẩu:", font=("Helvetica", 12), bg="#ffffff").place(x=150, y=100)
pass_entry = Entry(login_window, show="*", font=("Helvetica", 12), width=30)
pass_entry.place(x=80, y=130)

Button(login_window, text="Đăng Nhập", font=("Helvetica", 12), command=login).place(x=150, y=170)
Button(login_window, text="Đăng Ký", font=("Helvetica", 12), command=register).place(x=155, y=200)

# ==== RUN ====
window.mainloop()
