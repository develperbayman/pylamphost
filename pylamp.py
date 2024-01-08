import os
import webbrowser
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import socket
import requests
import sqlite3

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'databases', 'pylamp.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DATABASE_FOLDER'] = 'databases'
db = SQLAlchemy(app)

# Flask route to display a simple message
@app.route('/')
def home():
    return render_template('index.html')

# Flask route to handle import/export operations
@app.route('/import_export/<operation>', methods=['POST'])
def import_export_operation(operation):
    if operation == 'import':
        import_sql()
    elif operation == 'export':
        export_sql()
    return redirect('/')

# Function to handle importing SQL file
def import_sql():
    file_path = filedialog.askopenfilename(filetypes=[("SQL files", "*.sql")])
    if file_path:
        with open(file_path, 'r') as file:
            sql_script = file.read()
            connection = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            cursor = connection.cursor()
            cursor.executescript(sql_script)
            connection.commit()
            connection.close()

# Function to handle exporting SQL file
def export_sql():
    file_path = filedialog.asksaveasfilename(defaultextension=".sql", filetypes=[("SQL files", "*.sql")])
    if file_path:
        connection = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        with open(file_path, 'w') as file:
            for table in tables:
                cursor.execute(f"SELECT * FROM {table[1]}")
                result = cursor.fetchall()
                for row in result:
                    file.write(f"INSERT INTO {table[1]} VALUES {str(row)};\n")
        connection.close()

# Function to clear all tables
def clear_tables():
    connection = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"DELETE FROM {table[0]}")
    connection.commit()
    connection.close()

# Function to update IP addresses in the status bar
def update_ip_addresses():
    local_ip = socket.gethostbyname(socket.gethostname())
    public_ip = requests.get('https://api64.ipify.org?format=json').json()['ip']
    ip_status_var.set(f'Local IP: {local_ip} | Public IP: {public_ip}')

# Function to start Gunicorn server
def start_server():
    global server_process
    server_process = subprocess.Popen(['gunicorn', 'pylamp:app', '-b', '0.0.0.0:5000'])

# Function to stop the server
def stop_server():
    if hasattr(globals(), 'server_process'):
        server_process.terminate()

# Function to open the default web browser to the server's address
def open_browser():
    webbrowser.open('http://127.0.0.1:5000/')

# Function to start the server and open the browser
def start_server_and_browser():
    Thread(target=start_server).start()
    open_browser()

# Function to set up the database and start the server
def initialize():
    with app.app_context():
        create_initial_database()
    update_ip_addresses()

# Function to create the initial database
def create_initial_database():
    db_uri = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    if not os.path.exists(db_uri):
        with app.app_context():
            db.create_all(bind=db.get_engine(bind=db_uri))
        messagebox.showinfo("Info", f"Database '{os.path.basename(db_uri)}' created successfully.")

# Function to create a new database
def create_database():
    database_name = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Database files", "*.db")])
    if database_name:
        with app.app_context():
            new_db_uri = f"sqlite:///{database_name}"
            db.create_all(bind=db.get_engine(bind=new_db_uri))
        messagebox.showinfo("Info", f"Database '{os.path.basename(database_name)}' created successfully.")

# Function to delete a database
def delete_database():
    database_name = filedialog.askopenfilename(filetypes=[("Database files", "*.db")])
    if database_name:
        os.remove(database_name)
        messagebox.showinfo("Info", f"Database '{os.path.basename(database_name)}' deleted successfully.")

# Tkinter setup
root = tk.Tk()
root.title("Python Web Server")

# Check if the Message table exists, if not, create it
with app.app_context():
    create_initial_database()

# Status bar
ip_status_var = tk.StringVar()
ip_status_var.set('Local IP: 127.0.0.1 | Public IP: N/A')
ip_status = tk.Label(root, textvariable=ip_status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
ip_status.pack(side=tk.BOTTOM, fill=tk.X)

# Create the menu bar
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# Create the File menu
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Exit", command=root.destroy)

# Create the Database menu
database_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Databases", menu=database_menu)
database_menu.add_command(label="Create Database", command=create_database)
database_menu.add_command(label="Delete Database", command=delete_database)

# Create the Import/Export menu
import_export_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Import/Export", menu=import_export_menu)
import_export_menu.add_command(label="Import SQL", command=import_sql)
import_export_menu.add_command(label="Export SQL", command=export_sql)

# Create the Server menu
server_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Server", menu=server_menu)
server_menu.add_command(label="Start Server", command=start_server_and_browser)
server_menu.add_command(label="Stop Server", command=stop_server)

# Create and configure the notebook
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Create a frame for the server content
content_frame = ttk.Frame(notebook)
notebook.add(content_frame, text='Content')

# Create a Text widget to display the hosted content
content_text = tk.Text(content_frame, wrap=tk.WORD, state=tk.DISABLED)
content_text.pack(fill=tk.BOTH, expand=True)

# Tkinter main loop
Thread(target=initialize).start()
root.mainloop()
