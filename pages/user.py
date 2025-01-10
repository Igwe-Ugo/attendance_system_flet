import flet as ft
import os, io, base64
from PIL import Image
import pandas as pd
import datetime, json
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
                    bgcolor='#4f46e5',
                    gradient=ft.LinearGradient(
                        colors=['#ea580c', '#4f46e5'],
                    ),
                    content=ft.Text('Sign out', text_align=ft.TextAlign.CENTER, size=18, color=ft.colors.WHITE),
                    padding=ft.padding.only(left=25, right=25, top=20, bottom=20),
                    on_click=self.go_home,
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
                    img = img.resize((250, 250))  # Resize image for display
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
            ft.Image(src_base64=img_data, border_radius=10) if img_data else ft.Text('No Image available'),
            ft.Text(f"Full Name: {plain_fullname}"),
            ft.Text(f"Email: {plain_email}"),
            ft.Text(f"Phone: {plain_telephone}"),
            ft.Divider(height=10, color='transparent'),
            self.signout_button_user,
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

    def go_home(self, e):
        email = self.user_data.get('email')
        update_attendance(email=email, action='sign_out')
        self.page.client_storage.remove("session")
        self.page.go('/admin')

    def show_snackbar(self, message):
        snackbar = ft.SnackBar(
            bgcolor=ft.colors.GREY_900,
            content=ft.Text(message, color=ft.colors.WHITE)
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    