# server_pi_keyboard.py - Chạy trên Raspberry Pi
import socket
import threading
from zeroconf import ServiceInfo, Zeroconf
import logging
from keyboard_server import keyboard
import time

class KeyboardServer:
    def __init__(self, port=12345):
        self.port = port
        self.clients = []
        self.clients_lock = threading.Lock()
        
        # Initialize server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        
        # Initialize Zeroconf for service broadcasting
        self.zeroconf = Zeroconf()
        self.register_zeroconf_service()
        
        # Flag for main loop control
        self.running = True
        
        print(f"Server started on port {self.port}")

    def get_local_ip(self):
        try:
            # Create a socket to determine the IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't need to be reachable
            s.connect(('8.8.8.8', 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"Error getting IP: {e}")
            return '127.0.0.1'

    def register_zeroconf_service(self):
        # Get the actual network IP address
        local_ip = self.get_local_ip()
        hostname = socket.gethostname()
        
        print(f"Server hostname: {hostname}")
        print(f"Server IP: {local_ip}")
        
        self.service_info = ServiceInfo(
            "_keyboard._tcp.local.",
            "KeyboardControl._keyboard._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=self.port,
            properties={},
            server=f"{hostname}.local."
        )
        
        try:
            self.zeroconf.register_service(self.service_info)
            print(f"Service registered on {local_ip}:{self.port}")
            print("Waiting for computers to connect...")
        except Exception as e:
            print(f"Error registering service: {e}")

    def handle_client(self, client_socket, address):
        print(f"New connection from {address}")
        with self.clients_lock:
            self.clients.append(client_socket)
        
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:  # Connection closed by client
                    break
        except:
            print(f"Client {address} disconnected")
        finally:
            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            client_socket.close()

    def accept_connections(self):
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
            except:
                break

    def broadcast_command(self, command):
        with self.clients_lock:
            disconnected_clients = []
            for client in self.clients:
                try:
                    client.send(command.encode())
                except:
                    disconnected_clients.append(client)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                self.clients.remove(client)
            
            active_clients = len(self.clients)
            print(f"Command '{command}' sent to {active_clients} client(s)")

    def process_keyboard(self):
        print("\nKeyboard controls:")
        print("→ or 'D' or 'L': Next slide")
        print("← or 'A' or 'H': Previous slide")
        print("Q: Quit server")
        print("\nReady to receive keyboard input!")
        
        keyboard.on_press_key('right', lambda _: self.broadcast_command("NEXT"))
        keyboard.on_press_key('d', lambda _: self.broadcast_command("NEXT"))
        keyboard.on_press_key('l', lambda _: self.broadcast_command("NEXT"))
        
        keyboard.on_press_key('left', lambda _: self.broadcast_command("PREV"))
        keyboard.on_press_key('a', lambda _: self.broadcast_command("PREV"))
        keyboard.on_press_key('h', lambda _: self.broadcast_command("PREV"))
        
        keyboard.on_press_key('q', lambda _: self.stop())
        
        while self.running:
            time.sleep(0.1)

    def start(self):
        accept_thread = threading.Thread(target=self.accept_connections)
        accept_thread.daemon = True
        accept_thread.start()
        
        keyboard_thread = threading.Thread(target=self.process_keyboard)
        keyboard_thread.daemon = True
        keyboard_thread.start()
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        print("\nShutting down server...")
        self.running = False
        
        with self.clients_lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        self.cleanup()

    def cleanup(self):
        try:
            self.zeroconf.unregister_service(self.service_info)
            self.zeroconf.close()
            self.server_socket.close()
            print("Server stopped")
        except Exception as e:
            print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    try:
        print("Note: You might need to run this script with sudo for keyboard input")
        print("Example: sudo python3 server_pi_keyboard.py")
        
        server = KeyboardServer()
        server.start()
    except Exception as e:
        print(f"Error: {str(e)}")
        print("If you get permission errors, try running with sudo")