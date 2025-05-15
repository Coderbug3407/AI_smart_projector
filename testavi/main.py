from flask import Flask, render_template, jsonify, request, Response
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from flask_cors import CORS
import mimetypes

app = Flask(__name__)
CORS(app)

# Azure Storage Configuration
connection_string = ""
container_name = "videos"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

# Add Xvid MIME type support
mimetypes.add_type('video/xvid', '.xvid')
mimetypes.add_type('video/x-msvideo', '.avi')

def get_weekday(date_str):
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        weekday = date_obj.weekday()
        return (weekday + 1) % 7
    except ValueError:
        return None

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
        return f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
    except Exception as e:
        print(f"Error generating SAS URL: {str(e)}")
        return None

def get_mime_type(filename):
    mime_type = mimetypes.guess_type(filename)[0]
    if not mime_type:
        if filename.lower().endswith('.xvid'):
            return 'video/xvid'
        elif filename.lower().endswith('.avi'):
            return 'video/x-msvideo'
        else:
            return 'video/mp4'  # Default fallback
    return mime_type

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/videos')
def get_videos():
    try:
        videos = []
        blobs_list = container_client.list_blobs()
        
        selected_day = request.args.get('day')
        
        for blob in blobs_list:
            if blob.name.lower().endswith(('.mp4', '.webm', '.avi', '.xvid')):
                try:
                    blob_client = container_client.get_blob_client(blob.name)
                    properties = blob_client.get_blob_properties()
                    
                    video_date = properties.creation_time
                    video_weekday = (video_date.weekday() + 1) % 7
                    
                    if selected_day and str(video_weekday) != selected_day and selected_day != 'all':
                        continue
                    
                    metadata = {
                        'name': blob.name,
                        'date': properties.creation_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'size': properties.size,
                        'weekday': video_weekday,
                        'type': get_mime_type(blob.name)
                    }
                    videos.append(metadata)
                except Exception as e:
                    print(f"Error processing blob {blob.name}: {str(e)}")
                    continue
        
        videos.sort(key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d %H:%M:%S'), reverse=True)
        
        response = jsonify(videos)
        response.headers.update({
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        })
        return response
    except Exception as e:
        print(f"Error in get_videos: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/video/<path:video_name>')
def stream_video(video_name):
    try:
        video_url = generate_sas_url(video_name)
        if video_url:
            return jsonify({
                'url': video_url,
                'type': get_mime_type(video_name)
            })
        return jsonify({'error': 'Failed to generate video URL'}), 500
    except Exception as e:
        print(f"Error in stream_video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:video_name>')
def download_video(video_name):
    try:
        download_url = generate_sas_url(video_name)
        if download_url:
            return jsonify({
                'url': download_url,
                'filename': video_name,
                'type': get_mime_type(video_name)
            })
        return jsonify({'error': 'Failed to generate download URL'}), 500
    except Exception as e:
        print(f"Error in download_video: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)
