import flet as ft

class LandingPage(ft.UserControl):
    def sign_in(self, e):
        self.page.go('/signin')

    def __init__(self, page):
        super().__init__()
        self.page = page
        self.lock = ft.Icon(
            name='lock',
            scale=ft.Scale(5)
        )
        
        self.buttonSignIn = ft.Container(
            border_radius=5,
            expand=True,
            bgcolor='#4f46e5',
            gradient=ft.LinearGradient(
                colors=['#ea580c', '#4f46e5'],
            ),
            content=ft.Text(
                'Sign In',
                color='White',
                size=20,
                text_align=ft.TextAlign.CENTER
            ),
            padding=ft.padding.only(left=25, right=25, top=20, bottom=20),
            on_click=self.sign_in,
        )

    def build(self):
        # Define the list of items to display
        return ft.Container(
            padding=ft.padding.only(left=25, right=25, top=10, bottom=10),
            content=ft.SafeArea(
                expand=True,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Divider(
                            height=120,
                            color='transparent'
                        ),
                        self.lock,
                        ft.Divider(
                            height=70,
                            color='transparent',
                        ),
                        ft.Text(
                            'Access Restricted',
                            size=30,
                            text_align='center',
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Divider(
                            height=20,
                            color='transparent',
                        ),
                        ft.Text(
                            "The resource you are about to access is protected and accessible only to authorized users. Attempting to access this page without proper authorization is prohibited. All activities are monitored and logged.",
                            size=20,
                            text_align='center',
                            weight=ft.FontWeight.W_800
                        ),
                        ft.Divider(
                            height=20,
                            color='transparent',
                        ),
                        ft.Text(
                            'If your are an authorized user, then sign in here. Ensure you log out after your session to protect your information.',
                            size=20,
                            text_align='center',
                            weight=ft.FontWeight.W_500
                        ),
                        ft.Divider(
                            height=60,
                            color='transparent'
                        ),
                        self.buttonSignIn
                    ],
                    horizontal_alignment='center'
                ),
            )
        )