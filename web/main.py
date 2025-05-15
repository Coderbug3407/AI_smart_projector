from flask import Flask, render_template, jsonify, request
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Azure Storage Configuration
connection_string = ""
container_name = "videos"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

def get_weekday(date_str):
    try:
        # Parse the date string to datetime object
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Return weekday (0-6, where 0 is Monday and 6 is Sunday)
        weekday = date_obj.weekday()
        # Convert to match your frontend format (where Sunday is 0)
        return (weekday + 1) % 7
    except ValueError:
        return None

def generate_sas_url(blob_name):
    sas_token = generate_blob_sas(
        account_name=blob_service_client.account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=blob_service_client.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    return f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/videos')
def get_videos():
    videos = []
    try:
        # Lấy danh sách tất cả các blob
        blobs_list = container_client.list_blobs()
        
        for blob in blobs_list:
            if blob.name.lower().endswith(('.mp4', '.webm')):
                try:
                    # Lấy thông tin chi tiết của blob
                    blob_client = container_client.get_blob_client(blob.name)
                    properties = blob_client.get_blob_properties()
                    
                    metadata = {
                        'name': blob.name,
                        'date': properties.creation_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'size': properties.size,
                        'url': f"/video/{blob.name}",
                        'download_url': f"/download/{blob.name}"
                    }
                    videos.append(metadata)
                except Exception as e:
                    print(f"Error processing blob {blob.name}: {str(e)}")
                    continue
        
        # Sắp xếp video theo ngày tạo (mới nhất trước)
        videos.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        
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
    video_url = generate_sas_url(video_name)
    return jsonify({'url': video_url})

@app.route('/download/<path:video_name>')
def download_video(video_name):
    download_url = generate_sas_url(video_name)
    return jsonify({'url': download_url})

if __name__ == '__main__':
    app.run(debug=True)
