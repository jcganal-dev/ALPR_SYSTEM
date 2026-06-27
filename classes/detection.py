from ultralytics import YOLO
from Utils import Commons
import queue
import time
import cv2
import multiprocessing
import Utils.SPCA as SPCA
from classes import Configs
import math

class Detection:
    def __init__(self, stop_event, main_loop, send_data_live_video, ready_ocr_processes):
        self.stop_event = stop_event
        self.main_loop = main_loop
        self.send_data_live_video = send_data_live_video
        self.ready_ocr_processes = ready_ocr_processes
    
    def detection_thread(self, input_queue=queue.Queue, output_queue=queue.Queue, ocr_queue=multiprocessing.Queue, ocr_results_queue=multiprocessing.Queue, thread_name=str):
        model = YOLO(Configs.MODEL_PATH, task='detect')
        detection_id = 0
        old_results = {}
        while not self.stop_event.is_set():
            start_time = time.perf_counter()
            try:
                frame, ret = input_queue.get(timeout=1)
                frame_height, _, _ = frame.shape
            except queue.Empty:
                # print(f"{thread_name} did not get anything from camera thread")
                continue
            try:
                if Configs.FAST_MODE:
                    ocr_results = ocr_results_queue.get_nowait()
                else:
                    ocr_results = ocr_results_queue.get(timeout=1)
            except queue.Empty:
                ocr_results = {}

            detections = model.predict(frame, verbose=False, conf=Configs.MIN_YOLO_CONF)[0]

            if old_results:
                detection_id = max(detection_id, max(old_results.keys()))

            vehicles = {}
            plates = {}
            
            for detection in detections.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = detection
                x1, y1, x2, y2, class_id = map(int, (x1, y1, x2, y2, class_id))
                conf = score
                class_name = model.names[int(class_id)]
                detection_id += 1

                if class_name == 'motorcycle':
                    height = y2 - y1
                    new_height = int(height * Configs.MOTORCYCLE_HEIGHT_MULTIPLIER)
                    y1 = y1 - (new_height-height)
                    if y1 < 0:
                        y1 = 0

                if class_name == 'plate':
                    plates[detection_id] = {
                        'xyxy': [x1, y1, x2, y2],
                        'score': score,
                        'class_id': class_id,
                        'class_name': class_name
                    }
                else:
                    vehicles[detection_id] = {
                        'xyxy': [x1, y1, x2, y2],
                        'score': score,
                        'class_id': class_id,
                        'class_name': class_name,
                        'plate_xyxy': None,
                        'has_plate': False,
                        'registered': False,
                        'future_xyxy': [x1,y1,x2,y2],
                        'plate_text': '',
                        'owner': '',
                        'vehicle_type': '',
                        'UnSure': True,
                        'spawn_point': (int(x2+(x1-x2)//2), y2),
                        # 'spawn_point': (int(x2+(x1-x2)//2), int(y2+(y1-y2)//2)),
                        'age': 0,
                        'conf': conf,
                        'confirmed': False,
                        'ocrs': [],
                        'method': None,
                    }
            results = Commons.assign_plate_to_vehicles(vehicles, plates)
            results, count = Commons.identify_persisting_objects(old_results, results, detection_id, thread_name)
            metriced_ocr = False
            for id in ocr_results:
                try:
                    plate_text = ocr_results[id]
                    if id in results:
                        if Configs.graphs:
                            if thread_name == 'camera1':
                                Configs.metrics[f'{thread_name}_ocr'] = (time.perf_counter() - Configs.metrics['cam1_ocr_start']) * 1000
                            if thread_name == 'camera2':
                                Configs.metrics[f'{thread_name}_ocr'] = (time.perf_counter() - Configs.metrics['cam2_ocr_start']) * 1000
                            metriced_ocr = True
                    if results[id]['confirmed'] or not results[id]['UnSure']:
                        continue
                    if len(plate_text)<6:
                        continue
                    use_advance_patterns = len(results[id]['ocrs']) > Configs.PATTERN_CHECK_PATIENCE
                    unregistered, unreading, _, unmethod, unowner = SPCA.BlackListCheck.check_registration(plate_text, pattern_check=True, prints=True, advance_patterns=use_advance_patterns)
                    check_info = f' into {unreading}' if unregistered else ''
                    
                    registered, reading, _, method, owner = (False, plate_text, plate_text, 'N/A', 'N/A')
                    if not unregistered:
                        registered, reading, _, method, owner = SPCA.RegCheck.check_registration(plate_text, pattern_check=True, prints=True, advance_patterns=use_advance_patterns)
                        check_info = f' into {reading}' if registered else ''
                    results[id]['ocrs'].append(f"{plate_text}{check_info}")
                    results[id]['owner'] = owner
                    results[id]['plate_text'] = reading
                    results[id]['registered'] = registered
                    if method != 'Similar':
                        results[id]['UnSure'] = False
                    if unregistered:
                        results[id]['method'] = unmethod
                        results[id]['owner'] = unowner
                        results[id]['plate_text'] = unreading
                        results[id]['registered'] = False
                        results[id]['confirmed'] = True
                        continue
                    if registered:
                        results[id]['method'] = method
                        results[id]['confirmed'] = True
                except:
                    pass
            
            to_ocr = {}
            for id in results:
                plate_xyxy = results[id]['plate_xyxy']
                registered = results[id]['registered']
                has_plate = results[id]['has_plate']
                conf = results[id]['conf']
                confirmed = results[id]['confirmed']
                age = results[id]['age']
                ocrs = results[id]['ocrs']
                sx, sy = results[id]['spawn_point']
                if not has_plate:
                    continue
                if plate_xyxy == None or registered:
                    continue
                if sy < frame_height-frame_height*Configs.ALLOWED_SPAWNPOINT_FROM_BOTTOM:
                    continue
                if age < Configs.MIN_AGE:
                    continue
                if confirmed:
                    continue
                if len(ocrs) >= Configs.MAX_NUMBER_OF_READS_PER_PLATE and Configs.MAX_NUMBER_OF_READS_PER_PLATE != -1:
                    continue
                center_x = (x1 + x2) / 2
                center_y = y2
                distance = math.sqrt(math.pow(center_x - sx, 2) + math.pow(center_y - sy, 2))
                MOVE_THRESHOLD = frame_height * Configs.MOVE_THRESHOLD
                if distance < MOVE_THRESHOLD:
                    continue
                x1, y1, x2, y2 = plate_xyxy
                plate_crop = frame[y1:y2,x1:x2]
            
                height = 110
                plate_crop = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                plate_crop = cv2.convertScaleAbs(plate_crop, alpha=1.0, beta=75)
                # if y2-y1 < 110:
                plate_crop = cv2.resize(plate_crop, (height*7//4,height), interpolation=cv2.INTER_CUBIC)
                to_ocr[id] = plate_crop
            try:
                
                if thread_name == 'camera1':
                    Configs.metrics['cam1_ocr_start'] = time.perf_counter()
                if thread_name == 'camera2':
                    Configs.metrics['cam2_ocr_start'] = time.perf_counter()
                if Configs.FAST_MODE:
                    ocr_queue.put_nowait(to_ocr)
                else:
                    ocr_queue.put(to_ocr, timeout=1)
            except multiprocessing.queues.Full:
                    pass
            except:
                pass
            detection_id = count
            old_results = results

            try:
                output_queue.put((frame,results,detections,ret), timeout=1)
            except queue.Full:
                continue
            
            if Configs.graphs:
                if not metriced_ocr:
                    Configs.metrics[f'{thread_name}_ocr'] = 0
                Configs.metrics[f'{thread_name}_detection'] = (time.perf_counter() - start_time) * 1000
        print("Detection thread stopped.")