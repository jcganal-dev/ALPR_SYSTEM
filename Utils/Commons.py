import os
import queue
import datetime
from classes import Configs

def identify_persisting_objects(old_results, results, did, camera_name):
    """
    Updates the state of detected objects using a custom IoU-based tracker.
    Inherits metadata, stabilizes initial detections, and preserves unique Log IDs.
    """
    results_copy = results.copy()
    count = did
    
    # FIX: Track matched IDs to prevent multiple current objects from "stealing" the same old ID
    matched_old_ids = set()

    # Ensure we start counting from the highest existing ID
    if old_results:
        count = max(count, max(old_results.keys()))

    for current_id in results_copy:
        current_vehicle = results_copy[current_id]
        a, b, c, d = current_vehicle['xyxy']
        vehicle_area = (c - a) * (d - b)
        
        found_match = False
        matched_old_id = None
        
        # OLD LOGIC (Unrestricted matching):
        # for old_id in old_results:
        
        # NEW LOGIC: Check if old_id was already claimed in this frame
        for old_id in old_results:
            if old_id in matched_old_ids:
                continue
                
            old_vehicle = old_results[old_id]
            e, f, g, h = old_vehicle['xyxy']
            if Configs.USE_BBOX_PREDICTION_LOGIC:
                e, f, g, h = old_vehicle['future_xyxy']
            
            # Intersection coordinates
            ni, nj, nk, nl = max(a, e), max(b, f), min(c, g), min(d, h)
            
            if nk > ni and nl > nj:
                intersection_area = (nk - ni) * (nl - nj)
                shape_tolerance = Configs.OBJECT_PERSISTENCE_SHAPE_TOLERANCE
                iou_tolerance = Configs.OBJECT_PERSISTENCE_IOU_MIN
                current_vehicle_width = (c-a)
                current_vehicle_height = (d-b)
                old_vehicle_width = (g-e)
                old_vehicle_height = (h-f)
                # if intersection_area / vehicle_area > Configs.OBJECT_PERSISTENCE_IOU_MIN:
                if (intersection_area / vehicle_area > iou_tolerance and 
                    min(current_vehicle_width, old_vehicle_width) / max(current_vehicle_width, old_vehicle_width) > shape_tolerance and 
                    min(current_vehicle_height, old_vehicle_height) / max(current_vehicle_height, old_vehicle_height) > shape_tolerance and 
                    current_vehicle['class_name'] == old_vehicle['class_name']):
                    matched_old_id = old_id
                    found_match = True
                    break
        
        if found_match:
            # Mark this ID as claimed for this frame
            matched_old_ids.add(matched_old_id)
            
            new_data = results.pop(current_id)
            old_data = old_results[matched_old_id]
            
            # Inherit and update state
            new_data['age'] = old_data['age'] + 1
            new_data['log_id'] = old_data['log_id']
            new_data['spawn_point'] = old_data['spawn_point']
            oa,ob,oc,od = old_data['xyxy']
            pa = int(a + (a-oa))
            pb = int(b + (b-ob))
            pc = int(c + (c-oc))
            pd = int(d + (d-od))
            new_data['future_xyxy'] = [pa, pb, pc, pd]
            
            # Preserve timing info
            new_data['confirmed'] = old_data['confirmed']
            new_data['registered'] = old_data['registered']
            new_data['plate_text'] = old_data['plate_text']
            new_data['owner'] = old_data['owner']
            new_data['has_plate'] = old_data['has_plate'] or new_data['has_plate']
            new_data['method'] = old_data['method']
            new_data['ocrs'] = old_data['ocrs']

            # Bounding box NO smoothing
            new_data['xyxy'] = (a, b, c, d)

            results[matched_old_id] = new_data
        else:
            # Object is new - assign a persistent ID and generate log_id
            count += 1
            new_id = count
            new_data = results.pop(current_id)
            
            new_data['age'] = 1
            # Initial spawn point is the center of the first detection
            new_data['spawn_point'] = (a + (c - a) // 2, d)
            # new_data['spawn_point'] = (a + (c - a) // 2, b + (d - b) // 2)
            
            # GENERATE LOG ID ONLY ONCE
            timestamp = datetime.datetime.now().strftime("%d-%m-%Y-%I-%M-%p")
            new_data['log_id'] = f"{camera_name}-{timestamp}-{new_id}"
            
            results[new_id] = new_data
            
    return results, count

def assign_plate_to_vehicles(vehicles, plates):
    for vid in vehicles:
        vehicle = vehicles[vid]
        vx1, vy1, vx2, vy2 = vehicle['xyxy']
        temp_plate = None
        for pid in plates:
            plate = plates[pid]
            px1, py1, px2, py2 = plate['xyxy']
            if px1 < vx1:
                continue
            if py1 < vy1:
                continue
            if px2 > vx2:
                continue
            if py2 > vy2:
                continue
            temp_plate = plate['xyxy']
            break
        vehicle['plate_xyxy'] = temp_plate
        vehicle['has_plate'] = False if temp_plate is None else True
    return vehicles

def compress(time_list, dir_list):
    camera1_count = []
    camera2_count = []
    labels = []
    if not time_list:
        return camera1_count, camera2_count, labels
    item = time_list[0]
    while len(time_list) > 0:
        n = 0
        m = 0
        labels.append(item)
        while time_list.__contains__(item):
            p = time_list.index(item)
            if dir_list[p] == 'camera1':
                n += 1
            else:
                m += 1
            time_list.remove(item)
            del dir_list[p]
        camera1_count.append(n)
        camera2_count.append(m)
        item += 1
    return (camera1_count, camera2_count, labels)

def delete_all_files_in_directory(directory_path):
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}")
        else:
            os.mkdir(directory_path)

def save_in_database(id, plate_text, vehicle_type, image_path, name, ocrs, method, db_queue):
    try:
        task = {
            'id': id,      
            'plate': plate_text,
            'type': vehicle_type,
            'path': image_path,
            'cam': name,
            'ocrs': ocrs,
            'method': method
        }
        db_queue.put_nowait(task)
    except queue.Full:
        print("DB Queue full, skipping log to save memory.")
        pass