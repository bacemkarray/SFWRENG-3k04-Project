import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import user_db

class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DCM Interface Demo")
        self.state('zoomed')  # Windows
        self.resizable(True, True)

        # Create a main container that centers everything
        main_container = tk.Frame(self)
        main_container.pack(fill="both", expand=True)
        
        # Create a centered frame inside the main container
        centered_frame = tk.Frame(main_container)
        centered_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Dictionary to store page frames
        self.frames = {}

        # Register the page classes here
        for F in (WelcomePage, ModeSelectPage, ParameterPage, RegisterUserPage):
            frame = F(centered_frame, self)  # Use centered_frame as parent
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show initial page
        self.show_frame(WelcomePage)

    def show_frame(self, page_class):
        """Raise the given frame to the front."""
        frame = self.frames[page_class]
        frame.tkraise()

# ---------- Individual Pages ---------- #

class WelcomePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        label = ttk.Label(self, text="Welcome to the DCM Interface", font=("Arial", 16))
        label.pack(pady=30)

        ttk.Label(self, text="Username").pack()
        self.username_entry = ttk.Entry(self)
        self.username_entry.pack()

        ttk.Label(self, text="Password").pack()
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.pack()
        

        login_btn = ttk.Button(self, text="Login", command=self.login)
        login_btn.pack(pady=10)

        login_btn = ttk.Button(self, text="Register New User", command=lambda: controller.show_frame(RegisterUserPage))
        login_btn.pack(pady=10)

        quit_btn = ttk.Button(self, text="Quit", command=controller.destroy)
        quit_btn.pack(pady=10)
    
    def login(self):
        
        username = self.username_entry.get()
        password = self.password_entry.get()

        if user_db.check_login(username, password):
            self.controller.show_frame(ModeSelectPage)
        else:
            tk.messagebox.showerror("Login Failed", "Incorrect username or password")



class RegisterUserPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        label = ttk.Label(self, text="Welcome to the DCM Interface", font=("Arial", 16))
        label.pack(pady=30)

        ttk.Label(self, text="New Username").pack()
        self.username_entry = ttk.Entry(self)
        self.username_entry.pack()

        ttk.Label(self, text="New Password").pack()
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.pack()

        ttk.Label(self, text="Confirm Password").pack()
        self.password_confirm_entry = ttk.Entry(self, show="*")
        self.password_confirm_entry.pack()

        login_btn = ttk.Button(self, text="Register", command=self.register)
        login_btn.pack(pady=10)

        ttk.Button(self, text="Back to Welcome", command=lambda: controller.show_frame(WelcomePage)).pack(pady=20)
    
    def register(self):
        
        username = self.username_entry.get()
        password = self.password_entry.get()
        password_confirm = self.password_confirm_entry.get()

        if password == password_confirm:
            if user_db.register_user == "Max users reached.":
                tk.messagebox.showerror("Registration Failed", "Max users reached")
            elif user_db.register_user == "Username already exists.":
                tk.messagebox.showerror("Registration Failed", "Username already taken")
            else:
                user_db.register_user(username, password)
                tk.messagebox.showinfo("", "New user created")
                self.controller.show_frame(WelcomePage)

        else:
            tk.messagebox.showerror("Registration Failed", "Passwords do not match")


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