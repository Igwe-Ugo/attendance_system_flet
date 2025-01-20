import json
import base64
import os, time
import logging
import threading
import flet as ft
import numpy as np
import cv2, cvzone
from pages.ultils import FaceRecognitionFunctions, FaceDetector, center_crop_frame, update_attendance, DataCipher


class SignInPage(ft.UserControl):
    def __init__(self, page, camera_manager):
        super().__init__()
        self.page = page
        self.camera_manager = camera_manager
        self.admin_email_1 = 'ugo2000igwe12@gmail.com'
        self.admin_email_2 = 'aruegbepaul@gmail.com'
        self.file_data_path = 'application_data/application_storage/registered_data.json'
        self.camera = self.camera_manager.get_camera() # Get shared camera instance
        self.face_detector = FaceDetector()
        self.data_cipher = DataCipher()
        self.running = True
        self.img = ft.Image(
            border_radius=ft.border_radius.all(20),
            width=400,
            height=400
        )

        # Lottie loading animation
        self.loading_animation = ft.Lottie(
            src='pages/assets/loading_animations/loading-bigshelf.json',
            visible=False, # initially hide the function
            height=150,
            width=150,
            expand=True
        )

        self.signin_button =  ft.Row(
            controls=[
                ft.Container(
                    border_radius=5,
                    expand=True,
                    bgcolor='#3b82f6',
                    gradient=ft.LinearGradient(
                        colors=['#bbf7d0', '#86efac', '#3b82f6'],
                    ),
                    content=ft.Text('Take Attendance and Grant Access', text_align=ft.TextAlign.CENTER, size=25),
                    padding=ft.padding.only(left=170, right=170, top=10, bottom=10),
                    on_click=self.sign_in,
                )
            ],
            alignment='center',
            vertical_alignment='center'
        )

    # Configure the logger
    logging.basicConfig(
        level=logging.ERROR,  # Set the log level
        format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
        filename="error_log.log",  # Save logs to a file (optional)
        filemode="a"  # Append to the log file
    )

    logger = logging.getLogger(__name__)

    def toggle_loading(self, show):
        # This function toggles the loading animation
        self.loading_animation.visible = show
        self.page.update()

    def did_mount(self):
        self.update_frame()

    def will_unmount(self):
        self.running = False
        if self.camera is not None:
            self.camera_manager.release_camera() # Release camera when unmounting

    def update_frame(self):
        def update():
            failure_count = 0  # Track consecutive failures
            max_retries = 5    # Maximum retries before stopping the thread
            while self.running:
                ret, frame = self.camera.read()
                if ret:
                    # Reset failure count on success
                    failure_count = 0

                    # detect face in frame and draw bounding box
                    face_loc = self.face_detector.detect_face(frame)
                    if face_loc:
                        x, y, w, h = face_loc
                        cvzone.cornerRect(frame, (x, y, w, h), l=30, t=5, colorR=(0,255,0))

                    # Crop and encode frame
                    cropped_frame = center_crop_frame(frame)
                    _, im_arr = cv2.imencode('.png', cropped_frame)
                    im_b64 = base64.b64encode(im_arr)
                    self.img.src_base64 = im_b64.decode("utf-8")
                    self.update()
                else:
                    # Increment failure count and log
                    failure_count += 1
                    self.show_snackbar(f"Webcam read failed ({failure_count}/{max_retries}). Retrying...")

                    # Stop the thread if max retries are reached
                    if failure_count >= max_retries:
                        # Only navigate back if still on the SignIn page
                        if self.page.route == '/sign_in':  
                            self.show_snackbar("Maximum retries reached. Stopping webcam feed. Navigating back to landing page.")
                            self.running = False
                            self.page.go('/')
                        break

                    time.sleep(1)  # Delay for retries
        # Start the thread
        threading.Thread(target=update, daemon=True).start()

    def build(self):
        return ft.Column(
            [
                ft.Divider(height=10, color='transparent'),
                ft.Text('Welcome to the SignIn Page', size=24, weight=ft.FontWeight.BOLD, text_align='center'),
                ft.Divider(height=20, color='transparent'),
                self.img,
                ft.Divider(height=50, color='transparent'),
                self.signin_button
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def show_snackbar(self, message):
        """Display a snackbar with a message using the new Flet method."""
        snackbar = ft.SnackBar(
            bgcolor=ft.colors.GREY_900,
            content=ft.Text(message, color=ft.colors.WHITE)
        )
        # Append the snackbar to the page's overlay and make it visible
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()  # Refresh the page to show the snackbar

    def sign_in(self, e=None):
        self.toggle_loading(True) # start loading when signin button is clicked
        try:
            ret, frame = self.camera.read()
            if not ret or frame is None:
                self.toggle_loading(False)
                self.show_snackbar('Camera error, failed to capture image. Please try again.')
                return

            # Detect face using MediaPipe
            face_location = self.face_detector.detect_face(frame)
            if not face_location:
                self.toggle_loading(False)
                self.show_snackbar("No face detected. Please position your face properly.")
                return

            # Crop the face using the bounding box
            x, y, width, height = face_location
            cropped_face = frame[y:y+height, x:x+width]

            # Validate cropped face
            if cropped_face is None or cropped_face.size == 0:
                self.toggle_loading(False)
                self.show_snackbar("Unable to crop the face. Please try again.")    
                return

            # Get face embedding
            try:
                unknown_encoding = FaceRecognitionFunctions.get_face_encoding(self, cropped_face)
            except ValueError as e:
                self.show_snackbar(str(e))
                return

            # Rest of the logic
            if os.path.exists(self.file_data_path):
                try:
                    with open(self.file_data_path, 'r') as f:
                        user_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    self.show_snackbar("Error reading registered faces file. Please try again.")
                    return

                best_match = None
                highest_similarity = 0.0

                for user in user_data:
                    registered_encoding = np.load(user['face_encoding'])
                    similarity, is_match = FaceRecognitionFunctions.compare_faces(registered_encoding, unknown_encoding)
                    print(f"User: {user['fullname']}, Similarity: {similarity}, Match: {is_match}")

                    if is_match and similarity > highest_similarity:
                        best_match = user
                        highest_similarity = similarity

                if best_match:
                    fullname = self.data_cipher.decrypt_data(best_match['fullname'])
                    self.show_snackbar(f"Welcome back, {fullname}!")
                    # Set session for regular user
                    self.page.client_storage.set("recognized_user_data", best_match)
                    # set session for the admin
                    self.page.client_storage.set("admin_data", best_match)
                    email_ = self.data_cipher.decrypt_data(best_match['email'])
                    email = email_.strip().lower()
                    user_role = best_match['user_role']
                    self.page.client_storage.set("user_role", user_role) # I don't know why I am setting this session?
                    self.page.client_storage.set("registered_by_admin", False)

                    if user_role == 'Administrator':
                        self.show_admin(email=email)
                    else:
                        self.show_user(email=email)
                else:
                    self.show_snackbar("Face not recognized. Please try again.")

            else:
                self.show_snackbar("No registered users found. Please sign up first.")
        except Exception as e:
            # Log the exception with context
            self.logger.error("Error in process_data function", exc_info=True)
            print(f'An error occured while processing the image, please try again. {e}')
            self.show_snackbar(f'An error occured while processing the image, please try again. {e}')
        finally:
            self.toggle_loading(False) # hide the loading animation

    def show_admin(self, email):
        print("Navigating to User page")
        self.running = False  # Stop the thread
        self.camera_manager.release_camera()
        update_attendance(email=email, action='sign_in')
        self.page.go('/admin')

    def show_user(self, email):
        print("Navigating to User page")
        self.running = False  # Stop the thread
        self.camera_manager.release_camera()
        update_attendance(email=email, action='sign_in')
        self.page.go('/user')
