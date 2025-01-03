import flet as ft
import os, io, base64
from PIL import Image
import pandas as pd
import datetime, json
from pages.ultils import update_attendance

class User(ft.UserControl):
    def __init__(self, page, user_data):
        super().__init__()
        self.page = page
        self.user_data = user_data
        self.running = True
        self.admin_email = "ugo2000igwe12@gmail.com"  # Replace with the admin email
        self.no_user = ft.Icon(
            name=ft.icons.IMAGE_OUTLINED,
            scale=ft.Scale(5)
        )
        self.go_home_button = ft.Row(
            controls=[
                ft.Container(
                    border_radius=5,
                    expand=True,
                    bgcolor='#4f46e5',
                    gradient=ft.LinearGradient(
                        colors=['#ea580c', '#4f46e5'],
                    ),
                    content=ft.Text('Sign out', text_align=ft.TextAlign.CENTER, size=18, color=ft.colors.WHITE),
                    padding=ft.padding.only(left=50, right=50, top=10, bottom=10),
                    on_click=self.go_home,
                )
            ],
            alignment='center',
            vertical_alignment='center'
        )
        self.download_button = ft.Container(
            border_radius=5,
            expand=True,
            bgcolor='#3b82f6',
            gradient=ft.LinearGradient(
                colors=['#bbf7d0', '#86efac', '#3b82f6'],
            ),
            content=ft.Text('Download Activity Log', text_align=ft.TextAlign.CENTER, size=20, color=ft.colors.WHITE),
            padding=ft.padding.only(left=70, right=70, top=10, bottom=10),
            on_click=self.download_activity_log,
        )

    def load_image(self, path):
        print(f"Loading image from path: {path}")
        if os.path.exists(path):
            try:
                with Image.open(path) as img:
                    img = img.resize((400, 400))  # Resize image for display
                    buffered = io.BytesIO()
                    img.save(buffered, format='PNG')
                    return base64.b64encode(buffered.getvalue()).decode()
            except Exception as e:
                print(f"Error loading image: {e}")
        else:
            print("Image path does not exist.")
        return None
    
    def did_mount(self):
        # Reset any lingering logic
        self.page.client_storage.set("current_page", "/user")

    def build(self):
        if not self.user_data:
            return ft.View(
                controls = [
                    ft.AppBar(
                            leading=ft.IconButton(
                                icon=ft.icons.ARROW_BACK_IOS,
                                icon_size=20,
                                tooltip='Back to Landing Page',
                                on_click=lambda _: self.page.go("/sign_up")
                            ),
                            title=ft.Text("No User data found!"),
                            bgcolor=ft.colors.SURFACE_VARIANT
                        ),
                    ft.Column(
                        [
                            ft.Divider(height=120, color='transparent'),
                            self.no_user,
                            ft.Divider(height=70, color='transparent'),
                            ft.Text('No User found with this face, please signup!', size=18, weight=ft.FontWeight.W_800),
                        ],
                        horizontal_alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10
                    ),
                ]
            )

        img_data = self.load_image(self.user_data.get('face_image', None) or '')
        
        controls = [
            ft.Text('RESTRICTED AREA', size=24, weight=ft.FontWeight.BOLD),
            ft.Text('Face Recognized!', size=21, weight=ft.FontWeight.W_900),
            ft.Text('Below are the credentials of the user', size=18, weight=ft.FontWeight.W_800),
            ft.Image(src_base64=img_data) if img_data else ft.Text('No Image available'),
            ft.Text(f"Full Name: {self.user_data.get('fullname', 'N/A')}"),
            ft.Text(f"Email: {self.user_data.get('email', 'N/A')}"),
            ft.Text(f"Phone: {self.user_data.get('telephone', 'N/A')}"),
            ft.Divider(height=20, color='transparent'),
            self.go_home_button,
            ft.Divider(height=30, color='transparent'),
        ]

        # Show admin button if the logged-in user is the admin
        if self.user_data.get('email') == self.admin_email:
            controls.append(self.download_button)

        return ft.Container(
            content=ft.Column(
                controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.ALWAYS,  # Enables scrolling when content exceeds space
            ),
            alignment=ft.alignment.center,
            padding=20
        )

    def go_home(self, e):
        email = self.user_data.get('email')
        update_attendance(email=email, action='sign_out')
        self.page.client_storage.remove("session")
        self.page.go('/')

    def show_snackbar(self, message):
        snackbar = ft.SnackBar(
            bgcolor=ft.colors.GREY_900,
            content=ft.Text(message, color=ft.colors.WHITE)
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()

    def download_activity_log(self, e):
        """Generate and download the activity log as a CSV file."""
        try:
            # Load activity log from a JSON file
            if os.path.exists('registered_faces.json'):
                with open('registered_faces.json', 'r') as f:
                    activity_data = json.load(f)
            else:
                self.show_snackbar('No data present in the activity log for now. Try again later!')
                return

            # Extract relevant fields from the JSON
            extracted_data = []
            for user_data in activity_data:
                for attendance in user_data.get("attendance_status", []):
                    extracted_data.append({
                        "fullname": user_data["fullname"],
                        "email": user_data["email"],
                        "telephone": user_data["telephone"],
                        "sign_in_time": attendance["sign_in_time"],
                        "sign_out_time": attendance["sign_out_time"],
                        "total_attendance": user_data["total_attendance"],
                        "last_attendance_time": user_data["last_attendance_time"]
                    })

            # Convert extracted data to a DataFrame
            df = pd.DataFrame(extracted_data)

            # Add a timestamped filename
            filename = f"activity_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join('downloads', filename)
            os.makedirs('downloads', exist_ok=True)

            # Save the DataFrame to a CSV file
            df.to_csv(filepath, index=False)

            # Show a success snackbar
            self.show_snackbar(f"Activity log saved as {filename} in {filepath}")
        except Exception as ex:
            # Show an error snackbar
            self.show_snackbar(f"Error: {str(ex)}")

    