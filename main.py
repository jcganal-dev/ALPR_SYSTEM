
import cv2
import threading
import queue
import numpy as np
import multiprocessing
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import Utils.ConnectionManager as cm
import Utils.DatabaseManager as DB
import Utils.SPCA as SPCA
import subprocess
from classes.camera import Camera
from classes.detection import Detection
from classes.ocr import OCR
from classes.display import Display
from classes.db_worker import DB_WORKER
from classes import Configs
import bcrypt
import concurrent.futures

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")
templates = Jinja2Templates(directory="templates")

# --- DATABASE THREADPOOL CONFIG START ---
# This executor handles database queries in the background to prevent UI freezes
db_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

async def async_db_query(query):
    """Runs a standard SQL query in the background thread pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(db_executor, DB.db.database_query, query)

async def async_db_call(func, *args):
    """Runs a specific DB function (like verify_user) in the background thread pool."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(db_executor, func, *args)
# --- DATABASE THREADPOOL CONFIG END ---

main_loop = None
ready_ocr_processes = multiprocessing.Queue()
camera_active_status = {'camera1':False,'camera2':False}

data_to_send = {}

stop_event = threading.Event()
mp_stop_event = multiprocessing.Event()
camera1_stream_queue = queue.Queue(maxsize=1)
camera2_stream_queue = queue.Queue(maxsize=1)

threads = []
ocr_processes = []

def start_processing():
    # Commons.delete_all_files_in_directory("./images")
    global threads, ocr_processes
    
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError as e: 
        print(f"Warning: {e}")


    # --- QUEUE CREATION START ---
    db_queue = queue.Queue(maxsize=100) 
    camera1_to_detection1 = queue.Queue(maxsize=10)
    camera2_to_detection2 = queue.Queue(maxsize=10)
    detection1_to_display1 = queue.Queue(maxsize=10)
    detection2_to_display2 = queue.Queue(maxsize=10)
    detection1_to_ocr1 = multiprocessing.Queue(maxsize=1)
    detection2_to_ocr2 = multiprocessing.Queue(maxsize=1)
    orc1_to_detection1 = multiprocessing.Queue(maxsize=10)
    ocr2_to_detection2 = multiprocessing.Queue(maxsize=10)
    notification_queue = queue.Queue(maxsize=10)
    # --- QUEUE CREATION END ---



    # --- THREAD INITIALIZATION START ---
    capture_thread = Camera(stop_event, camera_active_status)
    detection_thread = Detection(stop_event, main_loop, send_data_live_video, ready_ocr_processes)
    ocr_process = OCR()
    display_thread = Display(stop_event, data_to_send, main_loop, camera1_stream_queue, camera2_stream_queue, send_data_dashboard, send_data_live_video, send_notification_to_main)
    database_worker = DB_WORKER(stop_event, data_to_send, send_data_dashboard, main_loop)
    # --- THREAD INITIALIZATION END ---


    # --- THREAD AND PROCESS EXECUTION START ---
    ocr_processes = [
        multiprocessing.Process(target=ocr_process.ocr_process, args=(mp_stop_event, detection1_to_ocr1, orc1_to_detection1, ready_ocr_processes), daemon=True),
        multiprocessing.Process(target=ocr_process.ocr_process, args=(mp_stop_event, detection2_to_ocr2, ocr2_to_detection2, ready_ocr_processes), daemon=True),
    ]

    threads = [
        threading.Thread(target=capture_thread.capture_thread, args=(Configs.camera1_source_cam, camera1_to_detection1, 'camera1'), daemon=True),
        threading.Thread(target=capture_thread.capture_thread, args=(Configs.camera2_source_cam, camera2_to_detection2, 'camera2'), daemon=True),
        threading.Thread(target=detection_thread.detection_thread, args=(camera1_to_detection1, detection1_to_display1, detection1_to_ocr1, orc1_to_detection1, 'camera1'), daemon=True),
        threading.Thread(target=detection_thread.detection_thread, args=(camera2_to_detection2, detection2_to_display2, detection2_to_ocr2, ocr2_to_detection2, 'camera2'), daemon=True),
        threading.Thread(target=display_thread.display_thread, args=(detection1_to_display1, detection2_to_display2, db_queue, notification_queue), daemon=True),
        threading.Thread(target=database_worker.database_worker, args=(db_queue,notification_queue), daemon=True)
    ]

    print("Starting background processes and threads...")
    for p in ocr_processes: p.start()
    for t in threads: t.start()
    # --- THREAD AND PROCESS EXECUTION END ---

