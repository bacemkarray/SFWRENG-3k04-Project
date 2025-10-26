import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import user_db

class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DCM Interface Demo")
        self.geometry("700x500")
        self.resizable(False, False)
        
        # Pacemaker status indicator. Exists globally.
        self.status_frame = tk.Frame(self)
        self.status_frame.pack(side="top", anchor="ne", padx=10, pady=10)
        self.status_canvas = tk.Canvas(self.status_frame, width=20, height=20, highlightthickness=0)
        self.status_canvas.pack(side="left")
        self.status_label = ttk.Label(self.status_frame, text="Pacemaker Disconnected", font=("Arial", 10))
        self.status_label.pack(side="left", padx=5)

        # Container for all frames
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        # Frames dictionary
        self.frames = {}

        # Append each page into the frames dict
        for F in (WelcomePage, ModeSelectPage, ParameterPage, RegisterUserPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show welcome page by default
        self.show_frame(WelcomePage)

        self.set_connection_status(False)

    def show_frame(self, page_class):
        """Raise the given frame to the front."""
        frame = self.frames[page_class]
        frame.tkraise()

    def set_connection_status(self, connected: bool):
        self.status_canvas.delete("all")
        if connected:
            self.status_canvas.create_oval(2, 2, 18, 18, fill="green")
            self.status_label.config(text="Pacemaker Connected")
        else:
            self.status_canvas.create_oval(2, 2, 18, 18, fill="red")
            self.status_label.config(text="Pacemaker Disconnected")


# pages

class WelcomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ttk.Label(self, text="Welcome to the DCM Interface", font=("Arial", 16))
        label.pack(pady=10)

        ttk.Label(self, text="Username").pack()
        self.username_entry = ttk.Entry(self)
        self.username_entry.pack()

        ttk.Label(self, text="Password").pack()
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.pack()

        self.message_label = ttk.Label(self, text="", foreground="red")
        self.message_label.pack(pady=5)

        login_btn = ttk.Button(self, text="Login", command=self.login_user)
        login_btn.pack(pady=10)

        register_btn = ttk.Button(self, text="Register New User", command=self.go_register)
        register_btn.pack(pady=10)

        quit_btn = ttk.Button(self, text="Quit", command=controller.destroy)
        quit_btn.pack(pady=10)

    def login_user(self):
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()

            if user_db.check_login(username, password):
                self.controller.current_user = username
                self.controller.show_frame(ModeSelectPage)
            else:
                self.message_label.config(text="Invalid username or password")

    def go_register(self):
        self.controller.show_frame(RegisterUserPage)



class RegisterUserPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Register New User", font=("Arial", 14)).pack(pady=20)

        ttk.Label(self, text="Username").pack()
        self.username_entry = ttk.Entry(self)
        self.username_entry.pack()

        ttk.Label(self, text="Password").pack()
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.pack()

        ttk.Label(self, text="Confirm Password").pack()
        self.confirm_entry = ttk.Entry(self, show="*")
        self.confirm_entry.pack()

        self.message_label = ttk.Label(self, text="")
        self.message_label.pack(pady=10)

        ttk.Button(self, text="Register", command=self.register_user).pack(pady=10)
        ttk.Button(self, text="Back to Welcome", command=self.go_back).pack(pady=5)

    def register_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        confirm = self.confirm_entry.get().strip()

        if password != confirm:
            self.message_label.config(text="Passwords do not match", foreground="red")
            return

        success = user_db.register_user(username, password)

        if success:
            self.message_label.config(text="User created successfully!", foreground="green")
        else:
            self.message_label.config(text="Username exists or max users reached.", foreground="red")

    def go_back(self):
        self.controller.show_frame(WelcomePage)



class ModeSelectPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        ttk.Label(self, text="Select Pacing Mode", font=("Arial", 14)).pack(pady=20)

        # Example buttons for pacing modes
        ttk.Button(self, text="AOO Mode", command=lambda: controller.show_frame(ParameterPage)).pack(pady=5)
        ttk.Button(self, text="VVI Mode", command=lambda: controller.show_frame(ParameterPage)).pack(pady=5)

        ttk.Button(self, text="Back to Welcome", command=lambda: controller.show_frame(WelcomePage)).pack(pady=20)


class ParameterPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        ttk.Label(self, text="Parameter Settings", font=("Arial", 14)).pack(pady=15)

        ttk.Label(self, text="Lower Rate Limit:").pack()
        ttk.Entry(self).pack()

        ttk.Label(self, text="Upper Rate Limit:").pack()
        ttk.Entry(self).pack()

        ttk.Button(self, text="Save", command=lambda: print("Parameters saved")).pack(pady=10)
        ttk.Button(self, text="Back to Mode Select", command=lambda: controller.show_frame(ModeSelectPage)).pack(pady=10)


if __name__ == "__main__":
    app = Main()
    app.mainloop()