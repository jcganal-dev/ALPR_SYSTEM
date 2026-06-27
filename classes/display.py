import queue
import numpy as np
import time
import cv2
import datetime
import os 
import asyncio
import Utils.Commons as Commons
from classes import Configs
import math
from collections import deque

class Display:
    def __init__(self, stop_event, data_to_send, main_loop, camera1_stream_queue, camera2_stream_queue, send_data_dashboard, send_data_live_video=None, send_notification_to_main=None):
        self.stop_event = stop_event
        self.data_to_send = data_to_send
        self.main_loop = main_loop
        self.camera1_stream_queue = camera1_stream_queue
        self.camera2_stream_queue = camera2_stream_queue
        self.send_data_dashboard = send_data_dashboard
        self.send_data_live_video = send_data_live_video
        self.send_notification_to_main = send_notification_to_main
    
    def display_thread(self, camera1_frames=queue.Queue, camera2_frames=queue.Queue, db_queue=queue.Queue, notif_queue=queue.Queue):
        metrics_graphs = {
            'camera1_total' : [],
            'camera2_total' : [],
            'camera1_capture': [],
            'camera2_capture': [],
            'camera1_detection': [],
            'camera2_detection': [],
            'camera1_ocr': [],
            'camera2_ocr': [],
            'camera1_display': [],
            'camera1_db_worker': [],
            'cam1_start' : [],
            'cam2_start' : [],
        }
        graph_memory_size = 100
        for key, _ in metrics_graphs.items():
            metrics_graphs[key] = deque(maxlen=graph_memory_size)
            for i in range(graph_memory_size):
                metrics_graphs[key].append(0)
        last_frame_entry = np.zeros((Configs.DISPLAY_HEIGHT, Configs.DISPLAY_WIDTH, 3), dtype=np.uint8)
        last_frame_exit = np.zeros((Configs.DISPLAY_HEIGHT, Configs.DISPLAY_WIDTH, 3), dtype=np.uint8)
        start_time_dashboard = time.time()
        start_time_live = time.time()
        while not self.stop_event.is_set():
            start_time = time.perf_counter()
            try:
                camera1_frame, camera1_results, camera1_detections, camera1_ret = camera1_frames.get(timeout=0.01)
            except queue.Empty:
                camera1_frame = np.copy(last_frame_entry)
                camera1_detections = 0
                camera1_results = 0
                camera1_ret = False
            try:
                camera2_frame, camera2_results, camera2_detections, camera2_ret = camera2_frames.get(timeout=0.01)
            except queue.Empty:
                camera2_frame = np.copy(last_frame_exit)
                camera2_detections = 0
                camera2_results = 0
                camera2_ret = False
            detections = [camera1_detections,camera2_detections]
            results = [camera1_results,camera2_results]
            frames = [camera1_frame,camera2_frame]
            name = ['camera1','camera2']
            for i in range(len(results)):
                if name[i] == 'camera1':
                    Configs.metrics['camera1_total'] = (time.perf_counter() - Configs.metrics['cam1_start'])*1000
                if name[i] == 'camera2':
                    Configs.metrics['camera2_total'] = (time.perf_counter() - Configs.metrics['cam2_start'])*1000
                current_detection = detections[i]
                current_result = results[i]
                current_frame = frames[i]
                current_frame_for_saving = frames[i].copy()
                frame_height, frame_width, _ = current_frame.shape
                y_offset = 0
                x_offset = 2
                graph_length = int(frame_width*0.3)
                graph_height = int(frame_height*0.10)
                font_size = 2
                thickness = 6
                if name[i]=='camera2':
                    font_size = font_size/1.5
                    thickness = thickness//2
                if Configs.graphs:
                        
                    for metric_name, value in Configs.metrics.items():
                        if name[i] == 'camera1' and not camera1_ret:
                            continue
                        if name[i] == 'camera2' and not camera2_ret:
                            continue
                        metric_parts = metric_name.split('_')
                        
                        if metric_parts[0] == name[i]:
                            current_graph = metrics_graphs[metric_name]
                            current_graph.append(value)
                            graph_arr = np.array(current_graph)
                            graph_peak = np.max(graph_arr)
                            max_point = max(graph_peak, 100)
                            
                            point_x_mult = (graph_height * 0.9) / max_point
                            point_y_mult = graph_length / graph_memory_size
                            graph_average = np.mean(graph_arr[-20:]) if len(graph_arr) >= 20 else np.mean(graph_arr)
                            
                            average_color = (0, 255, 0) if graph_average < 50 else (0, 255, 255) if graph_average < 100 else (0, 0, 255)
                            peak_color = (0, 255, 0) if graph_peak < 50 else (0, 255, 255) if graph_peak < 100 else (0, 0, 255)
                            
                            metric_label = ' '.join(metric_parts[1:])
                            cv2.putText(current_frame, f"{metric_label}: {graph_average:.2f}ms", (10 + x_offset, y_offset + (frame_height // 36)), cv2.FONT_HERSHEY_SIMPLEX, font_size, average_color, thickness)
                            cv2.putText(current_frame, f"peak: {graph_peak:.2f}ms", (10 + x_offset, y_offset + (frame_height // 36) * 2), cv2.FONT_HERSHEY_SIMPLEX, font_size, peak_color, thickness)
                            cv2.rectangle(current_frame, (x_offset, y_offset), (x_offset + graph_length, y_offset + graph_height), (0, 255, 0), 2)
                            
                            num_points = len(graph_arr)
                            if num_points > 1:
                                x_coords = (np.arange(num_points) * point_y_mult + x_offset).astype(np.int32)
                                y_coords = (y_offset + graph_height - (graph_arr * point_x_mult)).astype(np.int32)
                                
                                points = np.stack((x_coords, y_coords), axis=1).reshape((-1, 1, 2))
                                
                                cv2.polylines(current_frame, [points], isClosed=False, color=(0, 255, 0), thickness=3, lineType=cv2.LINE_AA)
                            
                            y_offset += graph_height
                
                if Configs.debugs:
                    y_point = int(frame_height*Configs.ALLOWED_SPAWNPOINT_FROM_BOTTOM)
                    if name[i] == 'camera1':
                        current_frame = cv2.rectangle(current_frame, (0,0),(int(frame_width*Configs.ALLOWED_FROM_LEFT),frame_height), (0,0,0),-1)
                        current_frame = cv2.line(current_frame,(int(frame_width*Configs.ALLOWED_FROM_LEFT),frame_height-y_point),(frame_width,frame_height-y_point),(0,0,255),3)
                    else:
                        current_frame = cv2.rectangle(current_frame, (int(frame_width*Configs.ALLOWED_FROM_RIGHT),0),(frame_width,frame_height), (0,0,0),-1)
                        current_frame = cv2.line(current_frame,(0,frame_height-y_point),(frame_width,frame_height-y_point), (0,0,255), 3)
                db_worker_started = False
                if current_result != 0:
                    for id in current_result:
                        result = current_result[id]
                        (x1,y1,x2,y2) = result['xyxy']
                        registered = result['registered']
                        vehicle_type = result['class_name']
                        has_plate = result['has_plate']
                        plate_text = result["plate_text"]
                        owner = result["owner"].replace('_', ', ')
                        sure = result["UnSure"]
                        age = result["age"]
                        conf = result["conf"]
                        confirmed = result["confirmed"]
                        ocrs = result["ocrs"]
                        method = result["method"]
                        sx, sy = result["spawn_point"]
                        
                        width = 2560 if name[i] == 'camera2' else 3840
                        height = 1440 if name[i] == 'camera2' else 2160
                        if Configs.debugs:
                            current_frame = cv2.circle(current_frame, (sx,sy), 3, (0,255,0), 3)
                            current_frame = cv2.circle(current_frame, ((x2-x1)//2,(y1-y2)//2), 3, (255,255,0), 3)
                            fa,fb,fc,fd = result['future_xyxy']
                            fa = fa if fa > 0 else 0
                            fb = fb if fb > 0 else 0
                            fc = fc if fc < width else width
                            fd = fd if fd < height else height
                            current_frame = cv2.rectangle(current_frame, (fa,fb), (fc,fd), (255,0,0), 3)
                        
                        center_x = (x1 + x2) / 2
                        center_y = y2
                        distance = math.sqrt(math.pow(center_x - sx, 2) + math.pow(center_y - sy, 2))
                        MOVE_THRESHOLD = height * Configs.MOVE_THRESHOLD
                        if distance < MOVE_THRESHOLD:
                            if Configs.debugs:
                                current_frame = cv2.line(current_frame,(sx,sy),((x2+x1)//2,(y1+y2)//2),(0,0,255),5,cv2.LINE_AA)
                            continue
                        else:
                            if Configs.debugs:
                                current_frame = cv2.line(current_frame,(sx,sy),((x2+x1)//2,(y1+y2)//2),(0,255,0),5,cv2.LINE_AA)

                        if name[i] == 'camera1':
                            if sx <= int(frame_width*Configs.ALLOWED_FROM_LEFT):
                                continue 
                            if sy <= frame_height-int(frame_height*Configs.ALLOWED_SPAWNPOINT_FROM_BOTTOM) or (y1+y2)//2 > frame_height-int(frame_height*Configs.ALLOWED_SPAWNPOINT_FROM_BOTTOM):
                                continue
                        if name[i] == 'camera2':
                            if sx >= int(frame_width*Configs.ALLOWED_FROM_RIGHT):
                                continue 
                            if sy <= frame_height-int(frame_height*Configs.ALLOWED_SPAWNPOINT_FROM_BOTTOM) or (y1+y2)//2 > frame_height-int(frame_height*Configs.ALLOWED_SPAWNPOINT_FROM_BOTTOM):
                                continue
                        if age < Configs.MIN_AGE:
                            continue
                        text_to_display = f'{plate_text} ({owner})'
                        tts = plate_text
                        if len(plate_text) == 0: 
                            text_to_display = "Unreadable plate"
                            tts = text_to_display
                        if not has_plate and not registered: 
                            text_to_display = "No plate detected"
                            tts = text_to_display
                        rect_color = (0,0,255)
                        if not confirmed: rect_color = (0, 255, 255)
                        if registered: 
                            rect_color = (0,255,0)
                        if not sure:
                            text_to_display = f'{plate_text} ({owner}) ???'
                            rect_color = (0,255,255)
                        
                        (tw, th), _ = cv2.getTextSize(text_to_display, cv2.FONT_HERSHEY_PLAIN, 2, 2)
                        
                        # Use the persistent log_id from Commons
                        log_id = result['log_id']
                        image_path = f'./images/{log_id}--snap.png'
                        image_path_conf = f'./images/{log_id}.png'
                        image_path_mbae = f'./images/{log_id}--mbae.png'
                        
                        if y2 < sy+50:
                            if confirmed:
                                if not os.path.isfile(image_path_conf):
                                    cv2.imwrite(image_path_conf,current_frame_for_saving[y1:y2,x1:x2])
                                    Commons.save_in_database(log_id, plate_text, vehicle_type, image_path_conf, name[i], ocrs, method, db_queue)
                                    db_worker_started = True
                                if os.path.isfile(image_path):
                                    os.remove(image_path)
                                if os.path.isfile(image_path_mbae):
                                    os.remove(image_path_mbae)
                            else:
                                if not os.path.isfile(image_path) and not os.path.isfile(image_path_conf):
                                    cv2.imwrite(image_path,current_frame_for_saving[y1:y2,x1:x2])
                                    Commons.save_in_database(log_id, "", vehicle_type, image_path, name[i], ocrs, method, db_queue)
                                    db_worker_started = True
                                if os.path.isfile(image_path_mbae):
                                    os.remove(image_path_mbae)
                        else:
                            if not os.path.isfile(image_path_mbae) and not os.path.isfile(image_path) and not os.path.isfile(image_path_conf):
                                cv2.imwrite(image_path_mbae,current_frame_for_saving[y1:y2,x1:x2])
                                Commons.save_in_database(log_id, "", vehicle_type, image_path_mbae, name[i], ocrs, method, db_queue)
                                db_worker_started = True
                        
                        current_frame = cv2.rectangle(current_frame, (x1,y1), (x2,y2), rect_color, 3)
                        current_frame = cv2.rectangle(current_frame, (x1,y1),(x1+tw+10,y1+th+10),rect_color,-1)
                        current_frame = cv2.putText(current_frame, text_to_display, (x1+5,y1+5+th), cv2.FONT_HERSHEY_PLAIN, 2, (255,0,0), 2)
                        current_time = datetime.datetime.now()
                        vehicle_data = {}
                        vehicle_data['plate'] = tts
                        vehicle_data['vehicle_type'] = vehicle_type
                        vehicle_data['owner'] = owner
                        vehicle_data['status'] = "Registered" if registered else "No Gate Pass"
                        vehicle_data['text_to_display'] = text_to_display
                        vehicle_data['date'] = current_time.strftime("%m/%d/%Y")
                        vehicle_data['time'] = current_time.strftime("%I:%M %p")
                        vehicle_data['int_min'] = current_time.minute + current_time.hour*60
                        vehicle_data['confirmed'] = confirmed
                        vehicle_data['ocrs'] = ocrs
                        vehicle_data['name'] = name[i]
                        vehicle_data['method'] = method
                        vehicle_data['visible'] = True
                        self.data_to_send[f'{log_id}'] = vehicle_data
                if current_detection != 0  and Configs.debugs:
                    if i==0:
                        camera1_frame = camera1_detections.plot()
                    else:
                        camera2_frame = camera2_detections.plot()
            if not db_worker_started:
                Configs.metrics['camera1_db_worker'] = 0.0
            end_time = time.perf_counter()
            if Configs.graphs:
                Configs.metrics['camera1_display'] = (end_time - start_time) * 1000

            if time.time() - start_time_dashboard >= 2:
                start_time_dashboard = time.time()
                if self.main_loop:
                    asyncio.run_coroutine_threadsafe(self.send_data_dashboard(), self.main_loop)
            
            if time.time() - start_time_live >= 0.1:
                start_time_live = time.time()
                if self.main_loop and self.send_data_live_video:
                    asyncio.run_coroutine_threadsafe(self.send_data_live_video(), self.main_loop)
                    try:
                        message = notif_queue.get_nowait()
                        asyncio.run_coroutine_threadsafe(self.send_notification_to_main(message, 'warning'), self.main_loop)
                    except:
                        pass

            try:
                last_frame_entry = camera1_frame
                self.camera1_stream_queue.put_nowait(camera1_frame)
            except queue.Full:
                pass
            try:
                last_frame_exit = camera2_frame
                self.camera2_stream_queue.put_nowait(camera2_frame)
            except queue.Full:
                pass

        print("Display thread stopped.")