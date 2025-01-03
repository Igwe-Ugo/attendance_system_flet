import re
import flet as ft

link_style = {
    "height": 50,
    "focused_border_color": '#4f46e5',
    "border_radius": 5,
    "cursor_height": 16,
    "cursor_color": "white",
    "content_padding": 10,
    "border_width": 1.5,
    "text_size": 14,
    "label_style": ft.TextStyle(
        color='#ea580c',
    )
}

regexEmail = r"^[a-zA-Z0-9.a-zA-Z0-9.!#$%&'*+-/=?^_`{|}~]+@[a-zA-Z0-9]+\.[a-zA-Z]+"

class SignUpPage(ft.UserControl):
    def __init__(self, page) -> None:
        super().__init__()
        self.page = page

        self.fullname = ft.TextField(
            password=False,
            label='Enter fullname',
            **link_style,
        )

        self.email_address = ft.TextField(
            password=False,
            **link_style,
            label='Enter email address'
        )

        self.telephone = ft.TextField(
            password=False,
            **link_style,
            label='Enter phone number',
        )

        self.registerButton = ft.Container(
            border_radius=5,
            expand=True,
            bgcolor='#4f46e5',
            gradient=ft.LinearGradient(
                colors=['#ea580c', '#4f46e5'],
            ),
            content=ft.Text(
                'Register',
                color='white',
                size=20,
                text_align=ft.TextAlign.CENTER
            ),
            padding=ft.padding.only(left=25, right=25, top=20, bottom=20),
            on_click=self.check_signup_fields,
        )

        # using expanded and row to make the button span the full page width
        self.register_button_row = ft.Row(
            controls=[
               self.registerButton
            ],
            alignment='center',
            vertical_alignment='center'
        )

    def build(self):
        # Define the list of items to display
        return ft.Container(
            expand=True,  # Ensures the container expands to fill the screen
            padding=ft.padding.only(left=25, right=25, top=10, bottom=10),
            content=ft.SafeArea(
                expand=True,  # Expand SafeArea to fill the screen
                content=ft.Column(
                    expand=True,  # Ensure the column also takes full height
                    controls=[
                        ft.Text(
                            'Welcome to the Sign Up Page',
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            text_align='center'
                        ),
                        ft.Divider(
                            height=10,
                            color='transparent'
                        ),
                        ft.Column(
                            spacing=20,
                            controls=[
                                self.fullname,
                                self.email_address,
                                self.telephone,
                                ft.Divider(
                                    height=50,
                                    color='transparent'
                                ),
                                self.register_button_row
                            ]
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            )
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

    def check_signup_fields(self, e):
        fullname = self.fullname.value
        email_address = self.email_address.value
        telephone = self.telephone.value

        if not (fullname and email_address and telephone):
            self.show_snackbar("All fields must be filled to proceed.")
        elif not re.match(regexEmail, email_address):
            self.show_snackbar("Invalid email address. Please enter a valid email.")
        else:
            # Store user credentials in client_storage
            self.page.client_storage.set("fullname", fullname)
            self.page.client_storage.set("email", email_address)
            self.page.client_storage.set("telephone", telephone)
            self.page.go('/register_face')
