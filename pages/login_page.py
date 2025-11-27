from PyQt6.QtWidgets import QWidget
from py_ui.login_page import Ui_Form


class LoginPage(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Connect login button
        self.ui.LogIn_2.clicked.connect(self.handle_login)

        self.main_window = None

    def set_main_window(self, main_window):
        """Allows this page to call functions on MainWindow (e.g., navigation)."""
        self.main_window = main_window

    def handle_login(self):
        username = self.ui.UsernameEntryBox_2.text().strip()
        password = self.ui.PasswordEntryBox_2.text().strip()

        # Replace this later with real credential logic
        if username == "test" and password == "123":
            # Update global status (optional)
            self.main_window.update_status(True)

            # Navigate to dashboard (once you add it)
            # self.main_window.go_to_dashboard()
            print("Login successful!")
        else:
            # Optional: show incorrect credentials message
            self.ui.LoginError.setVisible(True)
            self.ui.LoginError.setText("Invalid username or password.")

            print("Invalid login.")
