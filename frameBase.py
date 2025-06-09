import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog,filedialog,PhotoImage
from PIL import ImageTk , Image
import cv2
import os,sys
import shutil
import pytz
from datetime import datetime
from tkcalendar import DateEntry 
from tkinter import *
import webbrowser
import xlwt
import xlrd
import threading
import PIL


### CREATE DATABASE AND OTHER DIRECTORIES
def db_path(relative_path):
    return os.path.join(getattr(sys, '_MEIPASS', os.path.abspath(".")), relative_path)

def get_working_db_path():
    # Always use current working directory for writable DB
    return os.path.join(os.getcwd(), "inventory.db")

DB_PATH = get_working_db_path()

def backup_existing_database():
    db_path = get_working_db_path()
    if os.path.exists(db_path):
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_inventory_{timestamp}.db"
        #backup_path = os.path.join(os.getcwd(), backup_filename)
        filepath = filedialog.asksaveasfilename(initialfile = backup_filename,  defaultextension=".db")
        try:
            shutil.copy(db_path, filepath)
            messagebox.showinfo("Info",f"✔ Backup created: {backup_filename}")
        except Exception as e:
            messagebox.showerror("Error",f"❌ Failed to create DB backup: {e}")
    else:
        messagebox.showerror("Error","ℹ No existing DB to backup.")

def prompt_user_for_database_if_needed():
    db_path = get_working_db_path()

    # Only prompt if DB is missing
    if not os.path.exists(db_path):
        choice = messagebox.askyesno("No Database Found", "No database detected.\nDo you want to load a backup?")
        if choice:
            filepath = filedialog.askopenfilename(title="Select backup database", filetypes=[("DB files", "*.db")])
            if filepath:
                try:
                    shutil.copy(filepath, db_path)
                    messagebox.showinfo("Info","✅ Recovered DB copied.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to use selected backup: {e}")
                    sys.exit()
            else:
                messagebox.showinfo("Cancelled", "No backup selected. Exiting.")
                sys.exit()
        else:
            confirm = messagebox.askyesno("Start Fresh", "This will create a new empty database.\nContinue?")
            if not confirm:
                sys.exit()
            else:
                print("➡ Starting with fresh database.")

if not os.path.exists("images"):
    os.makedirs("images")
