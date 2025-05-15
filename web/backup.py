from flask import Flask, render_template, jsonify
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from flask_cors import CORS

# Khởi tạo Flask app
app = Flask(__name__)
CORS(app)

# Cấu hình Azure Storage
connection_string = ""
container_name = "videos"

# Khởi tạo dịch vụ Blob và Container Client
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

def get_weekday(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return date_obj.weekday()

def generate_sas_url(blob_name):
    try:
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )
        timestamp = int(datetime.utcnow().timestamp())
        return f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}&timestamp={timestamp}"
    except Exception as e:
        print(f"Error generating SAS URL for {blob_name}: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/videos')
def get_videos():
    videos = []
    try:
        # Lấy danh sách tất cả các blob
        blobs_list = container_client.list_blobs()
        
        # Xử lý từng blob
        for blob in blobs_list:
            if blob.name.lower().endswith(('.mp4', '.webm')):
                try:
                    # Lấy thông tin chi tiết của blob
                    blob_client = container_client.get_blob_client(blob.name)
                    properties = blob_client.get_blob_properties()
                    
                    metadata = {
                        'name': blob.name,
                        'date': properties.creation_time.strftime('%Y-%m-%d'),
                        'size': properties.size,
                        'url': f"/video/{blob.name}",
                        'download_url': f"/download/{blob.name}"
                    }
                    videos.append(metadata)
                except Exception as e:
                    print(f"Error processing blob {blob.name}: {str(e)}")
                    continue
        
        # Sắp xếp video theo ngày tạo (mới nhất trước)
        videos.sort(key=lambda x: x['date'], reverse=True)
        
        # Thêm cache control headers
        response = jsonify(videos)
        response.headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        })
        return response
    except Exception as e:
        print(f"Error fetching videos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/video/<path:video_name>')
def stream_video(video_name):
    try:
        # Kiểm tra sự tồn tại của blob
        blob_client = container_client.get_blob_client(video_name)
        if not blob_client.exists():
            return jsonify({'error': 'Video not found'}), 404
            
        video_url = generate_sas_url(video_name)
        response = jsonify({'url': video_url})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception as e:
        print(f"Error streaming video {video_name}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:video_name>')
def download_video(video_name):
    try:
        # Kiểm tra sự tồn tại của blob
        blob_client = container_client.get_blob_client(video_name)
        if not blob_client.exists():
            return jsonify({'error': 'Video not found'}), 404
            
        download_url = generate_sas_url(video_name)
        response = jsonify({'url': download_url})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception as e:
        print(f"Error generating download URL for {video_name}: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Kiểm tra kết nối Azure Storage khi khởi động
    try:
        container_client.get_container_properties()
        print(f"Successfully connected to container: {container_name}")
    except Exception as e:
        print(f"Error connecting to Azure Storage: {str(e)}")
        
    app.run(debug=True, host='0.0.0.0', port=5000)
