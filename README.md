# 🚗 License Plate Recognition System

A simple, lightweight Automatic License Plate Recognition (ALPR) system utilizing **YOLOv11** for object detection and **EasyOCR** for text extraction.

## 🎓 Academic Context

This repository was developed as part of the academic thesis titled:

> **Enhancement of the Vehicle License Plate Recognition System Using Deep Learning Model in Aid for Security at MMSU**

### Authors
* Ma. Josephine Barroga
* Geaniña Jane L. Bulong
* Mark Zion Vincent D. Endaya
* Christian G. Galang
* John Carlos M. Ganal
* Clarissa Elaine B. Libed

---

## 📂 Project Structure

The codebase follows a standard modular layout:

```text
ALPR_SYSTEM/
├── src/                  # Main application source code
│   ├── detection.py      # YOLOv11 inference logic
│   └── ocr.py            # EasyOCR text extraction
├── tests/                # Unit tests
├── config/               # Database and environment configurations
└── README.md