total = 0
# Database setup

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS client (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    balance INTEGER,
                    created_at DATETIME
                )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS client_ac (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id INTEGER,
                        name TEXT NOT NULL,
                        balance INTEGER,
                        receive INTEGER,
                        total INTEGER,
                        date DATETIME
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        manufacturer TEXT,
                        product_code NOT NULL UNIQUE,
                        image_path TEXT,
                        description TEXT,
                        part_number TEXT,
                        price REAL NOT NULL,
                        stock INTEGER NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER,
                        name TEXT NOT NULL,
                        manufacturer TEXT,
                        product_code TEXT,
                        image_path TEXT,
                        description TEXT,
                        part_number TEXT,
                        quantity INTEGER,
                        total REAL NOT NULL,
                        date DATETIME NOT NULL,
                        client TEXT NOT NULL DEFAULT 'customer',
                        payment  TEXT NOT NULL DEFAULT 'pending',
                        FOREIGN KEY(item_id) REFERENCES items(id))''')
    # CREATE DATA BASE FOR ADD ENIGINES 
    cursor.execute('''CREATE TABLE IF NOT EXISTS engines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER,
                        bike_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        manufacturer TEXT,
                        product_code TEXT,
                        image_path TEXT,
                        description TEXT,
                        part_number TEXT,
                        quantity INTEGER,
                        total REAL NOT NULL,
                        date DATE NOT NULL,
                        client TEXT NOT NULL DEFAULT 'customer',
                        payment  TEXT NOT NULL DEFAULT 'pending',
                        FOREIGN KEY(item_id) REFERENCES items(id))''')
    conn.commit()
    conn.close()
selected_list = []
# Functions to interact with the database
def add_item():
    name = name_entry.get()
    manufacturer = manufacturer_entry.get()
    product_code = product_code_entry.get().upper()
    image_path = image_path_entry.get()
    description = description_entry.get()
    part_number = part_number_entry.get()
    price = float(price_entry.get())
    stock = int(stock_entry.get())

    # Save image to images directory
    if os.path.exists(image_path):
        ext = os.path.splitext(image_path)[1]
        image_filename = f"images/{name.replace(' ', '_')}_{product_code}{ext}"
        shutil.copy(image_path, image_filename)
        image_path = image_filename

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (name, manufacturer, product_code, image_path, description, part_number, price, stock) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                   (name, manufacturer, product_code, image_path, description, part_number, price, stock))
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "Item added successfully")
    refresh_items()
# add client in data base
def add_client(value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    popup = tk.Toplevel(root)
    if value == "add":
        popup.title("ADD Client")
        popup.geometry("300x300")
        ttk.Label(popup, text="Add Client").pack(pady=5)
        ttk.Label(popup,text="Name").pack(padx=20)
        entry_name = tk.StringVar()
        entry_phone = tk.IntVar()
        name = tk.Entry(popup,width=40,textvariable=entry_name).pack(padx=2)
        ttk.Label(popup,text="Phone").pack(padx=20)
        phone = tk.Entry(popup,width=40,textvariable=entry_phone).pack(padx=2)
        balance = int(0)
        x = datetime.now()
        date = (f"{x.year}/{x.month}/{x.day}")
        def addClient():
            try:
                name = entry_name.get()
                phone = entry_phone.get()
                if name:
                    cursor.execute("INSERT INTO client (name, phone,balance,created_at) VALUES (?,?,?,?)",(name,phone,balance,date,))
                    conn.commit()
                    messagebox.showinfo("Info","Client has been Added")
                    popup.destroy()
            except Exception as e:
                print(e) 
            finally:
                conn.close()
        tk.Button(popup,text="ADD Client",command=addClient).pack(padx=2,pady=3)
def view_client():
    select_user = []
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    popup = tk.Toplevel(root)
    popup.title("VIEW CLIENT")
    popup.geometry("600x400")
    tuples = ("ID","NAME","PHONE","BALANCE","DATE")
    client_tree = ttk.Treeview(popup, columns=tuples, selectmode='extended',show="headings")
    for col in tuples:
        client_tree.heading(col, text=col)
        client_tree.column(col, width=100)
    client_tree.pack(pady=2)
    rows = cursor.execute("SELECT * FROM client").fetchall()
    for row in rows:
        client_tree.insert("", "end", values=row,)
    balance = tk.IntVar(value=0)
    received = tk.IntVar(value=0)
    p0 = ttk.LabelFrame(popup, text="Account")
    p0.pack(side="top", pady=4)
    row1 = ttk.Frame(p0)
    row1.pack(anchor="w", pady=2)

    ttk.Label(row1, text="Balance:", width=10).pack(side="left")
    bal = ttk.Entry(row1, textvariable=balance, width=20).pack(side="left")

    row2 = ttk.Frame(p0)
    row2.pack(anchor="w", pady=2)

    ttk.Label(row2, text="Received:", width=10).pack(side="left")
    rec = ttk.Entry(row2, textvariable=received, width=20).pack(side="left")
    row3 = ttk.Frame(p0)
    row3.pack(anchor="se",pady=2)

    def client_sheet(event):
        items = client_tree.identify_row(event.y)
        if items:
            select_user.clear()
            select_user.append(items)          
        print(select_user)
    def clinet_ac(event):
        ur_val = client_tree.item(select_user,"values")
        bal1 = balance.get()
        rec1 =  received.get()
        india_timezone = pytz.timezone("Asia/Kolkata")
        x = datetime.now(india_timezone)
        date = (f"{x.year}/{x.month}/{x.day} {x.hour}:{x.minute}:{x.second}")
        try:
            if select_user == "":
                messagebox.showerror("ERROR","CLIENT IS NOT SELECTED")
                return
            if bal1 != 0 and rec1 != 0:
                print("Both balance and received are entered.")
                client_id = int(ur_val[0])
                name = ur_val[1]
                total = int(ur_val[3]) + bal1 - rec1

                cursor.execute(
                    "INSERT INTO client_ac (client_id,name,balance,receive,total,date) VALUES (?,?,?,?,?,?)",
                    (client_id, name, bal1, rec1, total, date)
                )
                cursor.execute("UPDATE client SET balance = ? WHERE id = ?", (total, client_id))
                conn.commit()
            elif bal1 != 0:
                print("RUN Bal")
                client_id = int(ur_val[0])
                name = ur_val[1]
                total = bal1 + int(ur_val[3])
                cursor.execute("INSERT INTO client_ac (client_id,name,balance,total,date) VALUES (?,?,?,?,?)",(client_id,name,bal1,total,date,))
                cursor.execute("UPDATE client SET balance = balance + ?  WHERE id = ?",(bal1,client_id,))
                conn.commit()
            elif rec1 != 0:
                print("RUN received")
                client_id = int(ur_val[0])
                name = ur_val[1]
                total = int(ur_val[3]) - rec1
                cursor.execute("INSERT INTO client_ac (client_id,name,receive,total,date) VALUES (?,?,?,?,?)",(client_id,name,rec1,total,date,))
                cursor.execute("UPDATE client SET balance = balance - ? WHERE id = ?",(rec1,client_id,))
                conn.commit()
   
        except Exception as e:
                messagebox.showwarning("Warning",f"{e}")
                conn.close()
        finally:
            conn.close
            balance.set(0)
            received.set(0)
        for row in client_tree.get_children():
                client_tree.delete(row)
                rows = cursor.execute("SELECT * FROM client").fetchall()
        for row in rows:
            client_tree.insert("","end",values=row)
            

    def transaction_sheet(event):
        items = client_tree.identify_row(event.y)
        item = client_tree.item(items,"values")
        id = item[0]
        rows = cursor.execute("SELECT * FROM client_ac WHERE client_id = ?",id) 
        client_tree.pack_forget()
        p0.pack_forget()
        popup.geometry("700x400")
        tuples1 = ("ID","Client_ID","NAME","BALANCE","RECEIVED","TOTAL","DATE")
        client_tree2 = ttk.Treeview(popup, columns=tuples1, selectmode='extended',show="headings")
        for col in tuples1:
            client_tree2.heading(col, text=col)
            client_tree2.column(col, width=100)
        client_tree2.pack(pady=2)
        for row in rows:
            client_tree2.insert("","end",values=row)
    ttk.Button(row3,text="Submit",command=lambda:clinet_ac(event=None)).pack(side="right")
    client_tree.bind("<ButtonRelease-1>",client_sheet)
    client_tree.bind("<Double-1>",transaction_sheet)

#pop up for add items   
def show_popup(event):
    popup = tk.Toplevel(root)
    popup.title("Select an Option")
    popup.geometry("300x100")
    ttk.Label(popup, text="Choose Where to Add Item").pack(pady=5)
    button_sales = tk.Button(popup,text="DAILY SALES", command=lambda:add_to_sales(None)).pack(pady=6)
    button_engines = tk.Button(popup,text="ENGINE SALES",command=lambda: engines_pop(None)).pack(pady=6)
    popup.after(15000, lambda: popup.destroy())

#PROGRAM TO SELECT LIST 
def selectRow(event):
    total = 0
    if frame_items.winfo_ismapped():
        item_id = items_tree.identify_row(event.y)
        column_id = items_tree.identify_column(event.x)
        # Only toggle if clicked in the first column ("#0")
        if not item_id or column_id != "#0":
            return
        tags = items_tree.item(item_id, "tags")
        selected_data = []
        if "checked" in tags:
            # Change to unchecked
            items_tree.item(item_id, image=unchecked, tags=("unchecked",))
            if item_id in selected_list:
                selected_list.remove(item_id)
        else:
            # Change to checked
            items_tree.item(item_id, image=checked, tags=("checked",))
            if item_id not in selected_list:
                selected_list.append(item_id)
        select_list.configure(text=f"Selected:{len(selected_list)}")
    if frame_daily_sales.winfo_ismapped():
        item_id = sales_tree.identify_row(event.y)
        column_id = sales_tree.identify_column(event.x)
        # Only toggle if clicked in the first column ("#0")
        if not item_id or column_id != "#0":
            return
        tags = sales_tree.item(item_id, "tags")
        selected_data = []
        if "checked" in tags:
            # Change to unchecked
            sales_tree.item(item_id, image=unchecked, tags=("unchecked",))
            if item_id in selected_list:
                selected_list.remove(item_id)
        else:
            # Change to checked
            sales_tree.item(item_id, image=checked, tags=("checked",))
            if item_id not in selected_list:
                selected_list.append(item_id)
        select_list.configure(text=f"Selected:{len(selected_list)}")
        if not selected_list:
            total_Label.configure(text="Total: 0.0")
        else:
            for items in selected_list:
                item = sales_tree.item(items, "value")
                total += float(item[9]) if item[9] else 0.0
                total_Label.configure(text=f"Total: {total}")
    if frame_engine.winfo_ismapped():
        item_id = engine_tree.identify_row(event.y)
        column_id = engine_tree.identify_column(event.x)
        # Only toggle if clicked in the first column ("#0")
        if not item_id or column_id != "#0":
            return
        tags = engine_tree.item(item_id, "tags")
        selected_data = []
        if "checked" in tags:
            # Change to unchecked
            engine_tree.item(item_id, image=unchecked, tags=("unchecked",))
            if item_id in selected_list:
                selected_list.remove(item_id)
        else:
            # Change to checked
            engine_tree.item(item_id, image=checked, tags=("checked",))
            if item_id not in selected_list:
                selected_list.append(item_id)
        select_list.configure(text=f"Selected:{len(selected_list)}")
        if not selected_list:
            engine_total.configure(text="Total: 0.0")
        else:
            for items in selected_list:
                item = engine_tree.item(items, "value")
                total += float(item[10]) if item[10] else 0.0
                engine_total.configure(text=f"Total: {total}")
        
#ADD TO SALES  #######################################################################################
#ADD TO ALE #######################################################################################
def add_to_sales(event=None):
    #selected_item = items_tree.selection()
    combo = ""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if not selected_list:
        messagebox.showwarning("Warning","Item not selected")
        return
    C_data = cursor.execute("SELECT name FROM client").fetchall()
    C_data = [item[0] for item in C_data]
    popup = tk.Toplevel(root)
    popup.geometry("200x100")
    lbframe1 = ttk.LabelFrame(popup,text="Select Client")
    lbframe1.pack(pady=2)
    C_box = ttk.Combobox(lbframe1,values=C_data,state="normal")
    C_box.pack(pady=2)
    def fetch_val():
        combo = C_box.get()
        print(f"Button Clicked and value is : {combo}")
        if not combo:
            messagebox.showwarning("No Selection", "Please select a client.")
            return
        print(f"Selected client: {combo}")
        popup.destroy()
    
        for item in selected_list:
    
            try:
                item_data = items_tree.item(item, "values")
                if not item_data:
                    continue
                item_id = item_data[0]
                name = item_data[1]
                manufacturer = item_data[2]
                product_code = item_data[3]
                image_path = item_data[4]
                description = item_data[5]
                part_number = item_data[6]
                price = float(item_data[7])
                stock = int(item_data[8])
                quantity = simpledialog.askinteger("Quantity", f"Enter quantity:{name}", minvalue=1, maxvalue=stock)
                if quantity is None:
                    return
                total = price * quantity
                x = datetime.now()
                date = (f"{x.year }-{x.month}-{x.day}")
                client = combo
                cursor.execute("INSERT INTO sales (item_id, name, manufacturer, product_code, image_path, description, part_number, quantity, total, date, client) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (item_id, name, manufacturer, product_code, image_path, description, part_number, quantity, total,date,client,))
                cursor.execute("UPDATE items SET stock = stock - ? WHERE id = ?", (quantity, item_id,))
            except Exception as e:
                print(f"Error procesing item {item}:{e}")
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Item added to daily sales")
        refresh_items()
        selected_list.clear()
    ttk.Button(popup,text="OK",command=fetch_val).pack(pady=2)
#add items in engine with popup
def engines_pop(event=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    rows = cursor.execute("SELECT bike_id FROM engines")
    rows = rows.fetchall()
    client = cursor.execute("SELECT name FROM client").fetchall() 
    conn.close()
    popup = tk.Toplevel(root)
    popup.title("ADD TO ENGINE")
    popup.geometry("300x200") 
    ttk.Label(popup, text="Choose Bike or Add new Number in List ").pack(pady=5)
    rows.reverse()
    combo = ttk.Combobox(popup, values=rows, state="normal")
    combo.pack(pady=5)
    ttk.Label(popup, text="Choose Client ").pack(pady=5)
    clt = ttk.Combobox(popup,values=client,state="normal")
    clt.pack(pady=6)
     
    
    def on_select():
        selected_value = combo.get()
        quantity_data = clt.get()    
        add_to_engines(selected_value,quantity_data)
        popup.destroy()
        
    ttk.Button(popup, text="OK", command=on_select).pack(pady=5)


def add_to_engines(value,data,event=None):  
    #selected_item = items_tree.selection()
    if not selected_list:
        messagebox.showwarning("Warning", "Item not selected")
        return
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for item in selected_list:
                try:
                    item_data = items_tree.item(item, "values")
                    if not item_data:
                        continue
                    item_id = item_data[0]
                    name = item_data[1]
                    manufacturer = item_data[2]
                    product_code = item_data[3]
                    image_path = item_data[4]
                    description = item_data[5]
                    part_number = item_data[6]
                    price = float(item_data[7])
                    stock = int(item_data[8])
                    bike_id = value
                    quantity = simpledialog.askinteger("Quantity", f"Enter quantity:{name}", minvalue=1, maxvalue=stock)
                    if quantity is None:
                        return
                    total = price * quantity
                    x = datetime.now()
                    date = f"{x.year}-{x.month}-{x.day}"
                    client = data
                    payment = "pending"
                    cursor.execute(
                        "INSERT INTO engines (item_id, bike_id, name, manufacturer, product_code, image_path, description, part_number, quantity, total, date,client,payment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)",
                        (item_id, bike_id, name, manufacturer, product_code, image_path, description, part_number, quantity, total, date,client,payment)
                    )
                    cursor.execute("UPDATE items SET stock = stock - ? WHERE id = ?",(quantity, item_id))
                except Exception as e:
                    print(f"Error processing item {item}: {e}")
            conn.commit()
        messagebox.showinfo("Success", "Item(s) added to Engine Diary")
    except sqlite3.OperationalError as e:
        messagebox.showerror("Database Error", f"Could not complete operation:\n{e}")
    selected_list.clear()
# Refresh Items
def refresh_items():
    for row in items_tree.get_children():
        items_tree.delete(row)
    for row in get_items():
        qty =  row[8]
        tag = 'low_stock' if qty <= 3 else ''
        items_tree.insert("", "end", values=row, image=unchecked ,tags=(tag,))  
    selected_list.clear()
    select_list.configure(text=f"Selected:{len(selected_list)}")

def get_items():
    for row in items_tree.get_children():
        items_tree.delete(row)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    rows = cursor.fetchall()
    conn.close()
    return rows
    for row in rows:
        items_tree.insert("", "end", values=row,)
# SHOW LEVELS OF QUANTITY 
def stk_lvl():
    for row in items_tree.get_children():
        items_tree.delete(row)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE stock <= 3")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        items_tree.insert("","end",values=row)
    result = messagebox.askyesno("PRINT","DO YOU WANT TO CREATE A PDF?")
    if result == True:
        export_list("pdf")
    
# CONTEXT MENU FOR ITEM LIST
def item_list1(event):
    context_menu_item.tk_popup(event.x_root,event.y_root)  
def items_menu(value):
    selected = items_tree.selection()
    item = items_tree.item(selected,"values")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if value == "stock":
        item_id = item[0]
        print(item_id)
        result = simpledialog.askinteger("ADD STOCK","ENTER STOCK")
        if result:
            cursor.execute("UPDATE items SET stock = stock + ? WHERE id = ?",(result,item_id))
            conn.commit()
            conn.close()
            refresh_items()
        else:
            conn.close()
            return
    if value == "price":
        item_id = item[0]
        result = simpledialog.askinteger("EDIT PRICE","ENTER PRICE")
        if result:
            cursor.execute("UPDATE items SET price = ? WHERE id = ?",(result,item_id))
            conn.commit()
            conn.close()
            refresh_items()
        else:
            conn.close()
            return
        
#search button for items
def search_items():
    for row in items_tree.get_children():
        items_tree.delete(row)
    search_term = search_entry.get()
    print(search_term)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT * FROM items WHERE name LIKE ? OR product_code LIKE ? OR manufacturer LIKE ?"
    cursor.execute(query, ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        messagebox.showwarning("WARNING","ITEM NOT FOUND")
    for row in rows:
        items_tree.insert("","end",values=row)   
# ---------------------------------------------------------
def get_engine():
    for row in engine_tree.get_children():
        engine_tree.delete(row)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM engines")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        engine_tree.insert("", "end", values=row,image=unchecked)

def search_engine_items():
    total = 0
    for row in engine_tree.get_children():
        engine_tree.delete(row)
    search1 = search_engine1.get()
    date = cal2.get_date()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    formatted_date = datetime.strptime(f'{date}', "%Y-%m-%d").strftime("%Y-%#m-%#d")
    if search1:
        rows = cursor.execute(f"SELECT * FROM engines WHERE bike_id ='{search1}'").fetchall()
        if not rows:
            messagebox.showerror(title="WARNING",message="ITEM NOT FOUND")
            get_engine()
        for row in rows:
            total += float(row[10]) if row[10] else 0
            engine_tree.insert("", "end", values=row)
        engine_total.configure(text=f"Total: {total}")
    else:
        rows = cursor.execute(f"SELECT * FROM engines WHERE date ='{formatted_date}'").fetchall()
        if not rows:
            messagebox.showerror(title="WARNING",message="ITEM NOT FOUND")
            get_engine()
        for row in rows:
            total += float(row[10]) if row[10] else 0
            engine_tree.insert("", "end", values=row)
        engine_total.configure(text=f"Total: {total}")
    conn.close()      
# search client in engine frame 
def sr_clt():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
    
        for row in engine_tree.get_children():
            engine_tree.delete(row)
        rows = cursor.execute(f"SELECT * FROM engines WHERE client='{chr_clinet.get()}'").fetchall()
        for row in rows:
            engine_tree.insert("", "end", values=row)
    except Exception as e:
        messagebox.showwarning("Warning",f"{e}")
        get_engine()

# Show daily list 
def daily_list():
    for row in sales_tree.get_children():
        sales_tree.delete(row)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        sales_tree.insert("", "end", values=row , image=unchecked)
    show_daily_list()
  
# Context menu for daily sale item
def daily_item_edit(event):
    context_menu.tk_popup(event.x_root,event.y_root)

# edit daily items 
def sale_menu(value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()     
    if frame_daily_sales.winfo_ismapped():
        selected = sales_tree.selection()
        item = sales_tree.item(selected,"values")
        item_id = item[1]
        quantity  = item[8]
        sale_id = item[0]     
        if "delete" in value:
            result =  messagebox.askyesno("warning","Are You Sure")
            if result == True:
                rows = cursor.execute("DELETE FROM sales WHERE id = ?",(sale_id,))
                cursor.execute("UPDATE items SET stock = stock + ? WHERE id = ?", (quantity ,item_id,)).fetchall() 
                messagebox.showinfo("INFO","ITEM DELETED")
                conn.commit()
                conn.close() 
                daily_list()
                get_items()
            else:
                return
        if "qty" in value:
            qty = simpledialog.askinteger("Quatity","Enter Quantity",minvalue=1)
            price = cursor.execute("SELECT price FROM items WHERE id = ?",(item_id,)).fetchone()
            price = float(price[0])
            if qty:
                current_quantity = int(quantity)
                new_quantity = int(qty)
                total = price * new_quantity
                try:
                    # Compare and update
                    if new_quantity > current_quantity:
                        difference = new_quantity - current_quantity
                        rows =  cursor.execute("UPDATE sales SET quantity = ? , total = ? WHERE id = ?", (new_quantity, total, sale_id))
                        cursor.execute("UPDATE items SET stock = stock - ? WHERE id = ?", (difference, item_id))
                        messagebox.showinfo("Info", f"Quantity increased by {difference}")
                    elif new_quantity < current_quantity:
                        difference = current_quantity - new_quantity
                        rows = cursor.execute("UPDATE sales SET quantity = ? , total = ? WHERE id = ?", (new_quantity, total, sale_id))
                        cursor.execute("UPDATE items SET stock = stock + ? WHERE id = ?", (difference, item_id))
                        messagebox.showinfo("Info", f"Quantity decreased by {difference}")
                    else:
                        messagebox.showinfo("Info", "Quantity is unchanged.")
                    conn.commit()
                except Exception as e:
                    messagebox.showerror("Error", f"Something went wrong: {e}")
                finally:
                    conn.close()
                    daily_list()
                    get_items()
            else:
                return
    if frame_engine.winfo_ismapped():
        selected = engine_tree.selection()
        item = engine_tree.item(selected,"values")
        item_id = item[1]
        quantity  = item[9]
        sale_id = item[0]     
        if "delete" in value:
            result =  messagebox.askyesno("warning","Are You Sure")
            if result == True:
                rows = cursor.execute("DELETE FROM engines WHERE id = ?",(sale_id,))
                cursor.execute("UPDATE items SET stock = stock + ? WHERE id = ?", (quantity ,item_id,)).fetchall() 
                messagebox.showinfo("INFO","ITEM DELETED")
                conn.commit()
                conn.close() 
                get_engine()
            else:
                return
        if "qty" in value:
            qty = simpledialog.askinteger("Quatity","Enter Quantity",minvalue=1)
            price = cursor.execute("SELECT price FROM items WHERE id = ?",(item_id,)).fetchone()
            price = float(price[0])
            if qty:
                current_quantity = int(quantity)
                new_quantity = int(qty)
                total = new_quantity * price
                try:
                    # Compare and update
                    if new_quantity > current_quantity:
                        difference = new_quantity - current_quantity
                        rows =  cursor.execute("UPDATE engines SET quantity = ?, total = ? WHERE id = ?", (new_quantity,total,sale_id))
                        cursor.execute("UPDATE items SET stock = stock - ? WHERE id = ?", (difference, item_id)).fetchall()
                        messagebox.showinfo("Info", f"Quantity increased by {difference}")
                    elif new_quantity < current_quantity:
                        difference = current_quantity - new_quantity
                        rows = cursor.execute("UPDATE engines SET quantity = ? , total = ? WHERE id = ?", (new_quantity, total,sale_id))
                        cursor.execute("UPDATE items SET stock = stock + ? WHERE id = ?", (difference, item_id)).fetchall()
                        messagebox.showinfo("Info", f"Quantity decreased by {difference}")
                    else:
                        messagebox.showinfo("Info", "Quantity is unchanged.")
                    conn.commit()
                except Exception as e:
                    messagebox.showerror("Error", f"Something went wrong: {e}")
                finally:
                    conn.close()
                    get_engine()
            else:
                return

#SEARCH DAILY ITEMS 
def search_by_date():
    total = 0
    selected_date = cal.get_date()
    formatted_date = datetime.strptime(f'{selected_date}', "%Y-%m-%d").strftime("%Y-%#m-%#d")
    for row in sales_tree.get_children():
        sales_tree.delete(row)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM sales WHERE date = '{formatted_date}'")
    rows = cursor.fetchall()
    for row in rows:
        total += float(row[9]) if row[9] else 0
    total_Label.configure(text=f"Total: {total}")
    conn.close()
    if not rows:
        messagebox.showwarning("WARNING",f"NO RECORD FOUND ON : {selected_date}")
        daily_list()
    for row in rows:
        sales_tree.insert("", "end", values=row)
    show_daily_list()
    return total 


#FRAME SWITCH 
def show_add_item_page():
    frame_items.pack_forget()
    frame_daily_sales.pack_forget()
    frame_engine.pack_forget()
    frame_add_item.pack()
    

def show_items_page():
    frame_add_item.pack_forget()
    frame_daily_sales.pack_forget()
    frame_engine.pack_forget()
    frame_items.pack()
   

def show_daily_list():
    selected_list.clear()
    total_Label.configure(text=f"Total: {0.0}")
    frame_items.pack_forget()
    frame_add_item.pack_forget()
    frame_engine.pack_forget()
    frame_daily_sales.pack()
    
def show_engine_page():
    selected_list.clear()
    engine_total.configure(text=f"Total: {0.0}")
    frame_items.pack_forget()
    frame_add_item.pack_forget()
    frame_daily_sales.pack_forget()
    get_engine()
    frame_engine.pack()
   
    

def exit_app():
    root.destroy()


def select_image():
    filepath = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", "*.jpg *.png *.jpeg")])
    if filepath:
        image_path_entry.delete(0, tk.END)
        image_path_entry.insert(0, filepath)

def capture_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        filepath = "captured_image.jpg"
        cv2.imwrite(filepath, frame)
        image_path_entry.delete(0, tk.END)
        image_path_entry.insert(0, filepath)
        messagebox.showinfo("Captured", "Image saved as captured_image.jpg")
    cap.release()
    cv2.destroyAllWindows()
        
def show_image_popup(event):
    selected = items_tree.identify_row(event.y)
    if not selected:
        return

    values = items_tree.item(selected, "values")
    
    # Adjust these indices according to your column order in the Treeview
    item_name = values[1]
    item_price = values[7]
    item_quantity = values[8]
    image_path = values[4]

    if not os.path.exists(image_path):
        messagebox.showerror("Error", "Image not found!")
    # Create popup window
    popup = tk.Toplevel(root)
    popup.title("Item Details")
    popup.geometry("400x500")
    try:
        img = PIL.Image.open(image_path).resize((200, 200))
        photo = ImageTk.PhotoImage(img)
    except Exception as e:
        messagebox.showerror("Error", f"{e}")
        return

    # Display image
    img_label = ttk.Label(popup, image=photo)
    img_label.image = photo  # prevent garbage collection
    img_label.pack(pady=10)

    # Show other details
    ttk.Label(popup, text=f"Name:  {item_name}", font=("Arial", 12)).pack()
    ttk.Label(popup, text=f"Price:  ₹{item_price}", font=("Arial",12)).pack()
    ttk.Label(popup, text=f"Quantity:  {item_quantity}", font=("Arial", 12)).pack()
    ttk.Label(popup, text=f"Manufactrer :  {values[2]}",font=("Arial",12)).pack()
    ttk.Label(popup, text=f"Description :  {values[5]}",font=("Arial",12)).pack()
    ttk.Label(popup, text=f"Product Code :  {values[3]}",font=("Arial", 12)).pack()
    ttk.Label(popup, text=f"Part Number :  {values[6]}",font=("Arial",12)).pack()

    # Auto-close after 15 seconds
    popup.after(15000, popup.destroy)

                   
# EXCEL TEMPLATE
def download_template():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items LIMIT 1")
    column_names = [description[0] for description in cursor.description]
    excluded_columns = ['id']
    filtered_columns = [col for col in column_names if col not in excluded_columns]
    conn.close()
    print(filtered_columns)
    # Create .xls file
    wb = xlwt.Workbook()
    ws = wb.add_sheet("Template")
    
    for idx, col_name in enumerate(filtered_columns):
        ws.write(0, idx, col_name)
    
    filepath = filedialog.asksaveasfilename(defaultextension=".xls")
    if filepath:
        wb.save(filepath)
        print("Template saved.")
#IMPORT File
def upload_data_to_sql(progress_bar,status_label):
    filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xls")])
    progress_bar.start(10)  # Start moving
    status_label.config(text="Processing...")
    if not filepath:
        return
    book = xlrd.open_workbook(filepath)
    sheet = book.sheet_by_index(0)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    headers = [sheet.cell(0, col).value for col in range(sheet.ncols)]
    print("Headers:", headers)
    # Find the index of the unique identifier (e.g., part_number)
    try:
        part_number_index = headers.index("product_code")  # change if you're using another unique field
    except ValueError:
        print("product_code column not found in the Excel file!")
        conn.close()
        return
    for row_idx in range(1, sheet.nrows):
        values = [sheet.cell(row_idx, col).value for col in range(sheet.ncols)]
        product_code = values[part_number_index]
        # Check for existing entry in SQL
        cursor.execute("SELECT * FROM items WHERE product_code = ?", (product_code,))
        existing = cursor.fetchone()
        if not existing:
            placeholders = ','.join('?' * len(values))
            cursor.execute(f"INSERT INTO items ({','.join(headers)}) VALUES ({placeholders})", values)
            print(f"Inserted row {row_idx}: {product_code}")
        else:
            print(f"Duplicate skipped at row {row_idx}: {product_code}")
    conn.commit()
    conn.close()
    print("Data upload complete with duplicate check.")
    progress_bar.stop()
    progress_bar.grid_remove()
    status_label.config(text="Ready")

# EXPORT FUNCTION 

def export_list(value):
    data = []
    headers = []
    total = 0.0
    client = ""
    head = ""
    if frame_daily_sales.winfo_ismapped():
        head = "Daily Sales"
        print("daily_sale frame active")
        sales_tree.selection_set(sales_tree.get_children())   
        selected_items = sales_tree.selection()        
        all_columns = sales_tree["columns"]
        exclude_cols = ["ID","Item ID","Product Code","Image Path","Client","Payment"]
        headers = [col for col in all_columns if col not in exclude_cols]

        for item in selected_items:
            row = sales_tree.item(item, "values")
            row_dict = dict(zip(all_columns, row))
            total += float(row[9]) if row[9] else 0
            filtered_row = [row_dict[col] for col in headers]
            data.append(filtered_row)
            client = row[11]
    
    if frame_engine.winfo_ismapped():
        head = "Engine Sales"
        print("engine frame is active")
        engine_tree.selection_set(engine_tree.get_children())   
        selected_items = engine_tree.selection()        
        all_columns = engine_tree["columns"]
        exclude_cols = ["ID","Item ID","Product Code","Image Path","Client","Payment"]
        headers = [col for col in all_columns if col not in exclude_cols]
        for item in selected_items:
            row = engine_tree.item(item, "values")
            row_dict = dict(zip(all_columns, row))
            total += float(row[10]) if row[10] else 0
            filtered_row = [row_dict[col] for col in headers]
            data.append(filtered_row)
            client = row[12]
    if frame_items.winfo_ismapped():
        head = "STOCK LIST"
        print("ITEM frame is active")
        items_tree.selection_set(items_tree.get_children())   
        selected_items = items_tree.selection()        
        all_columns = items_tree["columns"]
        exclude_cols = ["ID","Product Code","Image Path","Price"]
        headers = [col for col in all_columns if col not in exclude_cols]
        for item in selected_items:
            row = items_tree.item(item, "values")
            row_dict = dict(zip(all_columns, row))
            filtered_row = [row_dict[col] for col in headers]
            data.append(filtered_row)
            
        # Create PDF
        
        # HTML template
        html_content = f"""
        <html>
        <head>
            <style>
            
            @page {{
            size: A4 landscape;
            margin: 1cm;
                }}

                body {{ font-family: Arial, sans-serif;font-size:'11pt';font-weight:500;}}
                h1{{}}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #444; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                 .total-row td {{
            font-weight: bold;
            background-color: #e2e2e2;
        }}
                
            </style>
        </head>
        <body>
            <h2>{head}</h2>
            <h3>Name : {client}</h2>
            <text>{datetime.now()}</text>
            <table>
                <tr>
                    {''.join(f"<th>{col}</th>" for col in headers)}
                </tr>
                {''.join(
                    f"<tr>{''.join(f'<td>{str(cell)}</td>' for cell in row)}</tr>"
                    for row in data
                )}
                 <tr class="total-row">
            <td colspan="{len(headers) - 1}">Total</td>
            <td>{total}/-</td>
        </tr>
            </table>
        </body>
        </html>
        """
    if value == "pdf":
        with open("invoice.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        # Open in default browser (triggers print on load)
        webbrowser.open("invoice.html")
    



# Threading 
def start_db_thread(progress_bar, status_label):
    progress_bar.grid(row=0, column=0, padx=5, pady=2, sticky="e")  # Show progress bar
    threading.Thread(target=upload_data_to_sql, args=(progress_bar, status_label)).start()

def resource_path(relative_path):
    """ Get absolute path to resource (for dev and PyInstaller .exe) """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

# GUI Setup
root = tk.Tk()
root.title("Stock Management System")
icon = PhotoImage(file= resource_path("icon96.png"))  # PNG file
root.iconphoto(True, icon)

# Main Frame
frame_main = ttk.Frame(root, padding=10)
frame_main.pack()
#style of tree
style = ttk.Style()
style.configure("Treeview", font=("Arial",10,'bold')) 
style.configure("Treeview.Heading", font=("Arial",11, "bold"))
# Status Bar Frame
status_frame = ttk.Frame(root, relief="sunken")
status_frame.pack(side="bottom", fill="x")
status_frame.columnconfigure(0, weight=1)
status_frame.columnconfigure(1, weight=1)
status_frame.columnconfigure(2, weight=1)
# Status Label
status_label = ttk.Label(status_frame, text="Ready")
status_label.grid(row=0, column=0, padx=10, pady=2,sticky="w")
select_list = ttk.Label(status_frame,text="Selected:")
select_list.grid(row=0, column=1, padx=10, pady=5, sticky="e")  # Right aligned
# Progress Bar inside Status Bar
progress_bar = ttk.Progressbar(status_frame, mode='indeterminate', length=100)
# try to fetch images
checked = ()
unchecked = ()
try:
    chepic = PIL.Image.open(resource_path('checked.png')).resize((20, 20))
    unpic = PIL.Image.open(resource_path('unchecked.png')).resize((20, 20))
    checked = ImageTk.PhotoImage(chepic)
    unchecked = ImageTk.PhotoImage(unpic)

except Exception as e:
    print(f"there is an Error: {e}")
# Navigation Buttons
nav_frame = ttk.Frame(frame_main)
nav_frame.pack()
btn_add_item = ttk.Button(nav_frame, text="Add Item", command=show_add_item_page)
btn_add_item.pack(side=tk.LEFT, padx=5)
btn_view_items = ttk.Button(nav_frame, text="View Items", command=show_items_page)
btn_view_items.pack(side=tk.LEFT, padx=5)
btn_daily_sales = ttk.Button(nav_frame, text="Daily Sales", command=daily_list)
btn_daily_sales.pack(side=tk.LEFT, padx=5)
btn_engine_sales = ttk.Button(nav_frame, text="Engine List", command=show_engine_page)
btn_engine_sales.pack(side=tk.LEFT, padx=5)
btn_refresh = ttk.Button(nav_frame, text="Refresh", command=refresh_items)
btn_refresh.pack(side=tk.LEFT, padx=5)
btn_exit = ttk.Button(nav_frame, text="Exit", command=exit_app)
btn_exit.pack(side=tk.LEFT, padx=5)
# menu bar 
menubar = Menu(root)
file = tk.Menu(menubar,tearoff=0)
menubar.add_cascade(label='Export',menu =file )
file.add_command(label='Stock List',command= stk_lvl)
file.add_command(label='PDF',command=lambda:export_list("pdf"))
file.add_command(label="Backup",command=backup_existing_database)
Add_item = Menu(menubar,tearoff=0)
menubar.add_cascade(label='Add_Item',menu=Add_item)
Add_item.add_command(label='Download Template',command=download_template)
Add_item.add_command(label='Upload Template',command=lambda:start_db_thread(progress_bar,status_label))
Add_Client = Menu(menubar,tearoff=0)
menubar.add_cascade(label='Add Client',menu=Add_Client)
Add_Client.add_command(label="ADD Client",command=lambda:add_client("add"))
Add_Client.add_command(label="View Client",command=view_client)

# Add Item Frame
frame_add_item = ttk.Frame(frame_main, padding=10)
labels = ["Item Name", "Manufacturer", "Product Code", "Image Path", "Description", "Part Number", "Price", "Stock"]
entries = []
for i, label in enumerate(labels):
    ttk.Label(frame_add_item, text=label).grid(row=i, column=0, sticky=tk.W)
    entry = ttk.Entry(frame_add_item)
    entry.grid(row=i, column=1)
    entries.append(entry)

name_entry, manufacturer_entry, product_code_entry, image_path_entry, description_entry, part_number_entry, price_entry, stock_entry = entries
#ADD IMAGE INPUTS 
btn_select_image = ttk.Button(frame_add_item, text="Select Image", command=select_image)
btn_select_image.grid(row=3, column=2)
btn_capture_image = ttk.Button(frame_add_item, text="Capture Image", command=capture_image)
btn_capture_image.grid(row=3, column=3)


add_button = ttk.Button(frame_add_item, text="Add Item", command=add_item)
add_button.grid(row=len(labels), column=0, columnspan=2, pady=5)
# Create a top status bar or header frame
# Create a container frame at the top of the root
top_bar = tk.Frame(root)
top_bar.pack(side='top', fill='x', anchor='nw')  # Anchored to top-left

# Items List Frame
frame_items = ttk.Frame(frame_main, padding=10)
columns_items = ("ID", "Name", "Manufacturer", "Product Code", "Image Path", "Description", "Part Number", "Price", "Stock",)
items_tree = ttk.Treeview(frame_items, columns=columns_items, selectmode='extended',show="tree headings")
items_tree.tag_configure('low_stock',background="#ed2f36",foreground="white")  # or foreground='red'
items_tree.heading("#0", text="Select")
items_tree.column("#0", width=50)
items_tree.image_unchecked = unchecked
items_tree.image_checked = checked
for col in columns_items:
    items_tree.heading(col, text=col)
    items_tree.column(col, width=100)
items_tree.pack()
#-------------------------------------------------------

context_menu_item = tk.Menu(frame_items,tearoff=0)
context_menu_item.add_command(label="Add Items",command=lambda:show_popup(None))
context_menu_item.add_command(label="Add Stock",command=lambda:items_menu("stock"))
context_menu_item.add_command(label="Edit Price",command=lambda:items_menu("price"))
items_tree.bind("<Button-3>",item_list1)
items_tree.bind("<Double-1>", show_image_popup)
items_tree.bind("<Button-1>",selectRow)

# Engine repair 
frame_engine = ttk.Frame(frame_main)
# Create a vertical scrollbar
# === Inner frame to hold Treeview and scrollbars ===
tree_container_eng = ttk.Frame(frame_engine)
tree_container_eng.pack(fill='both', expand=True, side='top')
#scrollbars
vbar = tk.Scrollbar(tree_container_eng, orient='vertical')
hbar = tk.Scrollbar(tree_container_eng, orient='horizontal')

columns_items = ("ID", "Item ID","Bike Number", "Name", "Manufacturer", "Product Code", "Image Path", "Description", "Part Number", "Quantity", "Total","Date","Client","Payment",)
engine_tree = ttk.Treeview(tree_container_eng, yscrollcommand=vbar.set, xscrollcommand=hbar.set, columns=columns_items, show="tree headings")
engine_tree.heading("#0", text="Select")
engine_tree.column("#0", width=50)
engine_tree.image_unchecked = unchecked
engine_tree.image_checked = checked
for col in columns_items:
    engine_tree.heading(col, text=col)
    engine_tree.column(col, width=100)

vbar.config(command=engine_tree.yview)
hbar.config(command=engine_tree.xview)
# Grid layout inside the tree_container only
engine_tree.grid(row=0, column=0, sticky='nsew')
vbar.grid(row=0, column=1, sticky='ns')
hbar.grid(row=1, column=0, sticky='ew')

tree_container_eng.grid_rowconfigure(0, weight=1)
tree_container_eng.grid_columnconfigure(0, weight=1)
engine_tree.bind("<Button-1>",selectRow)
engine_total = tk.Label(frame_engine,text=f"Total: 0.0 ",borderwidth=2,width=10 ,bg="white",relief="solid")
engine_total.pack(pady=5,side="bottom")
#Radio Button:
chr_clinet = tk.StringVar(value="customer")
# Engine Item search
search_frame1 = ttk.Frame(frame_engine)
search_frame1.pack(pady=10,fill='x',side="top")
op = []
clt_list = ""
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    clt_list = cursor.execute("SELECT bike_id FROM engines").fetchall()
    unique_names = list(set([row[0] for row in clt_list]))
    if unique_names:
        op = unique_names
    else:
        op = "Empty"
except Exception as e:
    messagebox.showerror("ERROR","FAILED TO FETCH")

sr_lb1 = ttk.LabelFrame(search_frame1,text="Select From List")
sr_lb1.pack(pady=6,side="top")
search_engine1 = ttk.Combobox(sr_lb1, values=op, state="normal")
search_engine1.pack()
sr_lb2 = ttk.LabelFrame(search_frame1,text="Search With Date")
sr_lb2.pack(side="top",padx=5)
cal2 = DateEntry(sr_lb2, width=12, borderwidth=2)
cal2.pack()
search_engine_date = ttk.Button(sr_lb2,text="Search",command=search_engine_items)
search_engine_date.pack()
sr_lb3 = ttk.LabelFrame(search_frame1,text="Sreach Client")
sr_lb3.pack(side="left",padx=5)
clt = []
cl_list = ""
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cl_list = cursor.execute("SELECT name FROM client").fetchall()
    unique_names = list(set([row[0] for row in cl_list]))
    if unique_names:
        clt = unique_names
    else:
        clt = "NO DATA"
except Exception as e:
    messagebox.showerror("ERROR","FAILED TO FETCH")

search_client = ttk.Combobox(sr_lb3,values=clt, textvariable=chr_clinet, state="normal").pack()
ttk.Button(sr_lb3,text="Go",command=sr_clt).pack(pady=5,side="top")
engine_tree.bind("<Button-3>",daily_item_edit)
# Search Bar to add sales 
search_frame = ttk.Frame(frame_items)
search_frame.pack(pady=5)
search_entry = ttk.Entry(search_frame, width=30)
search_entry.pack(padx=5)
search_button = ttk.Button(search_frame, text="Search", command=search_items)
search_button.pack(pady=6)

# === Inside your frame-based page switch system ===
frame_daily_sales = ttk.Frame(frame_main)  # Use the correct parent, like root or container
# Do not pack/grid it here if you show/hide it later, just define it

# === Inner frame to hold Treeview and scrollbars ===
tree_container = ttk.Frame(frame_daily_sales)
tree_container.pack(fill='both', expand=True, side='top')

# Scrollbars
vbar = tk.Scrollbar(tree_container, orient='vertical')
hbar = tk.Scrollbar(tree_container, orient='horizontal')

# Treeview setup
columns_sales = ("ID", "Item ID", "Name", "Manufacturer", "Product Code", "Image Path", "Description", "Part Number", "Quantity", "Total", "Date", "Client", "Payment")
sales_tree = ttk.Treeview(tree_container, columns=columns_sales, yscrollcommand=vbar.set, xscrollcommand=hbar.set, selectmode=tk.EXTENDED, show="tree headings")

sales_tree.heading("#0", text="Select")
sales_tree.column("#0", width=60)
sales_tree.image_unchecked = unchecked
sales_tree.image_checked = checked

for col in columns_sales:
    sales_tree.heading(col, text=col)
    sales_tree.column(col, width=100)

# Scrollbar connections
vbar.config(command=sales_tree.yview)
hbar.config(command=sales_tree.xview)

# Grid layout inside the tree_container only
sales_tree.grid(row=0, column=0, sticky='nsew')
vbar.grid(row=0, column=1, sticky='ns')
hbar.grid(row=1, column=0, sticky='ew')

tree_container.grid_rowconfigure(0, weight=1)
tree_container.grid_columnconfigure(0, weight=1)

# === Add calendar and total label below tree, inside same page frame ===
bottom_controls = ttk.Frame(frame_daily_sales)
bottom_controls.pack(side='top', fill='x', pady=10)
date_frame = ttk.LabelFrame(bottom_controls,text="Search By Date")
date_frame.pack(side='top', padx=5)
cal = DateEntry(date_frame, width=12, borderwidth=2)
cal.pack()
get_date_button = ttk.Button(date_frame, text="Get Selected Date", command=search_by_date)
get_date_button.pack()

total_Label = tk.Label(bottom_controls, text=f"Total: 0.0", borderwidth=2, width=10, bg="white", relief="solid")
total_Label.pack(side='left', padx=5)

# === Context menu binding remains same ===
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Delete", command=lambda: sale_menu("delete"))
context_menu.add_command(label="Quantity", command=lambda: sale_menu("qty"))


sales_tree.bind("<Button-3>", daily_item_edit)
sales_tree.bind("<Button-1>", selectRow)

# Initialize database
prompt_user_for_database_if_needed()
init_db()
refresh_items()
frame_items.pack()
root.config(menu=menubar)
root.mainloop()
