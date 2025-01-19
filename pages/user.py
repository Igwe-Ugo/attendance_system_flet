import flet as ft
import os, io, base64
from PIL import Image
from pages.ultils import update_attendance, DataCipher

class User(ft.UserControl):
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
        self.signout_button_user = ft.Row(
            controls=[
                ft.Container(
                    border_radius=5,
                    expand=True,
                    bgcolor='#b4d4fb',
                    gradient=ft.LinearGradient(
                        colors=['#b4d4fb', '#848484', '#0f8389'],
                    ),
                    content=ft.Text('Sign out', text_align=ft.TextAlign.CENTER, size=18, color=ft.colors.WHITE),
                    padding=ft.padding.only(left=25, right=25, top=20, bottom=20),
                    on_click=self.logout_user,
                )
            ],
            alignment='center',
            vertical_alignment='center'
        )

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
            ft.Text('User Recognized!', size=19, weight=ft.FontWeight.W_900),
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
            self.signout_button_user,
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
            ft.Divider(height=10, color='transparent'),
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

    def logout_user(self, e):
        email = self.user_data.get('email')
        update_attendance(email=email, action='sign_out')

        # Retrieve the registered_by_admin flag
        registered_by_admin = self.page.client_storage.get("registered_by_admin")

        # Navigate based on the flag
        if registered_by_admin:
            self.page.go('/admin')  # Return to admin page
        else:
            self.page.go('/')  # Return to landing page

        # Clear user-related storage after navigation
        self.page.client_storage.remove('user_data')
        self.page.client_storage.remove('registered_by_admin')


    def show_snackbar(self, message):
        snackbar = ft.SnackBar(
            bgcolor=ft.colors.GREY_900,
            content=ft.Text(message, color=ft.colors.WHITE)
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    