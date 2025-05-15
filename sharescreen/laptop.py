# Server (Laptop) code - save as laptop_server.py
import socket
import mss
import numpy as np
import zlib
import pickle
from PIL import Image
import io
import threading
import json

class ScreenShareServer:
    def __init__(self, share_port=5000, discovery_port=5001):
        self.share_port = share_port
        self.discovery_port = discovery_port
        self.server_name = socket.gethostname()
        self.running = False
        
    def start_discovery_service(self):
        """Broadcast server presence on the network"""
        discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        discovery_socket.bind(('', self.discovery_port))
        
        print("Discovery service started")
        while self.running:
            try:
                # Wait for discovery request
                data, addr = discovery_socket.recvfrom(1024)
                if data == b'DISCOVER_SCREEN_SHARE_SERVER':
                    # Get all network interfaces
                    hostname = socket.gethostname()
                    ip_addresses = []
                    for ip in socket.gethostbyname_ex(hostname)[2]:
                        if not ip.startswith('127.'):  # Exclude localhost
                            ip_addresses.append(ip)
                    
                    # Send server info
                    server_info = {
                        'name': self.server_name,
                        'ip_addresses': ip_addresses,
                        'port': self.share_port
                    }
                    discovery_socket.sendto(json.dumps(server_info).encode(), addr)
                    print(f"Responded to discovery request from {addr}")
            except Exception as e:
                print(f"Discovery error: {e}")
                
    def start_screen_share(self):
        """Handle screen sharing"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', self.share_port))
        server_socket.listen(1)
        print(f"Screen share server started on port {self.share_port}")
        
        sct = mss.mss()
        
        while self.running:
            client_socket, addr = server_socket.accept()
            print(f"Client connected from {addr}")
            
            try:
                while self.running:
                    # Capture screen
                    screen = sct.grab(sct.monitors[1])
                    
                    # Convert and resize
                    img = Image.frombytes('RGB', screen.size, screen.rgb)
                    img = img.resize((1024, 576))
                    
                    # Convert to bytes and compress
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='JPEG', quality=70)
                    compressed = zlib.compress(img_bytes.getvalue(), level=3)
                    
                    # Send size and data
                    message_size = len(compressed)
                    client_socket.send(message_size.to_bytes(8, byteorder='big'))
                    client_socket.send(compressed)
                    
            except (ConnectionResetError, BrokenPipeError):
                print("Client disconnected")
                client_socket.close()
    
    def start(self):
        """Start both discovery and screen sharing services"""
        self.running = True
        
        # Start discovery service in a separate thread
        discovery_thread = threading.Thread(target=self.start_discovery_service)
        discovery_thread.daemon = True
        discovery_thread.start()
        
        # Start screen sharing in main thread
        self.start_screen_share()
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    server = ScreenShareServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
        print("\nServer stopped")