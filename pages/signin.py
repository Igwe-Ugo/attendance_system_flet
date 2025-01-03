import flet as ft
import cv2, cvzone
import threading
import base64
import os, time
import json
import numpy as np
from pages.ultils import compute_similarity, calculate_embedding, FaceDetector, center_crop_frame, update_attendance


class SignInPage(ft.UserControl):
    def __init__(self, page, camera_manager):
        super().__init__()
        self.page = page
        self.camera_manager = camera_manager
        self.camera = self.camera_manager.get_camera() # Get shared camera instance
        self.face_detector = FaceDetector()
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
                unknown_encoding = calculate_embedding(cropped_face)
            except ValueError as e:
                self.show_snackbar(str(e))
                return

            # Rest of the logic
            if os.path.exists('registered_faces.json'):
                try:
                    with open('registered_faces.json', 'r') as f:
                        user_data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    self.show_snackbar("Error reading registered faces file. Please try again.")
                    return

                best_match = None
                best_similarity = -1
                
                for user in user_data:
                    registered_encoding = np.load(user['face_encoding'])
                    similarity = compute_similarity(registered_encoding, unknown_encoding)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match = user

                threshold = 0.4  # Adjust this threshold as needed
                
                if best_similarity >= threshold:
                    self.show_snackbar(f"Welcome back, {best_match['fullname']}!")
                    self.page.client_storage.set("recognized_user_data", best_match)
                    email = best_match['email']
                    status = 'old'
                    self.page.client_storage.set('status', status)
                    message = update_attendance(email=email, action='sign_in')
                    self.show_snackbar(message)
                    self.show_user()
                else:
                    self.show_snackbar("Face not recognized. Please try again.")
            else:
                self.show_snackbar("No registered users found. Please sign up first.")
        except Exception as e:
            self.show_snackbar(f'An error occured while processing the image, please try again. {e}')
        finally:
            self.toggle_loading(False) # hide the loading animation

    def show_user(self):
        print("Navigating to User page")
        self.running = False  # Stop the thread
        self.camera_manager.release_camera()
        self.page.go('/user')