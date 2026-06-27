import cv2
import numpy as np
import queue
import os
import time
from classes import Configs

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
class Camera:
    def __init__(self, stop_event, camera_active_status):
        self.stop_event = stop_event
        self.camera_active_status = camera_active_status
    def capture_thread(self, source, output_queue, name):
        capture = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
        time_start = time.time()
        timer_started = False
        while not self.stop_event.is_set():
            if name == 'camera1':
                Configs.metrics['cam1_start'] = time.perf_counter()
            if name == 'camera2':
                Configs.metrics['cam2_start'] = time.perf_counter()
            start_time = time.perf_counter()
            ret, frame = capture.read()
            if not ret:
                self.camera_active_status[name] = False
                capture.release()
                frame = np.zeros((Configs.DISPLAY_HEIGHT, Configs.DISPLAY_WIDTH, 3), dtype=np.uint8)
                title = "Connection lost."
                (title_width, title_height), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_COMPLEX, 4, 3)
                text = "Trying to re-establish connection..."
                (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, 2, 2)
                gap = 50
                frame = cv2.putText(frame, title, ((Configs.DISPLAY_WIDTH-title_width)//2,Configs.DISPLAY_HEIGHT//2+gap//3), cv2.FONT_HERSHEY_COMPLEX,4,(255,255,255),3,cv2.LINE_AA)
                frame = cv2.putText(frame, text, ((Configs.DISPLAY_WIDTH-text_width)//2,Configs.DISPLAY_HEIGHT//2+text_height+gap//2), cv2.FONT_HERSHEY_COMPLEX,2,(255,255,255),2,cv2.LINE_AA)
                if not timer_started:
                    timer_started = True
                    time_start = time.time()
                if time.time() - time_start >= 3:
                    capture = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
                    timer_started = False
                    time_start = time.time()
                
                time.sleep(0.1)
            else:
                self.camera_active_status[name] = True
            try:
                if Configs.ULTRA_FAST_MODE:
                    output_queue.put_nowait((frame,ret))
                else:
                    output_queue.put((frame,ret), timeout=1)
            except queue.Full:
                continue
            
            if Configs.graphs:
                Configs.metrics[f'{name}_capture'] = (time.perf_counter() - start_time) * 1000
        capture.release()
        print(f"Capture thread for {source} stopped.")