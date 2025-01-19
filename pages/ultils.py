import numpy as np
import cv2, os, json
import mediapipe as mp
import tensorflow as tf
import face_recognition
from datetime import datetime as dt
from cryptography.fernet import Fernet

class FaceRecognitionFunctions:
    def __init__(self):
        pass

    def get_face_encoding(self, image):
        """
        Get face encoding from an image using face_recognition library.
        
        Args:
            image: Input image (numpy array).
        
        Returns:
            Face encoding (128-d vector) or None if no face is detected.
        """
        try:
            # Convert to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # Detect face locations
            face_locations = face_recognition.face_locations(rgb_image, model='hog')
            if face_locations:
                # Get face encodings
                face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                if face_encodings:
                    return face_encodings[0]
            return None
        except Exception as e:
            print(f"Error in get_face_encoding: {e}")
            return None

    @staticmethod
    def compare_faces(known_encoding, unknown_encoding, tolerance=0.4):
        """
        Compare two face encodings and return similarity score and match status.
        
        Args:
            known_encoding: Known face encoding (128-d vector).
            unknown_encoding: Unknown face encoding (128-d vector).
            tolerance: Similarity threshold for match (default 0.3).
        
        Returns:
            similarity (float): Similarity score between 0 and 1.
            is_match (bool): True if similarity >= tolerance.
        """
        if known_encoding is None or unknown_encoding is None:
            return 0.0, False
        try:
            # Calculate face distance
            face_distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
            # Convert to similarity score
            similarity = 1 - face_distance
            # Determine match status
            is_match = similarity >= tolerance
            return similarity, is_match
        except Exception as e:
            print(f"Error in compare_faces: {e}")
            return 0.0, False


class FaceDetector:
    def __init__(self):
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    def detect_face(self, image):
        "Detect face using mediapipe and return face location"
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(image_rgb)

        if results.detections:
            detection = results.detections[0]  # get the first detected face
            bbox = detection.location_data.relative_bounding_box
            h, w, _ = image.shape
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)

            # Add padding to ensure the whole face is captured
            padding = 20
            x = max(0, x - padding)
            y = max(0, y - padding)
            width = min(w - x, width + 2 * padding)
            height = min(h - y, height + 2 * padding)
            return (x, y, width, height)
        return None

class CameraManager:
    '''
    Responsible for all camera functions and inputs...
    '''
    def __init__(self):
        self.camera = None

    def get_camera(self):
        if self.camera is None or self.camera.isOpened():
            for index in range(10): # Try different camera indices
                self.camera = cv2.VideoCapture(index)
                if self.camera.isOpened():
                    # set camera resolution
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    return self.camera
        return self.camera
    
    def release_camera(self):
        if self.camera and self.camera.isOpened():
            self.camera.release()
            self.camera = None

# To crop and center the camera frame
def center_crop_frame(frame, size=400):
    height, width = frame.shape[:2]
    start_x = max(0, (width - size) // 2)
    start_y = max(0, (height - size) // 2)
    cropped = frame[start_y:start_y + size, start_x:start_x + size]
    # ensure correct size
    if cropped.shape[:2] != (size, size):
        cropped = cv2.resize(cropped, (size, size))
    return cropped

def update_attendance(email, action):
    '''
        Function responsible for taking attendance in this system.
    '''
    file_path = 'application_data/application_storage/registered_data.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            all_users = json.load(f)
    else:
        print("Error: No registered users found.")
        return

    # Find the user by email
    user_found = False
    for user in all_users:
        # Decrypt and normalize the stored email
        stored_email = DataCipher().decrypt_data(user['email']).strip().lower()
        input_email = email.strip().lower()  # Normalize input email
        print(f"Encrypted Email in JSON: {user['email']}")
        print(f"Decrypted Email for Comparison: '{stored_email}'")
        print(f"Input Email for Comparison: '{input_email}'")
        if stored_email == input_email:
            user_found = True
            if 'attendance_status' not in user:
                user['attendance_status'] = []

            if action == "sign_in":
                # Check if the user can sign in based on the last sign-out time
                if user['attendance_status']:
                    last_record = user['attendance_status'][-1]
                    if last_record['sign_out_time']:
                        date_time_object = dt.strptime(last_record['sign_out_time'], "%d-%m-%Y %H:%M:%S")
                        seconds_elapsed = (dt.now() - date_time_object).total_seconds()
                        if seconds_elapsed < 30:  # Replace 30 with 86400 for 24 hours
                            print(f"User {email} signed out at {last_record['sign_out_time']}. You can only sign in again after 24 hours.")
                            return  # Stop further processing
                # Append a new sign-in record
                attendance = {
                    'sign_in_time': dt.now().strftime("%d-%m-%Y %H:%M:%S"),
                    'sign_out_time': ''  # Initially empty
                }
                user['total_attendance'] += 1
                user['attendance_status'].append(attendance)
                print(f"Sign-in time recorded for {email}.")

            elif action == "sign_out":
                # Update the last sign-out time
                if user['attendance_status']:
                    last_record = user['attendance_status'][-1]
                    if last_record['sign_out_time'] == '':
                        last_record['sign_out_time'] = dt.now().strftime("%d-%m-%Y %H:%M:%S")
                        user['last_attendance_time'] = dt.now().strftime("%d-%m-%Y %H:%M:%S")
                        print(f"Sign-out time recorded for {email}.")
                    else:
                        print(f"Error: User {email} has already signed out. Sign in first.")
                else:
                    print(f"Error: No sign-in record found for {email}. Please sign in first.")
            else:
                print(f"Error: Invalid action '{action}'. Use 'sign_in' or 'sign_out'.")

            break

    if not user_found:
        print(f"Error: No user found with email {email}. Please register first.")
    else:
        # Save updated data
        with open(file_path, 'w') as f:
            json.dump(all_users, f, indent=4)

class DataCipher:
    def __init__(self, key_file='encryption_key.key'):
        self.key_file = key_file
        self.cipher = self._load_or_generate_key()

    def _load_or_generate_key(self):
        '''
        Load the encryption key from a file or generate a new one
        '''
        try:
            # try to load the key from the key file
            save_key = os.path.join('application_data', 'application_storage')
            os.makedirs(save_key, exist_ok=True)
            register_key = os.path.join(save_key, self.key_file)
            with open(register_key, 'rb') as key_file:
                key = key_file.read()
        except FileNotFoundError:
            # generate a new key if the file doesn't exist
            key = Fernet.generate_key()
            with open(register_key, 'wb') as key_file:
                key_file.write(key)
        return Fernet(key)
    
    def encrypt_data(self, data: str) -> str:
        '''Encrypt a string'''
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, data: str) -> str:
        '''Decrypt a string'''
        return self.cipher.decrypt(data.encode()).decode()
    