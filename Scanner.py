""" Veri-Quick Scanner made to access the qr content and load the content in browser
made by D.Rana 

Acesss: Limited and under copyright 

Github: Dave R 
Repository: Veri-Quick Final Scanner.final.py 

Permission required to edit and modify the code 

Date of update : 10-11-2024

Version : 3.0.0      

"""

# importing modules
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon, QImage, QPixmap
import cv2
from pyzbar import pyzbar
import pytesseract
import re
import sys
import requests
import os
import json
import pygame 
import webbrowser

# Adding pytessaract module 
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#Initiating modules 
pygame.init()
pygame.mixer.init()

# Loading assets 

aadhar_detected = r"D:\Python\Main Python Directory\Mega projects\Prototype assets\Aadhar_detected.mp3"
pan_detected = r"D:\Python\Main Python Directory\Mega projects\Prototype assets\PAN_DETECTED.mp3"
failure = r"D:\Python\Main Python Directory\Mega projects\Prototype assets\verfication unsuccessful manual checking neede.mp3"

# ...existing code...

# GUI and the working code 
class QRScannerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  
        self.cap.set(cv2.CAP_PROP_FPS, 30)  
        self.browser_opened = False
        self.qr_data = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)  

    def initUI(self):
        self.setWindowTitle("Veri-quick ✅ Scanner")
        self.setWindowIcon(QIcon(r"D:\Python\Main Python Directory\Mega projects\Prototype assets\qricon.ico"))
        self.image_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        self.show()

    def update_frame(self):
        success, frame = self.cap.read()
        if not success:
            print("Error reading frame from camera.")
            return

        decoded_objs = pyzbar.decode(frame)
        if decoded_objs:
            for obj in decoded_objs:
                data = obj.data.decode('utf-8')
                print(f"Decoded QR Code Data: {data}")
                x, y, w, h = obj.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 250, 0), 2)

                if not self.browser_opened and (self.qr_data is None or self.qr_data != data):
                    self.qr_data = data
                    document_metadata = self.process_qr_data(data)

                    if document_metadata:
                        for doc in document_metadata["files"]:
                            doc_type = doc.get("document_type", "Unknown")
                            doc_url = doc.get("document_url", "")
                            print(f"Detected Document Type: {doc_type}, URL: {doc_url}")

                            # Play sound based on document type
                            if doc_type == "Aadhaar":
                                pygame.mixer.music.load(aadhar_detected)
                                pygame.mixer.music.play()
                            elif doc_type == "PAN":
                                pygame.mixer.music.load(pan_detected)
                                pygame.mixer.music.play()
                            else:
                                pygame.mixer.music.load(failure)
                                pygame.mixer.music.play()

                            # Open the document URL in the web browser
                            if doc_url:
                                webbrowser.open(doc_url)
                                self.browser_opened = True

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def process_qr_data(self, data):
        print(f"Processing QR data: {data}")
        try:
            qr_content = json.loads(data)
            files = qr_content.get("files", [])

            if not files:
                print("No files found in QR data.")
                return None

            for file_info in files:
                doc_url = file_info.get("document_url", "")
                if not doc_url:
                    continue

                # Modify Dropbox URL to trigger direct download
                direct_url = doc_url.replace("dl=0", "dl=1")
                image_path = self.download_image_from_url(direct_url)
                if not image_path:
                    return None

                extracted_text = self.extract_text_from_image(image_path)
                document_type = self.detect_document_type(extracted_text)

                file_info["document_type"] = document_type

            return qr_content
        except Exception as e:
            print(f"Error processing QR data: {e}")
            return None

    def download_image_from_url(self, url):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                local_filename = "downloaded_image.jpg"
                with open(local_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Image downloaded successfully: {local_filename}")
                
                # Check if the image file exists after download
                if os.path.exists(local_filename):
                    return local_filename
                else:
                    print("Downloaded image not found.")
                    return None
            else:
                print(f"Failed to download image. HTTP Status Code: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

    def extract_text_from_image(self, image_path):
        try:
            # Check if the image file exists
            if not os.path.exists(image_path):
                print(f"Error: Image path does not exist: {image_path}")
                return ""

            image = cv2.imread(image_path)
            if image is None:
                print(f"Error: Could not load image from {image_path}")
                return ""

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply preprocessing steps for better OCR accuracy
            gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            _, binary_image = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(binary_image)
            print(f"Extracted Text: {text}")
            return text
        except Exception as e:
            print(f"Error during OCR: {e}")
            return ""

    def detect_document_type(self, text):
        aadhaar_pattern = r"\b\d{4}\s\d{4}\s\d{4}\b"
        pan_pattern = r"[A-Z]{5}\d{4}[A-Z]"

        if re.search(aadhaar_pattern, text):
            return "Aadhaar"
        elif re.search(pan_pattern, text):
            return "PAN"
        else:
            return "Manual verification needed"

    def closeEvent(self, event):
        self.cap.release()
        cv2.destroyAllWindows()

        # Clean up the downloaded image if it exists
        if os.path.exists("downloaded_image.jpg"):
            os.remove("downloaded_image.jpg")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    scanner = QRScannerApp()
    sys.exit(app.exec_())
