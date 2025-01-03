import flet as ft

class LandingPage(ft.UserControl):
    def sign_up(self, e):
        self.page.go('/signup')

    def sign_in(self, e):
        self.page.go('/signin')

    def __init__(self, page):
        super().__init__()
        self.page = page
        self.lock = ft.Icon(
            name='lock',
            scale=ft.Scale(5)
        )

        # define button to route to signup or signin screen
        self.buttonSignUp = ft.Container(
            border_radius=5,
            expand=True,
            bgcolor='#4f46e5',
            gradient=ft.LinearGradient(
                colors=['#ea580c', '#4f46e5'],
            ),
            content=ft.Text(
                'Sign Up',
                color='white',
                size=20,
                text_align=ft.TextAlign.CENTER
            ),
            padding=ft.padding.only(left=25, right=25, top=20, bottom=20),
            on_click=self.sign_up,
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
                    controls=[
                        ft.Column(
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
                                    'Attendance system',
                                    size=30,
                                    text_align='center',
                                ),
                                ft.Divider(
                                    height=120,
                                    color='transparent'
                                ),
                            ],
                            horizontal_alignment='center'
                        ),
                        ft.Row(
                            controls=[
                                self.buttonSignUp,
                                self.buttonSignIn
                            ],
                            alignment='center',
                            spacing=20
                        )
                    ]
                )
            )
        )