from azure.storage.blob import BlobServiceClient

connection_string = ""
try:
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    print("Connection successful!")
except Exception as e:
    print(f"Connection failed: {e}")
