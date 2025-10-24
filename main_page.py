import tkinter as tk
from tkinter import ttk
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
        label = ttk.Label(self, text="Welcome to the DCM Interface", font=("Arial", 16))
        label.pack(pady=30)

        ttk.Label(self, text="Username").pack()
        ttk.Entry(self).pack()

        ttk.Label(self, text="Password").pack()
        ttk.Entry(self).pack()

        login_btn = ttk.Button(self, text="Login", command=lambda: controller.show_frame(ModeSelectPage))
        login_btn.pack(pady=10)

        login_btn = ttk.Button(self, text="Register New User", command=lambda: controller.show_frame(RegisterUserPage))
        login_btn.pack(pady=10)

        quit_btn = ttk.Button(self, text="Quit", command=controller.destroy)
        quit_btn.pack(pady=10)



class RegisterUserPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        ttk.Label(self, text="Register New User", font=("Arial", 14)).pack(pady=20)

        ttk.Label(self, text="Username").pack()
        ttk.Entry(self).pack()

        ttk.Label(self, text="Password").pack()
        ttk.Entry(self).pack()

        ttk.Label(self, text="Confirm Password").pack()
        ttk.Entry(self).pack()

        ttk.Button(self, text="Back to Welcome", command=lambda: controller.show_frame(WelcomePage)).pack(pady=20)



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