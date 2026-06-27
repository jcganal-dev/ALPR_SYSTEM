DISPLAY_HEIGHT = 2160
DISPLAY_WIDTH = 3840
STREAM_QUALITY = 50
STREAM_HEIGHT = 2160*STREAM_QUALITY//100
STREAM_WIDTH = 3840*STREAM_QUALITY//100
ALLOWED_SPAWNPOINT_FROM_BOTTOM = 0.4    # default 0.4
ALLOWED_FROM_LEFT = 0       # default: 0
ALLOWED_FROM_RIGHT = 1      # default: 1
MIN_AGE = 8
MIN_YOLO_CONF = 0.7   # default 0.5
MOTORCYCLE_HEIGHT_MULTIPLIER = 2
OBJECT_PERSISTENCE_IOU_MIN = 0.4
OBJECT_PERSISTENCE_SHAPE_TOLERANCE = 0.4
MOVE_THRESHOLD = 0.32
MAX_NUMBER_OF_READS_PER_PLATE = -1  # set to -1 to disable
PATTERN_CHECK_PATIENCE = 5
FAST_MODE = False
ULTRA_FAST_MODE = False # NOT RECOMMENDED Camera will frame skip!
DASHBOARD_TIME_START = '06:00:00'
DASHBOARD_TIME_END = '18:00:00'
DASHBOARD_TIME_INTERVAL = '15'
USE_BBOX_PREDICTION_LOGIC = True
camera1_source_cam = "rtsp://admin:paraThesis(2026)@192.168.100.2:554/stream1"
camera2_source_cam = "rtsp://admin:thesisAdmin(25-26)@192.168.100.96:554/stream1"
# camera1_source_cam = "./SAMPLES/entry.mp4"
# camera2_source_cam = "./SAMPLES/exit1.mp4"
# MODEL_PATH = "./MODELS/best.engine"
MODEL_PATH = "./MODELS/last.engine"
debugs = False
graphs = False
metrics = {
    'camera1_total' : 0.0,
    'camera2_total' : 0.0,
    'camera1_capture': 0.0,
    'camera2_capture': 0.0,
    'camera1_detection': 0.0,
    'camera2_detection': 0.0,
    'cam1_ocr_start' : 0.0,
    'cam2_ocr_start' : 0.0,
    'camera1_ocr': 0.0,
    'camera2_ocr': 0.0,
    'camera1_display': 0.0,
    'camera1_db_worker': 0.0,
    'cam1_db_worker_start': 0.0,
    'cam1_start' : 0.0,
    'cam2_start' : 0.0,
}