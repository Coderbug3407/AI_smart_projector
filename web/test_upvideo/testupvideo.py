import os
import time
import threading
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

# Azure connection details
connection_string = ""
container_name = "videos"
video_folder_path = "/home/coderbug/workspace/AI_presentor/web/test1video/"

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Check if the container exists, or create it
try:
    container_client.get_container_properties()
    print(f"Container '{container_name}' already exists.")
except Exception as e:
    try:
        container_client.create_container()
        print(f"Container '{container_name}' created.")
    except Exception as create_exception:
        print("Error creating container:", create_exception)

# Function to check if the file already exists in Blob Storage
def file_exists_in_blob_storage(blob_name):
    blob_client = container_client.get_blob_client(blob_name)
    try:
        # Try to get the blob's properties to check if it exists
        blob_client.get_blob_properties()
        return True
    except Exception as e:
        return False

# Function to upload a file to Azure Blob Storage
def upload_video(file_path):
    video_blob_name = os.path.basename(file_path)
    
    # Check if file already exists in Blob Storage
    if file_exists_in_blob_storage(video_blob_name):
        print(f"File '{video_blob_name}' already exists in Blob Storage. Skipping upload.")
        return

    try:
        blob_client = container_client.get_blob_client(video_blob_name)
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        print(f"Uploaded {video_blob_name} to {container_name}.")

        # Delete the file after successful upload
        delete_file(file_path)
    except Exception as e:
        print("Error uploading video:", e)

# Function to delete a file from the folder
def delete_file(file_path):
    try:
        os.remove(file_path)
        print(f"Deleted file: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

# Monitor folder for new video files
def monitor_folder():
    while True:
        # List all files in the folder
        for filename in os.listdir(video_folder_path):
            file_path = os.path.join(video_folder_path, filename)
            
            # Check if it's a new file and has a video extension
            if filename.endswith(('.mp4', '.avi', '.mov')):
                upload_video(file_path)
        
        # Wait before checking again (e.g., every 10 seconds)
        time.sleep(10)

# Start the folder monitoring in a separate thread
monitor_thread = threading.Thread(target=monitor_folder, daemon=True)
monitor_thread.start()

# Keep the main program running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Monitoring stopped.")
