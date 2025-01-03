import threading
import flet as ft
from pages.landing_page import LandingPage
from pages.signup import SignUpPage
from pages.register_face import RegisterFace
from pages.user import User
from pages.signin import SignInPage
from pages.ultils import CameraManager

def main(page: ft.Page):
    page.title = "Flet Face Recognition Application"
    page.theme_mode = ft.ThemeMode.DARK
    camera_manager = CameraManager()

    def show_snackbar(message):
        """Display a snackbar with a message using the new Flet method."""
        snackbar = ft.SnackBar(
            bgcolor=ft.colors.GREY_900,
            content=ft.Text(message, color=ft.colors.WHITE)
        )
        # Append the snackbar to the page's overlay and make it visible
        page.overlay.append(snackbar)
        snackbar.open = True
        page.update()  # Refresh the page to show the snackbar

    # defining the routes to navigate to in the whole system
    def route_change(route):
        if page.route == '/':
            page.views.append(LandingPage(page))
        elif page.route == "/signup":
            page.views.append(
                ft.View(
                    route="/signup",
                    controls=[
                        ft.AppBar(
                            leading=ft.IconButton(
                                icon=ft.icons.ARROW_BACK_IOS,
                                icon_size=20,
                                tooltip='Back to Landing Page',
                                on_click=lambda _: page.go("/")
                            ),
                            title=ft.Text("Sign Up"),
                            bgcolor=ft.colors.SURFACE_VARIANT
                        ),
                        SignUpPage(page)
                    ]
                )
            )
        elif page.route == "/register_face":
            page.views.append(
                ft.View(
                    route="/register_face",
                    controls=[
                        ft.AppBar(
                            leading=ft.IconButton(
                                icon=ft.icons.ARROW_BACK_IOS,
                                icon_size=20,
                                tooltip='Back to Sign Up Page',
                                on_click=lambda _: disable_cam(route="/")
                            ),
                            title=ft.Text("Register face"),
                            bgcolor=ft.colors.SURFACE_VARIANT
                        ),
                        RegisterFace(page, camera_manager),
                    ]
                )
            )
        elif page.route.startswith("/user"):
            # Extract user data from the route
            print("Loading User page")
            user_data = page.client_storage.get("recognized_user_data")
            status = page.client_storage.get('status')
            if user_data:
                page.views.append(
                    ft.View(
                        route="/user",
                        controls=[
                            User(page=page, status=status, user_data=user_data),
                        ]
                    )
                )
            else:
                show_snackbar('No User found with this face, please signup! Redirecting to Sign Up...')
                page.go("/signup")
        elif page.route == "/signin":
            page.views.append(
                ft.View(
                    route="/signin",
                    controls=[
                        ft.AppBar(
                            leading=ft.IconButton(
                                icon=ft.icons.ARROW_BACK_IOS,
                                icon_size=20,
                                tooltip='Back to Landing Page',
                                on_click=lambda _: disable_cam(route="/")
                            ),
                            title=ft.Text("Sign In"),
                            bgcolor=ft.colors.SURFACE_VARIANT
                        ),
                        SignInPage(page, camera_manager)
                    ]
                )
            )
        else:
            show_snackbar("Invalid route. Redirecting to the landing page.")
            page.go("/")

        page.update()

    # function that the system should navigate to when the on_screen page is popped
    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

    def disable_cam(route):
        camera_manager.release_camera()
        page.go(route)
        threading.Timer(0.1, lambda: page.go(route)).start() # delayed navigation

if __name__ == '__main__':
    ft.app(target=main, assets_dir='assets')
