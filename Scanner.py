""" Veri-Quick Scanner made to access the qr content and load the content in browser
made by D.Rana 

Acesss: Limited and under copyright 

Github: Dave R 
Repository: Veri-Quick Final Scanner.final.py 

Permission required to edit and modify the code 

Date of update : 10-11-2024

Version : 2.2.8

"""

# Importing necessary modules
import cv2
import pyzbar.pyzbar as pyzbar
import webbrowser
import pygame
import sys
import json
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QTimer

# Initialize pygame mixer and preload sounds for faster access
pygame.mixer.init()
SUCCESS_SOUND = r"D:\\Python\Main Python Directory\Mega Project Prototype 1\Prototype assets\document loaded.mp3"
AADHAAR_DETECTED_SOUND = r"D:\Python\Main Python Directory\Mega Project Prototype 1\Prototype assets\aadhar_detected.mp3"
PAN_VERIFICATION_SOUND = r"D:\Python\Main Python Directory\Mega Project Prototype 1\Prototype assets\pan_detected .mp3"
MANUAL_VERIFICATION_SOUND = r"D:\Python\Main Python Directory\Mega Project Prototype 1\Prototype assets\Verification unsuccessful manual checking needed.mp3"

class QRScannerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cap = None
        self.initialize_camera()

        # Set initial flags and timer
        self.qr_data = None
        self.browser_opened = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Frame rate control

    def initUI(self):
        self.setWindowTitle("Veriquick - Document Scanner")
        self.setWindowIcon(QIcon("D:\\Python\\Main Python Directory\\Mega Project Prototype 1\\Prototype assets\\qricon.ico"))

        # Set up layout and video display label
        self.image_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)
        self.show()

    def initialize_camera(self):
        """Initialize the camera with error handling."""
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            if not self.cap.isOpened():
                raise Exception("Camera could not be initialized with DirectShow. Trying default settings.")
        except Exception as e:
            print(f"Camera initialization error: {e}")
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                sys.exit("Unable to access the camera. Please check the camera connection or settings.")

    def update_frame(self):
        if self.cap is None or not self.cap.isOpened():
            print("Camera is not available.")
            return

        success, frame = self.cap.read()
        if not success:
            print("Error reading frame from camera.")
            return

        # Decode QR code from frame
        decoded_objs = pyzbar.decode(frame)
        if decoded_objs:
            # Process each detected QR code
            for obj in decoded_objs:
                data = obj.data.decode('utf-8')
                print(f"Decoded QR Code Data: {data}")
                x, y, w, h = obj.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 250, 0), 2)

                # Only process if it's a new QR code
                if not self.browser_opened and (self.qr_data is None or self.qr_data != data):
                    self.qr_data = data
                    document_metadata = self.process_qr_data(data)

                    if document_metadata:
                        self.browser_opened = True  # Prevent re-opening on repeat scans
                        aadhaar_detected = False
                        pan_detected = False
                        success_sound_played = False  # Play success sound once

                        # Open each document URL in the QR code metadata
                        for doc in document_metadata["files"]:
                            doc_type = doc.get("document_type", "Unknown")
                            doc_url = doc.get("document_url", "")
                            aadhaar_numbers = doc.get("aadhaar_numbers", [])
                            pan_numbers = doc.get("pan_numbers", [])

                            # Open the document URL in the browser
                            webbrowser.open(doc_url)
                            print("Document loaded, playing success sound.")
                            if not success_sound_played:
                                self.play_sound(SUCCESS_SOUND)
                                success_sound_played = True

                            # Check document type and play corresponding sound
                            if doc_type == "Aadhaar" and aadhaar_numbers and not aadhaar_detected:
                                aadhaar_detected = True
                                print("Aadhaar detected, playing Aadhaar sound.")
                                self.play_sound(AADHAAR_DETECTED_SOUND)

                            elif doc_type == "PAN" and pan_numbers and not pan_detected:
                                pan_detected = True
                                print("PAN detected, playing PAN sound.")
                                self.play_sound(PAN_VERIFICATION_SOUND)

                        # Play manual verification sound if neither Aadhaar nor PAN was detected
                        if not aadhaar_detected and not pan_detected:
                            print("Manual verification needed, playing manual verification sound.")
                            self.play_sound(MANUAL_VERIFICATION_SOUND)

                    QTimer.singleShot(3000, self.reset_for_next_scan)  # Allow for a new scan after 3 seconds
        else:
            self.qr_data = None

        # Update display with video frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_img))

    def process_qr_data(self, qr_data):
        try:
            return json.loads(qr_data)
        except json.JSONDecodeError as e:
            print(f"Error decoding QR data: {e}")
            return None

    def play_sound(self, sound_path):
        """Play sound at specified path with error handling."""
        try:
            pygame.mixer.music.stop()  # Stop any previous sound to avoid overlap
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
            print(f"Played sound: {sound_path}")
        except pygame.error as e:
            print(f"Error playing sound {sound_path}: {e}")

    def reset_for_next_scan(self):
        """Reset necessary flags to allow for the next scan."""
        self.qr_data = None
        self.browser_opened = False

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    scanner = QRScannerApp()
    sys.exit(app.exec_())