def generate_camera1_stream():
    try:
        pframe = np.zeros((Configs.STREAM_WIDTH, Configs.STREAM_HEIGHT, 3), dtype=np.uint8)
        while not stop_event.is_set():
            try:
                frame = camera1_stream_queue.get_nowait()
                pframe = frame
            except queue.Empty:
                frame = pframe
                pass

            frame = cv2.resize(frame, (Configs.STREAM_WIDTH, Configs.STREAM_HEIGHT))
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, Configs.STREAM_QUALITY])
            if not ret:
                print("Failed to encode camera1 frame.")
                continue
            
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                   frame_bytes + b'\r\n')

    except GeneratorExit:
        pass
        # print("camera1 stream client disconnected.")
    finally:
        pass
        # print("camera1 stream generator stopped.")

def generate_camera2_stream():
    try:
        pframe = np.zeros((Configs.STREAM_WIDTH, Configs.STREAM_HEIGHT, 3), dtype=np.uint8)
        while not stop_event.is_set():
            try:
                frame = camera2_stream_queue.get_nowait()
                pframe = frame
            except queue.Empty:
                frame = pframe
                pass

            frame = cv2.resize(frame, (Configs.STREAM_WIDTH, Configs.STREAM_HEIGHT))
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, Configs.STREAM_QUALITY])
            if not ret:
                print("Failed to encode camera2 frame.")
                continue
            
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n'
                   b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                   frame_bytes + b'\r\n')

    except GeneratorExit:
        pass
        # print("camera2 stream client disconnected.")
    finally:
        pass
        # print("camera2 stream generator stopped.")

class Item(BaseModel):
    data: dict

@app.get("/main", response_class=HTMLResponse)
async def main(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

@app.get("/camera1", response_class=HTMLResponse)
async def camera1(request: Request):
    return templates.TemplateResponse("camera1.html", {"request": request})

@app.get("/camera2", response_class=HTMLResponse)
async def camera2(request: Request):
    return templates.TemplateResponse("camera2.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/live_video", response_class=HTMLResponse)
async def live_video(request: Request):
    return templates.TemplateResponse("live_video.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/report_template", response_class=HTMLResponse)
async def report_template(request: Request):
    return templates.TemplateResponse("report_template.html", {"request": request})

@app.get("/logs", response_class=HTMLResponse)
async def logs(request: Request):
    return templates.TemplateResponse("logs.html", {"request": request})

@app.get("/notifications", response_class=HTMLResponse)
async def notifications(request: Request):
    return templates.TemplateResponse("notifications.html", {"request": request})

@app.get("/users", response_class=HTMLResponse)
async def users(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})

@app.get("/edit_user", response_class=HTMLResponse)
async def edit_user(request: Request):
    return templates.TemplateResponse("edit_user.html", {"request": request})

@app.get("/reset_password", response_class=HTMLResponse)
async def reset_password(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})

@app.get("/add_to_watchlist", response_class=HTMLResponse)
async def add_to_watchlist(request: Request):
    return templates.TemplateResponse("add_to_watchlist.html", {"request": request})

@app.get("/simulate", response_class=HTMLResponse)
async def simulate(request: Request):
    return templates.TemplateResponse("simulate.html", {"request": request})

