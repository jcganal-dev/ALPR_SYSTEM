import queue
from classes import Configs
import Utils.DatabaseManager as DB
import time 
import asyncio
class DB_WORKER:
    def __init__(self, stop_event, data_to_send, send_data_dashboard=None, main_loop=None):
        self.stop_event = stop_event
        self.data_to_send = data_to_send
        self.send_data_dashboard = send_data_dashboard
        self.main_loop = main_loop

    # Add this near your other thread functions (e.g., after ocr_process)
    def database_worker(self, db_queue, notification_queue):
        
        print("Database worker started.")
        while not self.stop_event.is_set():
            Configs.metrics['cam1_db_worker_start'] = time.perf_counter()
            try:
                data_item = db_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            try:
                # Extract data
                id = data_item['id']  # Get the ID so we know which vehicle to update
                plate = data_item['plate']
                v_type = data_item['type']
                img_path = data_item['path']
                cam_name = data_item['cam']
                ocrs = data_item['ocrs']
                method = data_item['method']
                
                # 1. Process Database (This is the slow part, done safely here)
                status_result, detected_watchlist = DB.db.process_detection(id, plate, v_type, img_path, cam_name, ocrs, method)

                if detected_watchlist is not None:
                    notification_queue.put_nowait(detected_watchlist)
                
                # 2. Update the Live UI (data_to_send) safely
                # We try for 1 second to find the ID in the global dictionary
                for _ in range(10):
                    if id in self.data_to_send:
                        # Update the status based on what the DB returned
                        if status_result == "Registered":
                            self.data_to_send[id]['status'] = "Registered"
                        else:
                            self.data_to_send[id]['status'] = "No Gate Pass"
                        break # Success, exit retry loop
                    time.sleep(0.1) # Wait 100ms and try again
                
                # 3. Trigger Dashboard Update if callback is provided
                if self.send_data_dashboard and self.main_loop:
                    asyncio.run_coroutine_threadsafe(self.send_data_dashboard(), self.main_loop)
                
            except Exception as e:
                print(f"DB Worker Error: {e}")
            finally:
                db_queue.task_done()
            
            if Configs.graphs:
                time_end = time.perf_counter()
                Configs.metrics['camera1_db_worker'] = (time_end - Configs.metrics['cam1_db_worker_start']) * 1000
                Configs.metrics['cam1_db_worker_start'] = time_end
        print("Database worker stopped.")