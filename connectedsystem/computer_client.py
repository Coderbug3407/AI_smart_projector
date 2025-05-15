from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
import socket
import time
import threading
import pyautogui
import tkinter as tk
from tkinter import ttk
import logging

class GestureServiceListener(ServiceListener):
    def __init__(self):
        self.server_info = None
        self.on_service_found = None
        
    def remove_service(self, zc, type_, name):
        print(f"Service removed: {name}")
        
    def add_service(self, zc, type_, name):
        print(f"Found service: {name}")
        info = zc.get_service_info(type_, name)
        if info:
            print(f"Service info: {info}")
            server_ip = socket.inet_ntoa(info.addresses[0])
            print(f"Service IP: {server_ip}")
            print(f"Service port: {info.port}")
            if self.on_service_found:
                self.on_service_found(info)
            
    def update_service(self, zc, type_, name):
        pass

class GestureClient:
    def __init__(self):
        self.zeroconf = Zeroconf()
        self.listener = GestureServiceListener()
        self.listener.on_service_found = self.connect_to_server
        self.browser = ServiceBrowser(
            self.zeroconf, 
            "_keyboard._tcp.local.", 
            self.listener
        )
        
        self.connected = False
        self.socket = None
        self.status_callback = None
        self.recording_callback = None
        self.is_recording = False
        
    def connect_to_server(self, service_info):
        if self.connected:
            return
            
        try:
            server_ip = socket.inet_ntoa(service_info.addresses[0])
            server_port = service_info.port
            
            print(f"Attempting to connect to {server_ip}:{server_port}")
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # 5 second timeout
            self.socket.connect((server_ip, server_port))
            self.socket.settimeout(None)  # Remove timeout after connection
            self.connected = True
            
            if self.status_callback:
                self.status_callback(f"Connected to {server_ip}:{server_port}")
                
            receive_thread = threading.Thread(target=self.receive_commands)
            receive_thread.daemon = True
            receive_thread.start()
            
        except socket.timeout:
            if self.status_callback:
                self.status_callback("Connection timed out")
            self.connected = False
        except ConnectionRefusedError:
            if self.status_callback:
                self.status_callback("Connection refused - is the server running?")
            self.connected = False
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Connection failed: {str(e)}")
            self.connected = False
            
    def receive_commands(self):
        while self.connected:
            try:
                command = self.socket.recv(1024).decode()
                if not command:  # Connection closed by server
                    raise Exception("Connection closed by server")
                print(f'{command}')   
                
                if command == "True":
                    self.is_recording = True
                    if self.recording_callback:
                        self.recording_callback(True)
                elif command == "False":
                    self.is_recording = False
                    if self.recording_callback:
                        self.recording_callback(False)
                #elif self.is_recording:  # Only process movement commands if recording
                if command == "NEXT":
                    pyautogui.press('right')
                elif command == "PREV":
                    pyautogui.press('left')
                        
            except Exception as e:
                print(f"Error receiving command: {e}")
                self.connected = False
                if self.status_callback:
                    self.status_callback("Disconnected from server")
                if self.recording_callback:
                    self.recording_callback(False)
                break
                
    def cleanup(self):
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        try:
            self.zeroconf.close()
        except:
            pass

class GestureControlGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Keyboard Control Client")
        self.root.geometry("300x200")
        
        self.client = GestureClient()
        self.client.status_callback = self.update_status
        self.client.recording_callback = self.update_recording_status
        
        self.setup_gui()
        
    def setup_gui(self):
        # Connection status
        self.status_label = ttk.Label(
            self.root, 
            text="Searching for keyboard control service..."
        )
        self.status_label.pack(pady=20)
        
        self.connection_label = ttk.Label(
            self.root, 
            text="Not Connected",
            foreground="red"
        )
        self.connection_label.pack(pady=10)
        
        # Recording status
        self.recording_label = ttk.Label(
            self.root,
            text="Not Recording",
            foreground="red"
        )
        self.recording_label.pack(pady=10)
        
        # Close button
        self.close_button = ttk.Button(
            self.root, 
            text="Close", 
            command=self.cleanup
        )
        self.close_button.pack(pady=10)
        
    def update_recording_status(self, is_recording):
        if is_recording:
            self.recording_label.config(
                text="Recording",
                foreground="green"
            )
        else:
            self.recording_label.config(
                text="Not Recording",
                foreground="red"
            )
        
    def update_status(self, message):
        self.status_label.config(text=message)
        self.connection_label.config(
            text="Connected",
            foreground="green"
        ) if "Connected to" in message else self.connection_label.config(
            text="Not Connected",
            foreground="red"
        )
        
    def cleanup(self):
        self.client.cleanup()
        self.root.quit()
        
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.root.mainloop()

if __name__ == "__main__":
    app = GestureControlGUI()
    app.run()