import cv2
import threading
import queue
import time
from datetime import datetime
import pyaudio
import wave
import numpy as np
import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

class CameraRecorder:
    def __init__(self):
        self.frame_queue = queue.Queue(maxsize=300)  # Buffer for ~10 seconds at 30fps
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.is_running = True
        self.writer = None
        self.recording_thread = None
        self.audio_thread = None
        self.last_toggle_time = 0
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.audio = pyaudio.PyAudio()
        self.audio_frames = []
        
    def start_audio_recording(self, filename):
        """Start recording audio in a separate thread"""
        self.audio_stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        self.audio_filename = filename
        self.audio_frames = []
        self.audio_thread = threading.Thread(target=self.audio_recording_thread)
        self.audio_thread.start()
    
    def audio_recording_thread(self):
        """Thread function for audio recording"""
        while self.is_recording and self.is_running:
            try:
                data = self.audio_stream.read(self.CHUNK)
                self.audio_frames.append(data)
            except Exception as e:
                print(f"Audio recording error: {e}")
                break
    
    def save_audio(self):
        """Save recorded audio to WAV file"""
        if self.audio_frames:
            wf = wave.open(self.audio_filename, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.audio_frames))
            wf.close()
            return True
        return False
    
    def merge_audio_video(self, video_file, audio_file, output_file):
        """Merge audio and video files"""
        try:
            video = VideoFileClip(video_file)
            audio = AudioFileClip(audio_file)
            
            # If audio is longer than video, trim it
            if audio.duration > video.duration:
                audio = audio.subclip(0, video.duration)
            
            final_video = video.set_audio(audio)
            final_video.write_videofile(output_file, codec='libx264')
            
            # Close the clips
            video.close()
            audio.close()
            final_video.close()
            
            # Remove temporary files
            os.remove(video_file)
            os.remove(audio_file)
            
            return True
        except Exception as e:
            print(f"Error merging audio and video: {e}")
            return False
        
    def toggle_recording(self, frame):
        current_time = time.time()
        if current_time - self.last_toggle_time < 1:
            return
        
        self.last_toggle_time = current_time
        
        if not self.is_recording:
            self.start_recording(frame.shape[1], frame.shape[0])
        else:
            self.stop_recording()
    
    def start_recording(self, width, height):
        if not self.is_recording:
            print("Starting recording...")
            self.is_recording = True
            
            # Generate filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.video_filename = f"temp_video_{timestamp}.mp4"
            self.audio_filename = f"temp_audio_{timestamp}.wav"
            self.final_filename = f"/home/pi/cp/Interactive-projector-hand-recognizing-application-/videos/recording_{timestamp}.mp4"
            
            # Start video recording
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = cv2.VideoWriter(self.video_filename, fourcc, 30.0, (width, height))
            
            # Start audio recording
            self.start_audio_recording(self.audio_filename)
            
            # Start frame processing thread
            self.recording_thread = threading.Thread(target=self.process_frames)
            self.recording_thread.start()
    
    def process_frames(self):
        while self.is_recording and self.is_running:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                if self.writer is not None:
                    self.writer.write(frame)
            else:
                time.sleep(0.001)
    
    def stop_recording(self):
        if self.is_recording:
            print("Stopping recording...")
            self.is_recording = False
            
            # Wait for remaining frames
            while not self.frame_queue.empty():
                time.sleep(0.1)
            
            # Stop and save video
            if self.writer is not None:
                self.writer.release()
                self.writer = None
            
            # Stop and save audio
            if self.audio_stream is not None:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            
            if self.audio_thread is not None:
                self.audio_thread.join()
            
            # Save audio file
            self.save_audio()
            
            # Merge audio and video
            print("Merging audio and video...")
            self.merge_audio_video(
                self.video_filename,
                self.audio_filename,
                self.final_filename
            )
            print(f"Recording saved as: {self.final_filename}")
            
            if self.recording_thread is not None:
                self.recording_thread.join()
                self.recording_thread = None
    
    def add_frame(self, frame):
        if self.is_recording:
            # Add recording indicator
            cv2.circle(frame, (30, 30), 10, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 
                      1, (0, 0, 255), 2)
            
            if self.frame_queue.full():
                self.frame_queue.get()
            self.frame_queue.put(frame.copy())
    
    def cleanup(self):
        self.is_running = False
        if self.is_recording:
            self.stop_recording()
        
        # Cleanup audio
        self.audio.terminate()