# Client (Raspberry Pi) code - save as pi_client.py
import socket
import zlib
import pygame
import io
from PIL import Image

def start_client(server_host, server_port=5000):
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((1024, 576))
    pygame.display.set_caption("Screen Share Viewer")
    clock = pygame.time.Clock()
    
    # Connect to server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_host, server_port))
    print(f"Connected to server at {server_host}:{server_port}")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        try:
            # Receive data size
            msg_size = int.from_bytes(client_socket.recv(8), byteorder='big')
            
            # Receive data
            data = b''
            while len(data) < msg_size:
                packet = client_socket.recv(min(msg_size - len(data), 4096))
                if not packet:
                    break
                data += packet
            
            # Decompress data
            img_data = zlib.decompress(data)
            
            # Convert to PIL Image
            img = Image.open(io.BytesIO(img_data))
            
            # Convert to Pygame surface
            pg_img = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
            screen.blit(pg_img, (0, 0))
            pygame.display.flip()
            
            clock.tick(30)  # Limit to 30 FPS
            
        except Exception as e:
            print(f"Error: {e}")
            break
    
    pygame.quit()
    client_socket.close()

if __name__ == "__main__":
    SERVER_HOST = "192.168.2.165"  # Replace with your laptop's IP address
    start_client(SERVER_HOST)