import numpy as np
import cv2, os, json
import mediapipe as mp
import tensorflow as tf
from datetime import datetime as dt
from cryptography.fernet import Fernet

def triplet_loss(y_true, y_pred, alpha=0.2):
    batch_size = tf.shape(y_pred)[0] // 3
    anchor = y_pred[:batch_size]
    positive = y_pred[batch_size:2 * batch_size]
    negative = y_pred[2 * batch_size:]

    pos_dist = tf.reduce_sum(tf.square(anchor - positive), axis=-1)
    neg_dist = tf.reduce_sum(tf.square(anchor - negative), axis=-1)
    loss = tf.reduce_mean(tf.maximum(pos_dist - neg_dist + alpha, 0))
    return loss

# Load the pre-trained model for facial embeddings
model_path = 'face_recog_vggface.keras' # Please specify where this file path is in correctly for it to load.
model = tf.keras.models.load_model(model_path, custom_objects={'triplet_loss': triplet_loss})

def calculate_embedding(face_image):
    """Preprocess face and calculate embeddings."""

    if face_image is None or not isinstance(face_image, np.ndarray):
        raise ValueError("Invalid input: face_image must be a valid numpy array.")
    
    if face_image.size == 0:
        raise ValueError("Invalid input: face_image is empty.")
    
    face_image = cv2.resize(face_image, (224, 224))  # Resize to model input size
    face_image = face_image / 255.0  # Normalize
    face_image = np.expand_dims(face_image, axis=0)  # Add batch dimension
    return model.predict(face_image)[0]  # Get the embedding

def compute_similarity(known_embedding, unknown_embedding):
    """Compute similarity between two face embeddings."""
    return np.dot(known_embedding, unknown_embedding) / (
        np.linalg.norm(known_embedding) * np.linalg.norm(unknown_embedding)
    )

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
    # Load existing data or create a new file
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
        if user['email'] == email:
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
        '''Encrypt a string'''
        return self.cipher.decrypt(data.encode()).decode()