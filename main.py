from PyQt6.QtWidgets import QApplication, QMainWindow
from py_ui.main_window import Ui_MainWindow
from pages.login_page import LoginPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # GLOBAL STATUS STATE
        self.update_status(False)

        # Create Pages
        self.login_page = LoginPage()
        self.login_page.set_main_window(self)

        # Add pages to stacked widget
        self.ui.stackedWidget.addWidget(self.login_page)

        # Start on login
        self.ui.stackedWidget.setCurrentWidget(self.login_page)

    def update_status(self, connected: bool):
        if connected:
            color = "green"
            text = "Pacemaker Connected"
        else:
            color = "red"
            text = "Pacemaker Disconnected"

        self.ui.StatusIndicator.setStyleSheet(
            f"background-color: {color}; border-radius: 8px;"
        )
        self.ui.StatusLabel.setText(text)

    def go_to_dashboard(self):
        # You will add dashboard page later
        print("Switching to dashboard page...")
        # self.ui.stackedWidget.setCurrentWidget(self.dashboard_page)

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()