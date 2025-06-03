from tkinter import *
import tkinter as tk
from tkinter import messagebox
import json
import os

notes_ids = []
selected_index = 0
json_file = "notes.json"

# ===== JSON FUNCTIONS =====
def load_notes_from_json():
    global notes_ids
    if not os.path.exists(json_file):
        return []
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        notes_ids = [note['id'] for note in data]
        return data

def save_notes_to_json(notes_data):
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(notes_data, f, indent=4, ensure_ascii=False)

def get_note_by_id(note_id):
    notes = load_notes_from_json()
    for note in notes:
        if note['id'] == note_id:
            return note
    return None

# ===== UI SETUP =====
window = tk.Tk()
window.title("Note Taking App")

top_frame = tk.Frame(window)
scroll_list = tk.Scrollbar(top_frame)
scroll_list.pack(side=tk.RIGHT, fill=tk.Y)

list_notes = Listbox(top_frame, height=15, width=40)
list_notes.bind('<<ListboxSelect>>', lambda evt: onselect(evt))
list_notes.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0), pady=(10, 10))
scroll_list.config(command=list_notes.yview)
list_notes.config(yscrollcommand=scroll_list.set, cursor="hand2", background="#fff5e6",
                  highlightbackground="grey", bd=0, selectbackground="#c9b922")
top_frame.pack(side=tk.TOP, padx=(0, 5))

text_frame = tk.Frame(window)
note_title = tk.Entry(text_frame, width=39, font="Helvetica 13")
note_title.insert(tk.END, "Title")
note_title.config(background="#F4F6F7", highlightbackground="grey")
note_title.pack(side=tk.TOP, pady=(0, 5), padx=(0, 10))

scroll_text = tk.Scrollbar(text_frame)
scroll_text.pack(side=tk.RIGHT, fill=tk.Y)
note_text = tk.Text(text_frame, height=7, width=40, font="Helvetica 13")
note_text.pack(side=tk.TOP, fill=tk.Y, padx=(5, 0), pady=(0, 5))
note_text.tag_config("tag_your_message", foreground="blue")
note_text.insert(tk.END, "Notes")
scroll_text.config(command=note_text.yview)
note_text.config(yscrollcommand=scroll_text.set, background="#F4F6F7", highlightbackground="grey")
text_frame.pack(side=tk.TOP)

button_frame = tk.Frame(window)
photo_add = PhotoImage(file="add.gif")
photo_edit = PhotoImage(file="edit.gif")
photo_delete = PhotoImage(file="delete.gif")

btn_save = tk.Button(button_frame, text="Add", command=lambda: save_note(), image=photo_add)
btn_edit = tk.Button(button_frame, text="Update", command=lambda: update_note(), state=tk.DISABLED, image=photo_edit)
btn_delete = tk.Button(button_frame, text="Delete", command=lambda: delete_note(), state=tk.DISABLED, image=photo_delete)

# ===== NÚT MỚI: LƯU DỮ LIỆU VÀO JSON =====
def manual_save_to_json():
    notes = []
    for idx in range(len(notes_ids)):
        note = get_note_by_id(notes_ids[idx])
        if note:
            notes.append(note)
    save_notes_to_json(notes)
    tk.messagebox.showinfo("Đã lưu", "Dữ liệu đã được lưu vào file notes.json")

btn_manual_save = tk.Button(button_frame, text="Lưu Dữ Liệu", command=manual_save_to_json)

# ===== BUTTON PLACEMENT =====
btn_save.grid(row=0, column=1)
btn_edit.grid(row=0, column=2)
btn_delete.grid(row=0, column=3)
btn_manual_save.grid(row=0, column=4, padx=(10, 0))
button_frame.pack(side=tk.TOP)

# ===== FUNCTION: INIT =====
def init():
    notes = load_notes_from_json()
    for note in notes:
        list_notes.insert(tk.END, note['title'])

# ===== FUNCTION: SELECT NOTE =====
def onselect(evt):
    global selected_index
    if not list_notes.curselection():
        return
    index = int(list_notes.curselection()[0])
    selected_index = index
    display_note(index)

# ===== FUNCTION: DISPLAY NOTE =====
def display_note(index):
    note_title.delete(0, tk.END)
    note_text.delete('1.0', tk.END)
    note_id = notes_ids[index]
    note = get_note_by_id(note_id)
    if note:
        note_title.insert(tk.END, note['title'])
        note_text.insert(tk.END, note['note'])
    btn_delete.config(state=tk.NORMAL)
    btn_edit.config(state=tk.NORMAL)

# ===== FUNCTION: SAVE NOTE =====
def save_note():
    title = note_title.get()
    note = note_text.get("1.0", tk.END).strip()
    if not title or not note:
        tk.messagebox.showerror("ERROR", "Bạn phải nhập tiêu đề và nội dung")
        return
    notes = load_notes_from_json()
    for n in notes:
        if n['title'] == title:
            tk.messagebox.showerror("ERROR", "Tiêu đề đã tồn tại.")
            return
    new_note = {
        "id": max([n['id'] for n in notes], default=0) + 1,
        "title": title,
        "note": note
    }
    notes.append(new_note)
    save_notes_to_json(notes)
    list_notes.insert(tk.END, title)
    notes_ids.append(new_note['id'])
    note_title.delete(0, tk.END)
    note_text.delete('1.0', tk.END)

# ===== FUNCTION: UPDATE NOTE =====
def update_note():
    global selected_index
    title = note_title.get()
    note = note_text.get("1.0", tk.END).strip()
    if not title or not note:
        tk.messagebox.showerror("ERROR", "Bạn phải nhập tiêu đề và nội dung")
        return
    notes = load_notes_from_json()
    note_id = notes_ids[selected_index]
    for n in notes:
        if n['id'] == note_id:
            n['title'] = title
            n['note'] = note
            break
    save_notes_to_json(notes)
    list_notes.delete(selected_index)
    list_notes.insert(selected_index, title)
    note_title.delete(0, tk.END)
    note_text.delete('1.0', tk.END)

# ===== FUNCTION: DELETE NOTE =====
def delete_note():
    global selected_index, notes_ids
    if selected_index is None or selected_index >= len(notes_ids):
        tk.messagebox.showerror("ERROR", "Bạn chưa chọn ghi chú để xoá")
        return
    result = tk.messagebox.askyesno("Xoá", "Bạn có chắc chắn muốn xoá ghi chú này?")
    if result:
        note_id = notes_ids[selected_index]
        notes = load_notes_from_json()
        notes = [n for n in notes if n['id'] != note_id]
        save_notes_to_json(notes)
        del notes_ids[selected_index]
        list_notes.delete(selected_index)
        note_title.delete(0, tk.END)
        note_text.delete('1.0', tk.END)

# ===== RUN =====
init()
window.mainloop()
