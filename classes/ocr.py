import easyocr

class OCR:
    def __init__(self):
        pass

    def ocr_process(self, stop_event, ocr_queue, ocr_results, ready_ocr_processes):
        reader = easyocr.Reader(['en'], gpu=True)
        ready_ocr_processes.put(True)
        while not stop_event.is_set():
            try:
                results = ocr_queue.get(timeout=1)
            except:
                continue
            to_output = {}
            for id in results:
                plate_crop = results[id]
                detections = reader.readtext(plate_crop, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ', paragraph=True)
                for detection in detections:
                    _, text= detection
                    text = text.upper()
                    to_output[id] = text
            try:
                ocr_results.put(to_output, timeout=1)
            except:
                continue
        print("OCR process stopped.")