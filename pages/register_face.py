import flet as ft
import numpy as np
import cvzone
import os, cv2, json, base64, threading, time
from datetime import datetime as dt
from pages.ultils import FaceDetector, calculate_embedding, center_crop_frame, update_attendance

class RegisterFace(ft.UserControl):
    def __init__(self, page, camera_manager):
        super().__init__()
        self.page = page
        self.running = True
        self.face_detector = FaceDetector()
        self.camera_manager = camera_manager
        self.camera = self.camera_manager.get_camera()
        self.img = ft.Image(
            border_radius=ft.border_radius.all(20),
            width=400,
            height=400
        )

        # lottie loading animation
        self.loading_animation = ft.Lottie(
            visible=False, # initially hidden
            expand=True,
            width=150,
            height=150,
            src='pages/assets/loading_animations/loading-bigshelf.json'
        )

        self.capture_face_button = ft.Row(
            controls=[
                ft.Container(
                    border_radius=5,
                    expand=True,
                    bgcolor='#3b82f6',
                    gradient=ft.LinearGradient(
                        colors=['#bbf7d0', '#86efac', '#3b82f6'],
                    ),
                    content=ft.Text(
                        'CAPTURE FACE AND GRANT ACCESS',
                        text_align=ft.TextAlign.CENTER,
                        size=20
                    ),
                    padding=ft.padding.only(left=170, right=170, top=10, bottom=10),
                    on_click=self.capture_image
                )
            ],
            alignment='center',
            vertical_alignment='center'
        )

    def did_mount(self):
        self.update_cam_timer()

    def will_unmount(self):
        self.running = False
        if self.camera is not None:
            self.camera_manager.release_camera()

    def toggle_loading(self, show):
        '''
        Show or hide the loading animation
        '''
        self.loading_animation.visible = show
        self.page.update()

    def update_cam_timer(self):
        def update():
            while self.running:
                ret, frame = self.camera.read()
                if not ret or frame is None:
                    if not self.running:  # Stop if the class is unmounted or navigation occurred
                        break
                    self.show_snackbar('Error: Failed to grab frame')
                    time.sleep(0.1)
                    continue

                try:
                    # detect face and draw bounding box
                    face_loc = self.face_detector.detect_face(frame)
                    if face_loc:
                        x, y, width, height = face_loc
                        cvzone.cornerRect(frame, (x, y, width, height), l=30, t=5, colorR=(0, 255, 0))
                    # get center crop coordinates
                    cropped_frame = center_crop_frame(frame)
                    # convert to base64
                    _, img_arr = cv2.imencode('.png', cropped_frame)
                    img_b64 = base64.b64encode(img_arr)
                    # update image in UI
                    self.img.src_base64 = img_b64.decode('utf-8')
                    self.update()
                except Exception as e:
                    self.show_snackbar(f'Error processing frame: {e}')
                time.sleep(0.033) # cap at ~ 30 FPS
        threading.Thread(target=update, daemon=True).start()

    def build(self):
        return ft.Column(
            [
                ft.Divider(height=10, color='transparent'),
                ft.Text('Position face for capturing', size=24, weight=ft.FontWeight.BOLD, text_align='center'),
                ft.Divider(height=20, color='transparent'),
                self.img,
                ft.Divider(height=50, color='transparent'),
                self.capture_face_button
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def show_snackbar(self, message):
        snackbar = ft.SnackBar(
            bgcolor=ft.colors.GREY_900,
            content=ft.Text(message, color=ft.colors.WHITE)
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def capture_image(self, e=None):
        self.toggle_loading(True) # show loading animation
        try:
            if self.camera is None or not self.camera.isOpened():
                self.loading_animation(False)
                self.show_snackbar("Camera not available. Please check your camera connection")
                return
            
            ret, frame = self.camera.read()
            if not ret or frame is None:
                self.toggle_loading(False)
                self.show_snackbar('Failed to capture image. Please try again.')
                return
            
            face = center_crop_frame(frame)

            # Detect face using MediaPipe
            face_location = self.face_detector.detect_face(face)
            if not face_location:
                self.toggle_loading(False)
                self.show_snackbar("No face detected. Please position your face properly.")
                return
            
            # Crop the face using the bounding box
            x, y, width, height = face_location
            cropped_face = frame[y:y+height, x:x+width]

            # Validate cropped face
            if cropped_face is None or cropped_face.size == 0:
                self.show_snackbar("Unable to crop the face. Please try again.")
                return

            # Get face encoding                        
            try:
                face_encoding = calculate_embedding(cropped_face)
                if face_encoding is None:
                    self.toggle_loading(False)
                    self.show_snackbar("Unable to process face. Please try again.")
                    return
            except ValueError as e:
                self.show_snackbar(str(e))
                return

            # Get user data
            fullname = self.page.client_storage.get("fullname")
            email = self.page.client_storage.get("email")
            telephone = self.page.client_storage.get("telephone")

            if not all([fullname, email, telephone]):
                self.show_snackbar("User data not found. Please sign up again.")
                self.page.go('/signup')
                return

            # Save face image
            save_dir = os.path.join('application_data', "user_faces")
            os.makedirs(save_dir, exist_ok=True)
            image_path = os.path.join(save_dir, f'{email}.jpg')
            cv2.imwrite(image_path, frame)

            # Save face encoding
            save_encoding = os.path.join('application_data', 'user_faces_encoding')
            os.makedirs(save_encoding, exist_ok=True)
            encoding_path = os.path.join(save_encoding, f'{email}_encoding.npy')
            np.save(encoding_path, face_encoding)
            
            # Prepare user data
            user_data = {
                "fullname": fullname,
                "email": email,
                "telephone": telephone,
                "face_image": image_path,
                "face_encoding": encoding_path,
                'total_attendance': 0,
                'attendance_status': [],
                'last_attendance_time': dt.now().strftime("%d-%m-%Y %H:%M:%S")
            }
            
            # Load existing data or create new file
            if os.path.exists('registered_faces.json'):
                with open('registered_faces.json', 'r') as f:
                    all_users = json.load(f)
            else:
                all_users = []

            # Add new user data
            all_users.append(user_data)

            # Save updated data
            with open('registered_faces.json', 'w') as f:
                json.dump(all_users, f, indent=4)
            
            status = 'new'
            self.page.client_storage.set('status', status)
            self.page.client_storage.set("recognized_user_data", user_data) # leverage on this later to try to solve the not showing image.
            update_attendance(email=email, action='sign_in')
            self.camera_manager.release_camera()
            self.show_snackbar('Face registered successfully!')
            self.page.go('/user')

        except Exception as e:
            self.show_snackbar(f"An error occurred while processing the image. Please try again. {e}")
        finally:
            self.toggle_loading(False) # hide loading animation
