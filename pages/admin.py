import flet as ft
import pandas as pd 
import os, io, base64
import datetime, json
from PIL import Image
from pages.ultils import update_attendance, DataCipher

class Admin(ft.UserControl):
    def __init__(self, page, user_data):
        super().__init__()
        self.page = page
        self.user_data = user_data
        self.running = True
        self.data_cipher = DataCipher()
        self.no_user = ft.Icon(
            name=ft.icons.IMAGE_OUTLINED,
            scale=ft.Scale(5)
        )
        
        self.signout_button_admin = ft.Row(
            controls=[
                ft.Container(
                    border_radius=5,
                    expand=True,
                    bgcolor='#b4d4fb',
                    gradient=ft.LinearGradient(
                        colors=['#b4d4fb', '#848484', '#0f8389'],
                    ),
                    content=ft.Text('Admin Sign out', text_align=ft.TextAlign.CENTER, size=18, color=ft.colors.WHITE),
                    padding=ft.padding.only(left=25, right=25, top=20, bottom=20),
                    on_click=self.admin_logout,
                )
            ],
            alignment='center',
            vertical_alignment='center'
        )

        self.buttonSignUp = ft.Container(
            border_radius=5,
            expand=True,
            bgcolor='#4f46e5',
            gradient=ft.LinearGradient(
                colors=['#ea580c', '#4f46e5'],
            ),
            content=ft.Text(
                'Register New User',
                color='white',
                size=18,
                text_align=ft.TextAlign.CENTER
            ),
            padding=ft.padding.only(left=25, right=25, top=20, bottom=20),
            on_click=self.sign_up,
        )

        self.download_button = ft.Container(
            border_radius=5,
            expand=True,
            bgcolor='#3b82f6',
            gradient=ft.LinearGradient(
                colors=['#bbf7d0', '#86efac', '#3b82f6'],
            ),
            content=ft.Text('Download Activity Log', text_align=ft.TextAlign.CENTER, size=18, color=ft.colors.WHITE),
            padding=ft.padding.only(left=25, right=25, top=20, bottom=20),
            on_click=self.download_activity_log,
        )

    def sign_up(self, e):
        self.page.go('/signup')

    def load_image(self, path):
        print(f"Loading image from path: {path}")
        if os.path.exists(path):
            try:
                with Image.open(path) as img:
                    img = img.resize((100, 100))  # Resize image for display
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
                            title=ft.Text("No Admin data found!"),
                            bgcolor=ft.colors.SURFACE_VARIANT
                        ),
                    ft.Column(
                        [
                            ft.Divider(height=120, color='transparent'),
                            self.no_user,
                            ft.Divider(height=70, color='transparent'),
                            ft.Text('No Admin found with this face, please signup!', size=18, weight=ft.FontWeight.W_800),
                        ],
                        horizontal_alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10
                    ),
                ]
            )

        encrypted_fullname = self.user_data.get('fullname', 'N/A')
        encrypted_email = self.user_data.get('email', 'N/A')
        encrypted_telephone = self.user_data.get('telephone', 'N/A')

        # decrypting the user details
        plain_fullname = self.data_cipher.decrypt_data(encrypted_fullname)
        plain_email = self.data_cipher.decrypt_data(encrypted_email)
        plain_telephone = self.data_cipher.decrypt_data(encrypted_telephone)

        img_data = self.load_image(self.user_data.get('face_image', None) or '')
        
        controls = [
            ft.Text('RESTRICTED AREA', size=22, weight=ft.FontWeight.BOLD),
            ft.Text('Face Recognized!', size=19, weight=ft.FontWeight.W_900),
            ft.Text('Below are the credentials of the user', size=18, weight=ft.FontWeight.W_800),
            ft.Row(
                spacing=20,
                controls=[
                    ft.Image(src_base64=img_data, border_radius=10) if img_data else ft.Text('No Image available'),
                    ft.Column(
                        spacing=5,
                        controls=[
                            ft.Text(f"Full Name: {plain_fullname}", size=20, weight=ft.FontWeight.W_900),
                            ft.Text(f"Email Address: {plain_email}", size=20, weight=ft.FontWeight.W_900),
                            ft.Text(f"Phone Number: {plain_telephone}", size=20, weight=ft.FontWeight.W_900),
                        ]
                    ),
                ]
            ),
            ft.Divider(height=10, color='transparent'),
            self.signout_button_admin,
            ft.Divider(height=10, color='transparent'),
            ft.Text(
                "System admin should ensure that user is properly cleared by the authorized personnel before being registered. If cleared to register, then click the signup link below and register new user.",
                size=15,
                weight=ft.FontWeight.W_800
            ),
            ft.Divider(height=10, color='transparent'),
            ft.Row(
                controls=[
                    self.buttonSignUp,
                    self.download_button
                ],
                alignment='center',
                spacing=20
            ),
            ft.Divider(height=10, color='transparent'),
            ft.Text('BUDGET REPORTS AND FINANCIAL PROJECTIONS', size=17, weight=ft.FontWeight.W_800),
            ft.Divider(height=10, color='transparent'),
            ft.Text('THIS IS A SAMPLE RESTRICTED PAGE, ONLY FOR THE PURPOSE OF ILLUSTRATION. THE TABLE BELOW DOES NOT REPRESENT ANY REAL INFORMATION OF ANY CORPORATE ENTITY. ', size=16, weight=ft.FontWeight.W_800),
            ft.Divider(height=15, color='transparent'),
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Department")),
                    ft.DataColumn(ft.Text("Budget Allocated (N)"), numeric=True),
                    ft.DataColumn(ft.Text("Amount Spent"), numeric=True),
                    ft.DataColumn(ft.Text("Remaining Budget"), numeric=True),
                    ft.DataColumn(ft.Text("Projection for Next Quarter"), numeric=True),
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("IT")),
                            ft.DataCell(ft.Text("50,500,000")),
                            ft.DataCell(ft.Text("40,320,000")),
                            ft.DataCell(ft.Text("10,180,000")),
                            ft.DataCell(ft.Text("45,320,000")),
                        ],
                    ),
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("Marketing")),
                            ft.DataCell(ft.Text("30,300,000")),
                            ft.DataCell(ft.Text("25,250,000")),
                            ft.DataCell(ft.Text("5,050,000")),
                            ft.DataCell(ft.Text("28,250,000")),
                        ],
                    ),
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text("Operations")),
                            ft.DataCell(ft.Text("16,700,000")),
                            ft.DataCell(ft.Text("15,620,000")),
                            ft.DataCell(ft.Text("1,080,000")),
                            ft.DataCell(ft.Text("17,620,000")),
                        ],
                    ),
                ],
            ),
        ]

        return ft.Container(
            expand=True,
            content=ft.Column(
                controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,  # Enables scrolling when content exceeds space
                on_scroll=self.on_scroll,
            ),
            alignment=ft.alignment.center,
            padding=20
        )
    
    def on_scroll(self, event):
        print(f"Scrolled to offset: {event.pixels}")

    def admin_logout(self, e):
        email = self.data_cipher.decrypt_data(self.user_data.get('email'))
        update_attendance(email=email, action='sign_out')
        self.page.go('/')
        self.page.client_storage.remove('admin_data')

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
            data_path = 'application_data/application_storage/registered_data.json'
            # Load activity log from a JSON file
            if os.path.exists(data_path):
                with open(data_path, 'r') as f:
                    activity_data = json.load(f)
            else:
                self.show_snackbar('No data present in the activity log for now. Try again later!')
                return

            # Extract relevant fields from the JSON
            extracted_data = []
            for user_data in activity_data:
                for attendance in user_data.get("attendance_status", []):
                    fullname = self.data_cipher.decrypt_data(user_data["fullname"])
                    email = self.data_cipher.decrypt_data(user_data["email"])
                    telephone = self.data_cipher.decrypt_data(user_data["telephone"])
                    extracted_data.append({
                        "fullname": fullname,
                        "email": email,
                        "telephone": telephone,
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

    