@app.get("/camera1_feed")
async def camera1_feed():
    return StreamingResponse(
        generate_camera1_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/camera2_feed")
async def camera2_feed():
    return StreamingResponse(
        generate_camera2_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

class UserRegistration(BaseModel):
    userid: str
    username: str
    password: str
@app.post("/api/register_user")
async def api_register_user(user: UserRegistration):
    success = await async_db_call(DB.db.register_new_user, user.userid, user.username, user.password)
    
    if success:
        return {"status": "success", "message": "Account created successfully!"}
    else:
        return {"status": "error", "message": "Employee ID already exists or Database Error."}

@app.post("/api/get_from_database")
async def api_login(item: Item):
    purpose = item.data['purpose']
    if purpose == 'users':
        search = item.data['search']
        is_valid, message = await async_db_query("SELECT * FROM `user_table` where CONCAT(user_table.employee_id, ' ', user_table.role, '', user_table.name) LIKE '%"+search+"%' ORDER BY user_table.active DESC, user_table.last_logout DESC")
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == 'logs':
        is_valid, message = await async_db_query("SELECT DISTINCT CAST(`date_time` AS DATE) FROM `transaction_table`")
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == 'registered-summary-in-day':
        date = item.data['date']
        is_valid, message = await async_db_query("SELECT status, COUNT(status) AS count FROM transaction_table WHERE CAST(date_time AS DATE) = '"+date+"' GROUP BY status;")
        is_valid2, message2 = await async_db_query("SELECT vehicle_type, COUNT(vehicle_type) AS count FROM transaction_table WHERE CAST(date_time AS DATE) = '"+date+"' GROUP BY vehicle_type;")
        if is_valid & is_valid2:
            return {"status": "success", "message": [message,message2]}
        else:
            return {"status": "error", "message": message}

    if purpose == "get_history":
        filters = 'WHERE '
        plate = item.data['plate']
        status = item.data['status']
        offset = item.data['offset']
        vehicle_type = item.data['vehicle_type']
        gate_number = item.data['gate_number']
        date_time = item.data['date_time']
        owner = item.data['owner']
        sort_by = item.data['sort_by']
        if sort_by=='date_time':
            sort_by = 'date_time_sorter'
        sort_by_dir = item.data['sort_by_dir']
        limit = item.data['limit']
        username = item.data['username']
        if limit == -1:
            limit = ''
        else:
            limit = f'LIMIT {limit} OFFSET {str(offset)}'
        input_filter_names = ['status', 'vehicle_type', 'gate_number', 'date_time', 'full_name', 'sort_by', 'sort_by_dir']
        input_filters = [status, vehicle_type, gate_number, date_time, owner, sort_by, sort_by_dir]
        final_filters = []

        filter_count = 0
        for i in range(len(input_filters)):
            filter = input_filters[i]
            filter_name = input_filter_names[i]
            if filter != 'All' and filter != '' and filter_name != 'sort_by' and filter_name != 'sort_by_dir':
                filter_count+=1
                final_filters.append([filter_name,filter])
        if filter_count <= 0:
            filters = ''
        elif filter_count == 1:
            if final_filters[0][0] == 'full_name':
                if status == "Registered" or status == "All":
                    filters += "(transaction_table.plate_number LIKE '%" + final_filters[0][1] + "%'" + " OR CONCAT(registration_table.first_name, ' ', registration_table.last_name) LIKE '%" + final_filters[0][1] + "%')"
                else:
                    filters += "transaction_table.plate_number LIKE '%" + final_filters[0][1] + "%'"
            elif final_filters[0][0] == 'date_time':
                if final_filters[0][1] == 'Today':
                    filters += "DATE(transaction_table." + final_filters[0][0] + ") = CURDATE()"
                elif final_filters[0][1] == 'Yesterday':
                    filters += "DATE(transaction_table." + final_filters[0][0] + ") = CURDATE()-1"
                elif final_filters[0][1] == 'This Week':
                    filters += "YEARWEEK(DATE(transaction_table." + final_filters[0][0] + ")) = YEARWEEK(CURDATE())"
                elif final_filters[0][1] == 'This Month':
                    filters += "DATE_FORMAT(transaction_table." + final_filters[0][0] + ", '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')"
                else:
                    filters += "DATE(transaction_table." + final_filters[0][0] + ") >= '" + final_filters[0][1].split(' to ')[0] + "' AND DATE(transaction_table." + final_filters[0][0] + ") <= '" + final_filters[0][1].split(' to ')[1] + "'"
            elif final_filters[0][0] == 'sort_by' or final_filters[0][0] == 'sort_by_dir':
                pass
            else:
                filters += "transaction_table." + final_filters[0][0] + " = '" + final_filters[0][1] + "'"
        else:
            for i in range(filter_count):
                if i == 0:
                    if final_filters[i][0] == 'full_name':
                        if status == "Registered" or status == "All":
                            filters += " and (transaction_table.plate_number LIKE '%" + final_filters[i][1] + "%'" + " OR CONCAT(registration_table.first_name, ' ', registration_table.last_name) LIKE '%" + final_filters[i][1] + "%')"
                        else:
                            filters += " and transaction_table.plate_number LIKE '%" + final_filters[i][1] + "%'"
                    elif final_filters[i][0] == 'date_time':
                        if final_filters[i][1] == 'Today':
                            filters += "DATE(transaction_table." + final_filters[i][0] + ") = CURDATE()"
                        elif final_filters[i][1] == 'Yesterday':
                            filters += "DATE(transaction_table." + final_filters[i][0] + ") = CURDATE()-1"
                        elif final_filters[i][1] == 'This Week':
                            filters += "YEARWEEK(DATE(transaction_table." + final_filters[i][0] + ")) = YEARWEEK(CURDATE())"
                        elif final_filters[i][1] == 'This Month':
                            filters += "DATE_FORMAT(transaction_table." + final_filters[i][0] + ", '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')"
                        else:
                            filters += "DATE(transaction_table." + final_filters[i][0] + ") >= '" + final_filters[i][1].split(' to ')[0] + "' AND DATE(transaction_table." + final_filters[i][0] + ") <= '" + final_filters[i][1].split(' to ')[1] + "'"
                    elif final_filters[i][0] == 'sort_by' or final_filters[0][0] == 'sort_by_dir':
                        pass
                    else:
                        filters += "transaction_table." + final_filters[i][0] + " = '" + final_filters[i][1] + "'"
                else:
                    if final_filters[i][0] == 'full_name':
                        if status == "Registered" or status == "All":
                            filters += " and (transaction_table.plate_number LIKE '%" + final_filters[i][1] + "%'" + " OR CONCAT(registration_table.first_name, ' ', registration_table.last_name) LIKE '%" + final_filters[i][1] + "%')"
                        else:
                            filters += " and transaction_table.plate_number LIKE '%" + final_filters[i][1] + "%'"
                    elif final_filters[i][0] == 'date_time':
                        if final_filters[i][1] == 'Today':
                            filters += " and DATE(transaction_table." + final_filters[i][0] + ") = CURDATE()"
                        elif final_filters[i][1] == 'Yesterday':
                            filters += " and DATE(transaction_table." + final_filters[i][0] + ") = CURDATE()-1"
                        elif final_filters[i][1] == 'This Week':
                            filters += " and YEARWEEK(DATE(transaction_table." + final_filters[i][0] + ")) = YEARWEEK(CURDATE())"
                        elif final_filters[i][1] == 'This Month':
                            filters += " and DATE_FORMAT(transaction_table." + final_filters[i][0] + ", '%Y-%m') = DATE_FORMAT(CURDATE(), '%Y-%m')"
                        else:
                            filters += " and DATE(transaction_table." + final_filters[i][0] + ") >= '" + final_filters[i][1].split(' to ')[0] + "' AND DATE(transaction_table." + final_filters[i][0] + ") <= '" + final_filters[i][1].split(' to ')[1] + "'"
                    elif final_filters[i][0] == 'sort_by' or final_filters[0][0] == 'sort_by_dir':
                        pass
                    else:
                        filters += " and transaction_table." + final_filters[i][0] + " = '" + final_filters[i][1] + "'"

        time_interval = '15'

        query1 = "SELECT transaction_table.guard_on_duty, transaction_table.transaction_id, transaction_table.plate_number, transaction_table.status, DATE_FORMAT(transaction_table.date_time, '%m/%d/%Y %h:%i %p') AS date_time, DATE_FORMAT(transaction_table.date_time, '%d/%m/%Y %H:%i') AS date_time_sorter, transaction_table.vehicle_type, transaction_table.gate_number, CONCAT(registration_table.first_name, ' ', registration_table.last_name) AS full_name, transaction_table.saved_picture FROM `transaction_table` LEFT JOIN `registration_table` ON transaction_table.plate_number = registration_table.plate_number "+filters+" ORDER BY "+sort_by+" "+sort_by_dir+" "+limit
        query2 = "SELECT COUNT(*) AS total_transactions FROM `transaction_table` LEFT JOIN `registration_table` ON transaction_table.plate_number = registration_table.plate_number "+filters
        query3 = "WITH RECURSIVE TimeSeries AS (SELECT CAST('2023-11-01 07:00:00' AS DATETIME) AS generated_time UNION ALL SELECT generated_time + INTERVAL "+time_interval+" MINUTE FROM TimeSeries WHERE generated_time < '2023-11-01 19:00:00') SELECT DATE_FORMAT(ts.generated_time, '%I:%i %p') AS `time`, COUNT(tt.date_time) AS `count` FROM TimeSeries ts LEFT JOIN (transaction_table tt LEFT JOIN registration_table registration_table ON tt.plate_number = registration_table.plate_number) ON TIME(tt.date_time) >= TIME(ts.generated_time) AND TIME(tt.date_time) < TIME(ts.generated_time + INTERVAL "+time_interval+" MINUTE) AND tt.gate_number = 1 "+filters.replace('WHERE ','and ').replace('transaction_table.', 'tt.')+" GROUP BY `time`, ts.generated_time ORDER BY ts.generated_time;"
        query4 = "WITH RECURSIVE TimeSeries AS (SELECT CAST('2023-11-01 07:00:00' AS DATETIME) AS generated_time UNION ALL SELECT generated_time + INTERVAL "+time_interval+" MINUTE FROM TimeSeries WHERE generated_time < '2023-11-01 19:00:00') SELECT DATE_FORMAT(ts.generated_time, '%I:%i %p') AS `time`, COUNT(tt.date_time) AS `count` FROM TimeSeries ts LEFT JOIN (transaction_table tt LEFT JOIN registration_table registration_table ON tt.plate_number = registration_table.plate_number) ON TIME(tt.date_time) >= TIME(ts.generated_time) AND TIME(tt.date_time) < TIME(ts.generated_time + INTERVAL "+time_interval+" MINUTE) AND tt.gate_number = 2 "+filters.replace('WHERE ','and ').replace('transaction_table.', 'tt.')+" GROUP BY `time`, ts.generated_time ORDER BY ts.generated_time;"
        query5 = "SELECT transaction_table.vehicle_type AS `class`, COUNT(*) AS `count` FROM transaction_table LEFT JOIN `registration_table` ON transaction_table.plate_number = registration_table.plate_number "+filters+" GROUP BY `class` "
        query6 = "SELECT DATE_FORMAT(MIN(date_time), '%d/%m/%Y %I:%i:%s %p') AS first_entry, DATE_FORMAT(MAX(date_time), '%d/%m/%Y %I:%i:%s %p') AS last_entry FROM transaction_table LEFT JOIN registration_table ON transaction_table.plate_number = registration_table.plate_number "+filters
        query7 = "SELECT employee_id, CURDATE() AS 'last_login' FROM user_table WHERE `employee_id` = '"+username+"'"
        query8 = "SELECT status, COUNT(*) AS count FROM transaction_table LEFT JOIN registration_table ON transaction_table.plate_number = registration_table.plate_number "+filters+" GROUP BY status"

        is_valid1, message = await async_db_query(query1)
        is_valid2, message2 = await async_db_query(query2)
        is_valid3, traffic_volume_entry = await async_db_query(query3)
        is_valid4, traffic_volume_exit = await async_db_query(query4)
        is_valid5, vehicle_classification = await async_db_query(query5)
        is_valid6, time_range = await async_db_query(query6)
        is_valid7, personel_info = await async_db_query(query7)
        is_valid8, status_counts = await async_db_query(query8)

        if is_valid1 and is_valid2 and is_valid3 and is_valid4 and is_valid5 and is_valid6 and is_valid7 and is_valid8:
            return {"status": "success", "message": [message,message2,traffic_volume_entry, traffic_volume_exit, vehicle_classification, time_range, personel_info, status_counts]}
        else:
            return {"status": "error", "message": [message,message2]}

    if purpose == "get_user_info":
        uid = item.data['uid']
        is_valid, message = await async_db_query("SELECT * FROM `user_table` where user_table.employee_id = '"+uid+"'")
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == "set_user_info":
        target = item.data['target']
        id = item.data['id']
        name = item.data['name']
        email = item.data['email']
        role = item.data['role']
        pfp = item.data['pfp']
        is_valid, message = await async_db_query(f"UPDATE `user_table` SET `employee_id`='{id}',`name`='{name}',`pfp`='{pfp}',`role`='{role}',`email`='{email}' WHERE `employee_id`='{target}'")
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == "set_user_password":
        target = item.data['target']
        password = item.data['password']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        is_valid, message = await async_db_query(f"UPDATE `user_table` SET `password`='{hashed_password}' WHERE `employee_id`='{target}'")
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == "delete_user":
        target = item.data['target']
        is_valid, message = await async_db_query(f"DELETE FROM `user_table` WHERE `employee_id`='{target}'")
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == "set_user_pfp":
        target = item.data['target']
        img = item.data['img']
        is_valid, message = await async_db_query(f"UPDATE `user_table` SET `pfp`='{img}' WHERE `employee_id`='{target}'")
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == "logout_user":
        target = item.data['target']
        query = f'UPDATE `user_table` SET `last_logout`=NOW(), `active`=0 WHERE `employee_id`="{target}";'
        is_valid, message = await async_db_query(query)
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == "get_for_watchlist":
        watchlist = item.data['watchlist']
        all_messages = []
        for item_list in watchlist:
            item = item_list['plate_number']
            query1 = f'SELECT *, DATE_FORMAT(date_time, "%m/%d/%Y %h:%i %p") as formatted_date FROM `transaction_table` WHERE `transaction_table`.`plate_number` = "{item}" ORDER BY date_time DESC LIMIT 1;'
            is_valid1, message1 = await async_db_query(query1)
            # print(query1)
            if message1 == "No results found.":
                message1 = [{'transaction_id': None, 'plate_number': item, 'status': None, 'date_time': None, 'vehicle_type': None, 'gate_number': None, 'saved_picture': None}]
            query2 = f'SELECT * FROM `registration_table` WHERE `registration_table`.`plate_number` = "{item}" LIMIT 1;'
            # is_valid2, message2 = DB.db.database_query(query2)
            is_valid2, message2 = await async_db_query(query2)
            if message2 == "No results found.":
                message2 = [{'registered_id': None, 'last_name': None, 'first_name': None, 'vehicle_model': None, 'plate_number': item}]
            else:
                message1[0]['status'] = 'Registered'
            message1[0]['added_by'] = item_list['added_by']
            message1[0]['remarks'] = item_list['remarks']
            message3 = [message1[0] | message2[0]]
            # print(message1)
            # print(message2)
            # print(message3)
            all_messages.append(message3)
        if all_messages != []:
            return {"status": "success", "message": all_messages}
        else:
            return {"status": "error", "message": all_messages}

    if purpose == "get_watchlist_list":
        query = "SELECT watchlist_table.*, MAX(transaction_table.date_time) AS latest_transaction FROM `watchlist_table` LEFT JOIN `transaction_table` ON watchlist_table.plate_number = transaction_table.plate_number GROUP BY watchlist_table.plate_number ORDER BY latest_transaction DESC;"
        is_valid, message = await async_db_query(query)
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == "add_watchlist_entry":
        plate = item.data['plate']
        reason = item.data['reason']
        user = item.data['user']
        is_valid, message = await async_db_query(f"INSERT INTO `watchlist_table`(`plate_number`, `added_by`, `remarks`) VALUES ('{plate}','{user}','{reason}')")
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == "remove_watchlist_entry":
        plate = item.data['plate']
        query = f"DELETE FROM `watchlist_table` WHERE watchlist_table.plate_number='{plate}'"
        is_valid, message = await async_db_query(query)
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

    if purpose == "get_detection_id":
        saved_picture = item.data['saved_picture']
        query = f"SELECT `transaction_id` WHERE `saved_picture` = '{saved_picture}'"
        is_valid, message = await async_db_query(query)
        if is_valid:
            return {"status": "success", "message": message}
        else:
            return {"status": "error", "message": message}

class UserLogin(BaseModel):
    userid: str
    password: str
@app.post("/api/login")
async def api_login(user: UserLogin):
    is_valid, message = await async_db_call(DB.db.verify_user, user.userid, user.password)
    
    if is_valid:
        return {"status": "success", "message": message}
    else:
        return {"status": "error", "message": message}

@app.on_event("shutdown")
def shutdown_event():
    print("Stopping threads and processes...")
    stop_event.set()
    mp_stop_event.set()
    for t in threads: t.join(timeout=2)
    for p in ocr_processes: p.join(timeout=5)
    print("Program finished.")

# Lock to prevent multiple dashboard updates from running at once
dashboard_lock = asyncio.Lock()

async def send_data_dashboard():
    if dashboard_lock.locked():
        # print("Dashboard update already in progress, skipping...")
        return
        
    async with dashboard_lock:
        # 1. Basic metrics today
        query_basic = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN vehicle_type = 'tricycle' THEN 1 ELSE 0 END) as tricycle,
                SUM(CASE WHEN vehicle_type = 'car' THEN 1 ELSE 0 END) as car,
                SUM(CASE WHEN vehicle_type = 'motorcycle' THEN 1 ELSE 0 END) as motorcycle,
                SUM(CASE WHEN status = 'Registered' THEN 1 ELSE 0 END) as registered,
                SUM(CASE WHEN status = 'No Gate Pass' AND plate_number != '' AND plate_number != 'Unreadable plate' AND plate_number != 'No plate detected' THEN 1 ELSE 0 END) as not_registered,
                SUM(CASE WHEN plate_number = '' OR plate_number = 'Unreadable plate' OR plate_number = 'No plate detected' THEN 1 ELSE 0 END) as unidentifiable
            FROM transaction_table 
            WHERE DATE(date_time) = CURDATE()
        """
        
        # 2. Traffic volume queries (gate 1 and gate 2)
        # Recursive CTE for today's volume (07:00 AM to 07:00 PM)
        query_volume = f"""
            WITH RECURSIVE TimeSeries AS (
                SELECT CAST(CONCAT(CURDATE(), ' {Configs.DASHBOARD_TIME_START}') AS DATETIME) AS generated_time 
                UNION ALL 
                SELECT generated_time + INTERVAL {Configs.DASHBOARD_TIME_INTERVAL} MINUTE 
                FROM TimeSeries 
                WHERE generated_time < CAST(CONCAT(CURDATE(), ' {Configs.DASHBOARD_TIME_END}') AS DATETIME)
            )
            SELECT 
                DATE_FORMAT(ts.generated_time, '%h:%i %p') AS `time`,
                SUM(CASE WHEN t.gate_number = 1 THEN 1 ELSE 0 END) AS count1,
                SUM(CASE WHEN t.gate_number = 2 THEN 1 ELSE 0 END) AS count2
            FROM TimeSeries ts
            LEFT JOIN transaction_table t ON t.date_time >= ts.generated_time 
                AND t.date_time < ts.generated_time + INTERVAL {Configs.DASHBOARD_TIME_INTERVAL} MINUTE
            GROUP BY ts.generated_time
            ORDER BY ts.generated_time
        """

        # is_valid_basic, basic_res = DB.db.database_query(query_basic)
        # is_valid_vol, vol_res = DB.db.database_query(query_volume)
        is_valid_basic, basic_res = await async_db_query(query_basic)
        is_valid_vol, vol_res = await async_db_query(query_volume)

        if not is_valid_basic or not basic_res:
            vehicles_today = 0
            tricycle_count = 0
            car_count = 0
            motorcycle_count = 0
            registered_count = 0
            not_registered_count = 0
            unidentifiable_count = 0
        else:
            res = basic_res[0]
            vehicles_today = res['total'] or 0
            tricycle_count = int(res['tricycle'] or 0)
            car_count = int(res['car'] or 0)
            motorcycle_count = int(res['motorcycle'] or 0)
            registered_count = int(res['registered'] or 0)
            not_registered_count = int(res['not_registered'] or 0)
            unidentifiable_count = int(res['unidentifiable'] or 0)

        labels = []
        count1 = []
        count2 = []
        if is_valid_vol and vol_res:
            for row in vol_res:
                labels.append(row['time'])
                count1.append(int(row['count1'] or 0))
                count2.append(int(row['count2'] or 0))

        if not labels:
            labels = ["07:00 AM"]
            count1 = [0]
            count2 = [0]

        data = {
            "camera1_status": "active" if camera_active_status['camera1'] else "inactive",
            "camera2_status": "active" if camera_active_status['camera2'] else "inactive",
            "vehicles_today": vehicles_today,
            "tricycle_count": tricycle_count,
            "car_count": car_count,
            "motorcycle_count": motorcycle_count,
            "classification_labels": ["Tricycle", "Car", "Motorcycle"],
            "classification_counts": [tricycle_count, car_count, motorcycle_count],
            "camera1_traffic_volume_labels": labels,
            "camera1_traffic_volume_count": count1,
            "camera2_traffic_volume_count": count2,
            "quick_metrics_labels": ['Registered', 'No Gate Pass', 'Unidentifiable'],
            "quick_metrics_count": [registered_count, not_registered_count, unidentifiable_count],
        }
        await cm.dashboard_manager.send_update(data)

@app.websocket("/dashboard_ws")
async def dashboard_ws(websocket: WebSocket):
    await cm.dashboard_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "Send data please!!":
                await send_data_dashboard()
    except WebSocketDisconnect:
        cm.dashboard_manager.disconnect(websocket)
        # print("Client Disconnected")

async def send_notification_to_main(message, type):
    data = {
        "message": message,
        "type": type,
    }
    await cm.notifications_manager.send_update(data)

@app.websocket("/notifications_ws")
async def notifications_ws(websocket: WebSocket):
    await cm.notifications_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "Send data please!!":
                await send_notification_to_main("Notification Test","warning")
    except WebSocketDisconnect:
        cm.notifications_manager.disconnect(websocket)
        # print("Client Disconnected")

async def send_data_live_video(all=False):
    if not all:
        # 1. Safely grab a snapshot of the keys (handles if size changes during iteration)
        while True:
            try:
                keys = list(data_to_send.keys())
                break
            except RuntimeError:
                pass
                
        payload_data = {}
        for id in keys:
            if id not in data_to_send:
                continue
                
            visible = data_to_send[id].get('visible', False)
            if not visible:
                data_to_send.pop(id, None) # Remove from original dictionary
            else:
                data_to_send[id]['visible'] = False
                payload_data[id] = data_to_send[id] # Add to safe payload dictionary
                
        data = {
            "new_data": payload_data
        }
    else:
        query = """
        SELECT transaction_table.transaction_id, transaction_table.plate_number, 
               transaction_table.vehicle_type, transaction_table.status, 
               transaction_table.ocrs, transaction_table.method, 
               DATE_FORMAT(transaction_table.date_time, '%m/%d/%Y') AS date, 
               DATE_FORMAT(transaction_table.date_time, '%I:%i %p') AS time, 
               HOUR(transaction_table.date_time)*60 + MINUTE(transaction_table.date_time) AS int_min,
               CONCAT(registration_table.first_name, ' ', registration_table.last_name) AS full_name,
               DATE_FORMAT(transaction_table.date_time, '%H:%i:%s') AS time_sorter
        FROM transaction_table 
        LEFT JOIN registration_table ON transaction_table.plate_number = registration_table.plate_number 
        WHERE DATE(transaction_table.date_time) = CURDATE()
        ORDER BY time_sorter ASC
        """
        is_valid, db_results = await async_db_query(query)
        db_data = {}
        if is_valid and isinstance(db_results, list):
            for row in db_results:
                ocrs = row['ocrs'].split(',') if row['ocrs'] != None else [] 
                log_id = str(row['transaction_id'])
                db_data[log_id] = {
                    'plate': row['plate_number'],
                    'vehicle_type': row['vehicle_type'],
                    'owner': "N/A" if not row['full_name'] else row['full_name'],
                    'status': row['status'],
                    'text_to_display': row['plate_number'],
                    'date': row['date'],
                    'time': row['time'],
                    'int_min': row['int_min'],
                    'confirmed': True,
                    'ocrs': ocrs, 
                    'name': row['full_name'],
                    'method': row['method'], 
                    'ocr_delay': '0ms',
                    'visible': False
                }
                
        # 2. Safely create a copy of the live data to merge
        while True:
            try:
                current_data = data_to_send.copy()
                break
            except RuntimeError:
                pass
                
        for k, v in current_data.items():
            db_data[k] = v
            
        data = {
            "new_data": db_data
        }

    await cm.live_video_manager.send_update(data)

@app.websocket("/live_video_ws")
async def live_video_endpoint(websocket: WebSocket):
    await cm.live_video_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "Send data please!!":
                await send_data_live_video(all=True)
    except WebSocketDisconnect:
        cm.live_video_manager.disconnect(websocket)

@app.post("/api/send_data")
async def receive_data(item: Item):
    purpose = item.data['purpose']
    if purpose == 'kill':
        print("Trying to kill cmd")
        subprocess.call("taskkill /IM LPR_System.exe /T /F", shell=True)
        subprocess.call("taskkill /IM cmd.exe /T /F", shell=True)

    if purpose == 'shutdown':
        print("Stopping threads and processes...")
        stop_event.set()
        mp_stop_event.set()
        for t in threads: t.join(timeout=2)
        for p in ocr_processes: p.join(timeout=5)
        print("Program finished.")
        return {"status": "Shutting down"}

    if purpose == 'toggle_debug':
        debug = item.data['debug'] 
        Configs.debugs = debug
    
    if purpose == 'toggle_graphs':
        graphs = item.data['graphs'] 
        Configs.graphs = graphs
    
    if purpose == 'verify':
        plate_to_check = item.data['plate_text'] 
        vehicle_type = item.data['vehicle_type'] 
        registered, reading, _, _, owner = SPCA.RegCheck.check_registration(plate_to_check, prints=False)
        return {
            "registered": registered, 
            "reading": reading, 
            "original": plate_to_check,
            "vehicle_type": vehicle_type,
            "owner": owner.replace('_', ', ')
        }
    
    if purpose == 'simulate':
        # SPCA.BlackListCheck.read_blacklist_file()
        plate_to_check = item.data['plate_text'] 
        use_advance_patterns = item.data['use_advance_patterns'] == 'true'
        registered, reading, _, _, owner = SPCA.BlackListCheck.check_registration(plate_to_check, pattern_check=True, advance_patterns=use_advance_patterns, prints=False)
        return {
            "registered": registered, 
            "reading": reading, 
            "original": plate_to_check,
            "owner": owner.replace('_', ', ')
        }
    
    if purpose == 'add_to_database':
        id = item.data['id']
        plate_text = item.data['plate_text'] 
        status = item.data['status'] 
        owner = item.data['owner']
        vehicle_type = item.data['vehicle_type']
        try: 
            data_to_send[id]['plate'] = plate_text
            data_to_send[id]['status'] = status
            data_to_send[id]['owner'] = owner
            data_to_send[id]['confirmed'] = True
            data_to_send[id]['visible'] = True
        except:
            pass

        if status == 'No Gate Pass':
            query = f"INSERT IGNORE INTO unregistered_plates (plate_number, last_name, vehicle_type) VALUES ('{plate_text}', 'N/A', '{vehicle_type}')"
            # DB.db.database_query(query)
            await async_db_query(query)
            SPCA.BlackListCheck.read_blacklist_file()

    if purpose == 'confirm':
        id = item.data['id']
        plate_text = item.data['plate_text'] 
        status = item.data['status'] 
        owner = item.data['owner']
        vehicle_type = item.data['vehicle_type']
        try: 
            data_to_send[id]['plate'] = plate_text
            data_to_send[id]['status'] = status
            data_to_send[id]['owner'] = owner
            data_to_send[id]['confirmed'] = True
            data_to_send[id]['visible'] = True
        except:
            pass
        # Sync with Database
        query = f"UPDATE transaction_table SET plate_number = '{plate_text}', status = '{status}' WHERE transaction_id = '{id}'"
        # DB.db.database_query(query)
        await async_db_query(query)
        await send_data_live_video()

        if status == 'No Gate Pass':
            query = f"INSERT IGNORE INTO unregistered_plates (plate_number, last_name, vehicle_type) VALUES ('{plate_text}', 'N/A', '{vehicle_type}')"
            # DB.db.database_query(query)
            await async_db_query(query)
            SPCA.BlackListCheck.read_blacklist_file()
            
    
    if purpose == 'delete':
        id = item.data['id']
        if id in data_to_send:
            data_to_send.pop(id)
        # Sync with Database
        query = f"DELETE FROM transaction_table WHERE transaction_id = '{id}'"
        # DB.db.database_query(query)
        await async_db_query(query)
        await send_data_live_video()

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()
    print("FastAPI app starting up... Starting processing threads.")
    threading.Thread(target=start_processing, daemon=True).start()
    # is_valid, message = DB.db.database_query(f'UPDATE `user_table` SET `active`= 0')
    is_valid, message = await async_db_query(f'UPDATE `user_table` SET `active`= 0')
    if is_valid:
        return {"status": "success", "message": message}
    else:
        return {"status": "error", "message": message}

if __name__ == "__main__":
    print("Starting FastAPI server...")
    # uvicorn.run(app, host="127.0.0.1", port=8000)
    