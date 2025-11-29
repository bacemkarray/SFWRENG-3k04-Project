import tkinter as tk
from tkinter import ttk
import user_db as user_db
import parameters as parameters
from threading import Thread
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import struct


class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DCM Interface Demo")
        self.geometry("1000x1000")
        self.resizable(False, False)

        # Font size options
        self.font_sizes = {
            "normal": {"title": 16, "label": 10, "button": 10},
            "medium": {"title": 20, "label": 12, "button": 12},
            "large": {"title": 24, "label": 14, "button": 14}
        }
        self.current_font_size = "normal"

        # Pacemaker status indicator
        self.status_frame = tk.Frame(self)
        self.status_frame.pack(side="top", anchor="ne", padx=10, pady=10)
        self.status_canvas = tk.Canvas(self.status_frame, width=20, height=20, highlightthickness=0)
        self.status_canvas.pack(side="left")
        self.status_label = ttk.Label(self.status_frame, text="Pacemaker Disconnected", font=("Arial", 10))
        self.status_label.pack(side="left", padx=5)
        

        # Connection management - initialize FIRST
        self.pacemaker_connected = False
        
        # Connect button - create BEFORE calling set_connection_status
        self.connect_btn = ttk.Button(self.status_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side="left", padx=10)

        # NOW set the initial status
        self.set_connection_status(self.pacemaker_connected)
        self.apply_fonts(self)


        # Container for all frames
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        # Frames dictionary
        self.frames = {}

        # Append each page into the frames dict
        for F in (WelcomePage, ModeSelectPage, ParameterPage, RegisterUserPage, EgramPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show welcome page by default
        self.show_frame(WelcomePage)
        
        # Start connection monitoring
        self.monitor_connection()

    def show_frame(self, page_class):
        frame = self.frames[page_class]
        frame.tkraise()
        if page_class == ParameterPage:
            frame.show_parameters()

    def set_connection_status(self, connected: bool):
        self.pacemaker_connected = connected 
        self.status_canvas.delete("all")
        if connected:
            self.status_canvas.create_oval(2, 2, 18, 18, fill="green")
            self.status_label.config(text="Pacemaker Connected")
            self.connect_btn.config(text="Disconnect")
        else:
            self.status_canvas.create_oval(2, 2, 18, 18, fill="red")
            self.status_label.config(text="Pacemaker Disconnected")
            self.connect_btn.config(text="Connect")

    def toggle_connection(self):
        if not self.pacemaker_connected:
            # Try to connect
            if parameters.pacemaker_comm.connect():
                self.set_connection_status(True)
            else:
                self.set_connection_status(False)
        else:
            # Disconnect
            parameters.pacemaker_comm.disconnect()
            self.set_connection_status(False)
    
    
    # continuously check connection status and attempt to reconnect if disconnected
    def monitor_connection(self):
        def check():
            while True:
                try:
                    # If not connected, attempt to reconnect automatically
                    if self.pacemaker_connected:
                        # Try to connect
                        if not parameters.pacemaker_comm.check_connection():
                            self.after(0, lambda: self.set_connection_status(False))
                            self.after(0, lambda: parameters.pacemaker_comm.disconnect())
                            print("Auto Disconnected")
                        
                except Exception as e:
                    print(f"Connection monitor error: {e}")
                    # If there's an error, assume disconnected
                    if self.pacemaker_connected:
                        self.after(0, lambda: self.set_connection_status(False))
                
                time.sleep(1)  # Check every second
        
        # Start the monitoring thread
        monitor_thread = Thread(target=check, daemon=True)
        monitor_thread.start()

    #Update all fonts inside a frame based on current size
    def apply_fonts(self, frame):
        sizes = self.font_sizes[self.current_font_size]

        for widget in frame.winfo_children():
            if isinstance(widget, (ttk.Label, tk.Label)):
                widget.config(font=("Arial", sizes["label"]))
            elif isinstance(widget, ttk.Button):
                widget.config(style="TButton")
            elif isinstance(widget, ttk.Entry):
                widget.config(font=("Arial", sizes["label"]))

            # Recursively update nested frames
            if isinstance(widget, tk.Frame):
                self.apply_fonts(widget)

        # Create updated button style
        style = ttk.Style()
        style.configure("TButton", font=("Arial", sizes["button"]))



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

        # Font size selector
        ttk.Label(self, text="Font Size").pack(pady=5)
        self.font_select = ttk.Combobox(
            self, values=["Normal", "Medium", "Large"], state="readonly"
        )
        self.font_select.current(0)
        self.font_select.pack()

        # Apply font size on change
        self.font_select.bind("<<ComboboxSelected>>", self.change_font_size)

        controller.apply_fonts(self)

    def change_font_size(self, event):
        size_map = {"Normal": "normal", "Medium": "medium", "Large": "large"}
        selected = self.font_select.get()
        self.controller.current_font_size = size_map[selected]

        # Apply new font sizes to *all* pages
        for frame in self.controller.frames.values():
            self.controller.apply_fonts(frame)
        self.controller.apply_fonts(self.controller)

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
        self.controller = controller
        ttk.Label(self, text="Select Pacing Mode", font=("Arial", 14)).pack(pady=20)

        ttk.Button(self, text="AOO", command=lambda: self.select_mode("AOO")).pack(pady=5)
        ttk.Button(self, text="AAI", command=lambda: self.select_mode("AAI")).pack(pady=5)
        ttk.Button(self, text="VOO", command=lambda: self.select_mode("VOO")).pack(pady=5)
        ttk.Button(self, text="VVI", command=lambda: self.select_mode("VVI")).pack(pady=5)
        ttk.Button(self, text="AOOR", command=lambda: self.select_mode("AOOR")).pack(pady=5)
        ttk.Button(self, text="VOOR", command=lambda: self.select_mode("VOOR")).pack(pady=5)
        ttk.Button(self, text="AAIR", command=lambda: self.select_mode("AAIR")).pack(pady=5)
        ttk.Button(self, text="VVIR", command=lambda: self.select_mode("VVIR")).pack(pady=5)
        ttk.Button(self, text="Egram Display", command=lambda: controller.show_frame(EgramPage)).pack(pady=20)
        ttk.Button(self, text="Back", command=lambda: controller.show_frame(WelcomePage)).pack(pady=20)

    def select_mode(self, mode):
        self.controller.current_mode = mode
        # Set the mode in the parameters manager
        parameters.pacemaker_params.set_mode(mode)
        self.controller.show_frame(ParameterPage)

class ParameterPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.widgets = {}
        self.title = ttk.Label(self, text="", font=("Arial", 14))
        self.title.pack(pady=10)
        self.form_frame = tk.Frame(self)
        self.form_frame.pack(pady=10)
        self.back_button = ttk.Button(self, text="Back to Modes", command=self.go_back)
        self.back_button.pack(pady=10)
        
        # Message labels
        self.upload_msg = ttk.Label(self, text="", foreground="red")
        self.upload_msg.pack(pady=5)

        # Button frame for Upload and Show Parameters
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)
        
        self.upload_button = ttk.Button(button_frame, text="Upload to Pacemaker", command=self.upload_to_pacemaker)
        self.upload_button.pack(side="left", padx=5)

        self.show_params_button = ttk.Button(button_frame, text="Show Current Parameters", command=self.show_current_parameters)
        self.show_params_button.pack(side="left", padx=5)
        self.save_profile_button = ttk.Button(button_frame, text="Save to Profile", command=self.save_profile)
        self.save_profile_button.pack(side="left", padx=5)
        self.load_profile_button = ttk.Button(button_frame,text="Fetch From Profile", command=self.load_profile)
        self.load_profile_button.pack(side="left", padx=5)

        controller.apply_fonts(self)
        
    # save data to profile
    def save_profile(self):
        username = self.controller.current_user
        mode = self.controller.current_mode

        profile = user_db.get_user_profile(username)

        mode_dict = {}

        for param_name, entry in self.widgets.items():
            display_value = entry.get().strip()
            if param_name == "Activity Threshold":
                display_value = parameters.ACTIVITY_MAP[display_value]

            mode_dict[param_name] = display_value
            profile[mode] = mode_dict
            user_db.save_user_profile(username, profile)

    # save data to profile
    def load_profile(self):
        username = self.controller.current_user
        mode = self.controller.current_mode
        profile = user_db.get_user_profile(username)

        mode_dict = profile[mode]

        for param_name, entry in self.widgets.items():
            if param_name in mode_dict:
                display = mode_dict[param_name]
                # convert value from number back to string (e.g "V-Low")
                if param_name == "Activity Threshold":
                    display = parameters.REVERSE_ACTIVITY_MAP[display]

                if isinstance(entry, ttk.Combobox):
                    entry.set(str(display))
                else:
                    entry.delete(0, tk.END)
                    entry.insert(0, str(display))
    
    # Creates the dropdowns for each param
    def create_dropdown(self, parent, param_name):
        if param_name in ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate"]:
            values = [x for x in range(30, 176, 5)]
            cb = ttk.Combobox(parent, values=values, width=10, state="readonly")
            cb.pack(side="left", padx=5)
            return cb
        if "Amplitude" in param_name:
            values = [round(x,1) for x in np.arange(0.1, 5.1, 0.1)]
            # values = [x for x in range(0.1, 5.1, 0.1)]
            cb = ttk.Combobox(parent, values=values, width=10, state="readonly")
            cb.pack(side="left", padx=5)
            return cb
        if "Pulse Width" in param_name:
            values = [x for x in range(1, 31, 1)]
            cb = ttk.Combobox(parent, values=values, width=10, state="readonly")
            cb.pack(side="left", padx=5)
            return cb
        if "Sensitivity" in param_name:
            values = [round(x,1) for x in np.arange(0.0, 5.1, 0.1)]
            # values = [x for x in range(0, 5.1, 0.1)]
            cb = ttk.Combobox(parent, values=values, width=10, state="readonly")
            cb.pack(side="left", padx=5)
            return cb
        if param_name in ["ARP", "VRP"]:
            values = [x for x in range(150, 510, 10)]
            cb = ttk.Combobox(parent, values=values, width=10, state="readonly")
            cb.pack(side="left", padx=5)
            return cb
        if param_name == "Activity Threshold":
            values = ["V-Low", "Low", "Med-Low", "Med", "Med-High", "High", "V-High"]
            cb = ttk.Combobox(parent, values=values, width=10, state="readonly")
            cb.pack(side="left", padx=5)
            return cb
        if param_name == "Reaction Time":
            values = [x for x in range(10, 60, 10)]
            cb = ttk.Combobox(parent, values=values, width=10, state="readonly")
            cb.pack(side="left", padx=5)
            return cb
        if param_name == "Response Factor":
            values = [x for x in range(1, 17, 1)]
            cb = ttk.Combobox(parent, values=values, width=10, state="readonly")
            cb.pack(side="left", padx=5)
            return cb
        if param_name == "Recovery Time":
            values = [x for x in range(2, 17, 1)]
            cb = ttk.Combobox(parent, values=values, width=10, state="readonly")
            cb.pack(side="left", padx=5)
            return cb

    # Show the parameters for the given mode
    def show_parameters(self):
        # Clear
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        self.widgets.clear()

        mode = self.controller.current_mode
        self.title.config(text=f"{mode} Parameters")

        params = parameters.MODE_PARAMETER_LAYOUT.get(mode, [])

        for p in params:
        
            row = tk.Frame(self.form_frame)
            row.pack(fill="x", pady=3)

            ttk.Label(row, text=p).pack(side="left", padx=5)

            entry = self.create_dropdown(row, p)
            self.widgets[p] = entry

            # Retrieve raw value already stored in pacemaker_params
            if not self.controller.pacemaker_connected:
                display_value = "—"
            else:
                raw_value = parameters.pacemaker_params.get_parameter(p)
                display_value = self.format_display_value(p, raw_value)

            ttk.Label(row, text=f"On-Device: {display_value}", foreground="gray").pack(side="left", padx=10)
            

    # convert raw parameter value to display format
    def format_display_value(self, param_name, raw_value):
        if raw_value is None:
            return "N/A"
        if "Amplitude" in param_name:
            return f"{raw_value/10:.1f}V"
        elif "Pulse Width" in param_name:
            return f"{raw_value/10:.1f}ms"
        elif param_name in ["ARP", "VRP"]:
            return f"{raw_value*10}ms"
        elif param_name in ["Atrial Sensitivity", "Ventricular Sensitivity"]:
            return f"{raw_value/10:.1f}mV"
        else:
            return str(raw_value)

    # upload data to pacemaker
    def upload_to_pacemaker(self):
        for param_name, entry in self.widgets.items():
            if 'Lower Rate Limit' in self.widgets and 'Upper Rate Limit' in self.widgets:
                lrl = float(self.widgets['Lower Rate Limit'].get().strip())
                url = float(self.widgets['Upper Rate Limit'].get().strip())
                
                if url < lrl:
                    self.upload_msg.config(
                        text="Upper Rate Limit cannot be lower than the Lower Rate Limit",
                        foreground="red")
                    return
        if not self.controller.pacemaker_connected:
            self.upload_msg.config(text="Cannot upload - Pacemaker not connected", foreground="red")
            return
        
        for param_name, entry in self.widgets.items():
            value = entry.get().strip()
            if param_name == "Activity Threshold":
                raw = parameters.ACTIVITY_MAP[value]
                parameters.pacemaker_params.set_parameter("Activity Threshold", raw)
                continue
            if not value:
                self.upload_msg.config(text=f"Please enter value for {param_name}", foreground="red")
                return
            
            # validate the parameter
            valid, msg = parameters.validate_param(param_name, value)
            if not valid:
                self.upload_msg.config(text=msg, foreground="red")
                return
            
            # convert to appropriate format and set in parameter manager
            if param_name in ["Lower Rate Limit", "Upper Rate Limit", "ARP", "VRP"]:
                # These are integer values
                int_value = int(value)
                if param_name == "Lower Rate Limit":
                    parameters.pacemaker_params.set_parameter('Lower Rate Limit', int_value)
                elif param_name == "Upper Rate Limit":
                    parameters.pacemaker_params.set_parameter('Upper Rate Limit', int_value)
                elif param_name == "ARP":
                    parameters.pacemaker_params.set_parameter('ARP', int_value // 10)  # convert to raw value
                elif param_name == "VRP":
                    parameters.pacemaker_params.set_parameter('VRP', int_value // 10)  # convert to raw value
            
            elif "Amplitude" in param_name:
                # Convert voltage to raw value
                raw_value = int(value * 10)
                if "Atrial" in param_name:
                    parameters.pacemaker_params.set_parameter('Atrial Amplitude', raw_value)
                else:
                    parameters.pacemaker_params.set_parameter('Ventricular Amplitude', raw_value)
            
            elif "Pulse Width" in param_name:
                # convert ms to raw value
                raw_value = int(value * 10)
                if "Atrial" in param_name:
                    parameters.pacemaker_params.set_parameter('Atrial Pulse Width', raw_value)
                else:
                    parameters.pacemaker_params.set_parameter('Ventricular Pulse Width', raw_value)
                        
        
        # get the parameter bytes and send to pacemaker
        try:
            param_bytes = parameters.pacemaker_params.get_parameter_bytes()
            
            # Send raw parameters to pacemaker
            success = parameters.pacemaker_comm.send_raw_parameters(param_bytes)
            
            if success:
                self.upload_msg.config(text="Parameters successfully uploaded to pacemaker", foreground="green")
                # Print the parameters for verification
                parameters.pacemaker_params.print_parameters()
            else:
                self.upload_msg.config(text="Failed to upload parameters", foreground="red")
                
        except Exception as e:
            self.upload_msg.config(text=f"Error: {str(e)}", foreground="red")


    # fetch then display params 
    def show_current_parameters(self):
        if not self.controller.pacemaker_connected:
            self.upload_msg.config(text="Cannot fetch parameters - Pacemaker not connected", foreground="red")
            return
        
        self.upload_msg.config(text="Requesting parameters from pacemaker...", foreground="blue")
        Thread(target=self.fetch_parameters_thread, daemon=True).start()


    # Fetch params from pacemaker
    def fetch_parameters_thread(self):
        try:
            # Clear the serial buffer first
            if parameters.pacemaker_comm.ser.in_waiting > 0:
                parameters.pacemaker_comm.ser.read(parameters.pacemaker_comm.ser.in_waiting)
            
            # Set to echo mode and send request
            parameters.pacemaker_params.set_echo_mode()
            echo_bytes = parameters.pacemaker_params.get_parameter_bytes()
            
            # Send echo request to pacemaker
            success = parameters.pacemaker_comm.send_raw_parameters(echo_bytes)
            
            if success:
                # Wait for response and read available data
                time.sleep(2) 
                
                # Read response from pacemaker
                if parameters.pacemaker_comm.ser.in_waiting >= 18:
                    response = parameters.pacemaker_comm.ser.read(18)
                    
                    print(f"Received {len(response)} bytes from pacemaker:")
                    for i, byte in enumerate(response):
                        print(f"  Byte {i}: {byte} (0x{byte:02x})")
                    
                    # update the parameters from the response
                    self.update_parameters_from_response(response)
                    
                    # refresh the display in main thread
                    self.after(0, self.refresh_display)
                    
                    # switch back to parameter mode for future uploads
                    parameters.pacemaker_params.set_parameter_mode()
                    
                    # update GUI in main thread
                    self.after(0, lambda: self.upload_msg.config(
                        text="Successfully fetched parameters from pacemaker", 
                        foreground="green"
                    ))
                else:
                    bytes_available = parameters.pacemaker_comm.ser.in_waiting
                    self.after(0, lambda: self.upload_msg.config(
                        text=f"No response from pacemaker (only {bytes_available} bytes available)", 
                        foreground="red"
                    ))
            else:
                self.after(0, lambda: self.upload_msg.config(
                    text="Failed to send echo request", 
                    foreground="red"
                ))
                
        except Exception as e:
            self.after(0, lambda: self.upload_msg.config(text=f"Error fetching parameters: {str(e)}", foreground="red"))


    #  
    def update_parameters_from_response(self, response_bytes):
        """Update parameter manager and display from pacemaker response"""
        if len(response_bytes) != 18:
            print(f"Invalid response length: {len(response_bytes)} bytes")
            return
        
        try:
            # Update the parameter manager with the received bytes
            success = parameters.pacemaker_params.set_parameters_from_bytes(response_bytes)
            if success:
                print("Parameters successfully updated from pacemaker response")
                # Print the updated parameters for verification
                parameters.pacemaker_params.print_parameters()
            else:
                print("Failed to update parameters from response")
                
        except Exception as e:
            print(f"Error updating parameters from response: {e}")


    # refresh the param display with the current values
    def refresh_display(self):
        self.show_parameters()
        self.controller.apply_fonts(self)

    def go_back(self):
        self.controller.show_frame(ModeSelectPage)



class EgramPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ttk.Label(self, text="Egram Display", font=("Arial", 14)).pack(pady=10)
        
        self.egram_msg = ttk.Label(self, text="", foreground="red")
        self.egram_msg.pack(pady=5)
        
        # Frame for controls
        control_frame = tk.Frame(self)
        control_frame.pack(pady=5)
        
        ttk.Button(control_frame, text="Start Egram", command=self.start_egram).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Stop Egram", command=self.stop_egram).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Clear Graph", command=self.clear_display).pack(side="left", padx=5)
        
        # Frame for gain and filter controls
        settings_frame = tk.Frame(self)
        settings_frame.pack(pady=5)
        
        # Gain control
        ttk.Label(settings_frame, text="Gain:").pack(side="left", padx=5)
        self.gain_var = tk.DoubleVar(value=1.0)
        ttk.Radiobutton(settings_frame, text="0.5x", variable=self.gain_var, value=0.5, command=self.update_plot).pack(side="left", padx=2)
        ttk.Radiobutton(settings_frame, text="1x", variable=self.gain_var, value=1.0, command=self.update_plot).pack(side="left", padx=2)
        ttk.Radiobutton(settings_frame, text="2x", variable=self.gain_var, value=2.0, command=self.update_plot).pack(side="left", padx=2)
        
        # High-pass filter control
        ttk.Label(settings_frame, text="  High-Pass Filter:").pack(side="left", padx=(15, 5))
        self.filter_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Enable", variable=self.filter_var, command=self.update_plot).pack(side="left", padx=2)
        
        ttk.Button(self, text="Back to Mode Select", command=self.go_back).pack(pady=5)

        # Two subplots: atrial (top), ventricular (bottom)
        self.fig = Figure(figsize=(6, 5), dpi=100)

        self.ax_atrial = self.fig.add_subplot(211)
        self.ax_vent = self.fig.add_subplot(212)

        # Labeling and grid
        self.ax_atrial.set_title('Atrial Data', fontsize=10)
        self.ax_atrial.set_ylabel('Amplitude', fontsize=8)
        self.ax_atrial.grid(True, alpha=0.3)
        self.ax_atrial.set_ylim(-5, 5)
        self.ax_vent.set_ylim(-5, 5)
        self.ax_vent.set_title('Ventricular Data', fontsize=10)
        self.ax_vent.set_xlabel('Time (s)', fontsize=8)
        self.ax_vent.set_ylabel('Amplitude', fontsize=8)
        self.ax_vent.grid(True, alpha=0.3)

        # Create lines for each subplot
        self.atrial_line, = self.ax_atrial.plot([], [], 'b-', linewidth=1)
        self.ventricular_line, = self.ax_vent.plot([], [], 'r-', linewidth=1)

        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        
        # DATA STORAGE
        self.time_data = []
        self.atrial_data = []
        self.ventricular_data = []
        self.atrial_data_raw = []
        self.ventricular_data_raw = []
        self.start_time = None
        
        # Control flag for continuous reading
        self.reading_egram = False
        
        # Display window parameters
        self.display_window = 5.0
        # Matplotlib lines
        self.atrial_line, = self.ax_atrial.plot([], [], 'b-', linewidth=1, label='Atrial')
        self.ventricular_line, = self.ax_vent.plot([], [], 'r-', linewidth=1, label='Ventricular')

    
    # start the graph
    def start_egram(self):
        if not self.controller.pacemaker_connected:
            self.egram_msg.config(text="Cannot read egram - Pacemaker not connected", foreground="red")
            return
        
        if self.reading_egram:
            self.egram_msg.config(text="Egram reading already in progress", foreground="orange")
            return
            
        self.reading_egram = True
        self.start_time = time.time()
        self.egram_msg.config(text="Reading egram data...", foreground="green")
        
        # Read data in separate thread.
        thread = Thread(target=self.fetch_egram_thread, daemon=True)
        thread.start()
    
    
    def stop_egram(self):
        self.reading_egram = False
        self.egram_msg.config(text="Egram reading stopped", foreground="blue")
    
    
    def clear_display(self):
        self.time_data.clear()
        self.atrial_data.clear()
        self.ventricular_data.clear()
        self.atrial_data_raw.clear()
        self.ventricular_data_raw.clear()        
        self.atrial_line.set_data([], [])
        self.ax_atrial.set_xlim(0, self.display_window)
        self.ax_vent.set_xlim(0, self.display_window)
        self.ventricular_line.set_data([], [])
        self.canvas.draw()
        self.egram_msg.config(text="Display cleared", foreground="blue")
    
    
    #Fetch from serial data
    def fetch_egram_thread(self):
        try:
            # Clear serial buffer
            if parameters.pacemaker_comm.ser.in_waiting > 0:
                parameters.pacemaker_comm.ser.read(parameters.pacemaker_comm.ser.in_waiting)
            
            sample_count = 0
            
            echo_packet = self.build_echo_packet()
            parameters.pacemaker_comm.ser.write(echo_packet)
            print("Echo packet sent to start egram capture")
            
            while self.reading_egram:
                if not self.controller.pacemaker_connected:
                    self.after(0, lambda: self.egram_msg.config(
                        text="Pacemaker disconnected",
                        foreground="red"
                    ))
                    self.reading_egram = False
                    break
                
                if parameters.pacemaker_comm.ser.in_waiting >= 32:
                    packet_data = parameters.pacemaker_comm.ser.read(32)
                    
                    if len(packet_data) == 32:
                        egram_bytes = packet_data[16:32]
                        
                        try:
                            atrial_value = struct.unpack('<d', egram_bytes[0:8])[0]
                            ventricular_value = struct.unpack('<d', egram_bytes[8:16])[0]
                            
                            current_time = time.time() - self.start_time
                            
                            self.after(0, lambda t=current_time, a=atrial_value, v=ventricular_value:
                                       self.add_data_point(t, a, v))
                            
                            sample_count += 1
                            print(f"Sample {sample_count}: Atrial={atrial_value:.6f}, Ventricular={ventricular_value:.6f}")
                            
                            self.after(0, self.update_plot)
                            
                            parameters.pacemaker_comm.ser.write(echo_packet)
                        
                        except struct.error as e:
                            print(f"Error unpacking egram data: {e}")
                
                time.sleep(0.1)
            
            self.after(0, lambda c=sample_count: self.egram_msg.config(
                text=f"Captured {c} egram samples",
                foreground="green"
            ))
                
        except Exception as e:
            self.reading_egram = False
            self.after(0, lambda: self.egram_msg.config(
                text=f"Error reading egram: {str(e)}",
                foreground="red"
            ))
            print(f"Egram thread error: {e}")
    

    # echo packet builder. will request egram data 
    def build_echo_packet(self):
        return bytearray([
            0x16, 0x22, 1, 60, 120, 120, 35, 35,
            4, 4, 75, 75, 32, 25, 10, 30,
            8, 5
        ])


    # add data point
    def add_data_point(self, time_val, atrial_val, ventricular_val):
        self.time_data.append(time_val)
        
        self.atrial_data_raw.append(atrial_val)
        self.ventricular_data_raw.append(ventricular_val)
        
        gain = self.gain_var.get()
        use_filter = self.filter_var.get()
        
        if use_filter and len(self.atrial_data_raw) and len(self.ventricular_data_raw) > 1:
            # high pass filter implementation
            atrial_filtered = (atrial_val - self.atrial_data_raw[-2]) / 2.0
            ventricular_filtered = (ventricular_val - self.ventricular_data_raw[-2]) / 2.0
            
            self.atrial_data.append(atrial_filtered * gain)
            self.ventricular_data.append(ventricular_filtered * gain)
        else:
            self.atrial_data.append(atrial_val * gain)
            self.ventricular_data.append(ventricular_val * gain)
        
        # only keep track of up to 1000 samples
        if len(self.time_data) > 1000:
            self.time_data.pop(0)
            self.atrial_data.pop(0)
            self.ventricular_data.pop(0)
            self.atrial_data_raw.pop(0)
            self.ventricular_data_raw.pop(0)


    # update the plot for every new point
    def update_plot(self):
        try:
            if len(self.time_data) == 0:
                return
            
            gain = self.gain_var.get()
            use_filter = self.filter_var.get()
            
            self.atrial_data.clear()
            self.ventricular_data.clear()
            
            for i in range(len(self.atrial_data_raw)):
                # apply the filter
                if use_filter and i > 0:
                    a_f = (self.atrial_data_raw[i] - self.atrial_data_raw[i - 1]) / 2.0
                    v_f = (self.ventricular_data_raw[i] - self.ventricular_data_raw[i - 1]) / 2.0
                    
                    # scale the FILTERED data point by the selected gain
                    self.atrial_data.append(a_f * gain)
                    self.ventricular_data.append(v_f * gain)
                else:
                    # scale the data point by the selected gain
                    self.atrial_data.append(self.atrial_data_raw[i] * gain)
                    self.ventricular_data.append(self.ventricular_data_raw[i] * gain)

            self.atrial_line.set_data(self.time_data, self.atrial_data)
            self.ventricular_line.set_data(self.time_data, self.ventricular_data)

            latest_time = self.time_data[-1]

            self.ax_atrial.set_xlim(latest_time - self.display_window, latest_time)
            self.ax_vent.set_xlim(latest_time - self.display_window, latest_time)
            self.canvas.draw()
        
        except Exception as e:
            print(f"Plot update error: {e}")
    
    def go_back(self):
        if self.reading_egram:
            self.stop_egram()
            time.sleep(0.5)
        
        self.controller.show_frame(ModeSelectPage)



if __name__ == "__main__":
    app = Main()
    app.mainloop()