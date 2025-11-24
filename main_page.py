import tkinter as tk
from tkinter import ttk
import user_db
import parameters
from threading import Thread
import time

class Main(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DCM Interface Demo")
        self.geometry("700x500")
        self.resizable(False, False)
        
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

        # Container for all frames
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        # Frames dictionary
        self.frames = {}

        # Append each page into the frames dict (removed EgramPage)
        for F in (WelcomePage, ModeSelectPage, ParameterPage, RegisterUserPage):
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
    
    def monitor_connection(self):
        """Continuously check connection status and attempt to reconnect if disconnected"""
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
        self.controller = controller

        ttk.Label(self, text="Select Pacing Mode", font=("Arial", 14)).pack(pady=20)

        ttk.Button(self, text="AOO", command=lambda: self.select_mode("AOO")).pack(pady=5)
        ttk.Button(self, text="AAI", command=lambda: self.select_mode("AAI")).pack(pady=5)
        ttk.Button(self, text="VOO", command=lambda: self.select_mode("VOO")).pack(pady=5)
        ttk.Button(self, text="VVI", command=lambda: self.select_mode("VVI")).pack(pady=5)
        
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
        
        self.upload_button = ttk.Button(button_frame, text="Upload to Pacemaker",
                                command=self.upload_to_pacemaker)
        self.upload_button.pack(side="left", padx=5)

        self.show_params_button = ttk.Button(button_frame, text="Show Current Parameters",
                                    command=self.show_current_parameters)
        self.show_params_button.pack(side="left", padx=5)

        # Frame to display current parameters from pacemaker
        self.current_params_frame = tk.Frame(self)
        self.current_params_frame.pack(pady=10, fill="x", padx=20)
        
        # Label for current parameters section
        self.current_params_label = ttk.Label(self.current_params_frame, text="Current Pacemaker Parameters:", 
                                             font=("Arial", 12, "bold"))
        self.current_params_label.pack(anchor="w", pady=(0, 5))
        
        # Text widget to display parameters (read-only)
        self.params_text = tk.Text(self.current_params_frame, height=8, width=70, state="disabled")
        self.params_text.pack(fill="x")
        
        # Scrollbar for parameters text
        params_scrollbar = ttk.Scrollbar(self.current_params_frame, orient="vertical", command=self.params_text.yview)
        params_scrollbar.pack(side="right", fill="y")
        self.params_text.configure(yscrollcommand=params_scrollbar.set)

    def show_parameters(self):
        # Clear the frame
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        self.widgets.clear()

        mode = self.controller.current_mode
        self.title.config(text=f"{mode} Parameters")

        # Mode-specific param lists
        if mode == "AOO":
            params = ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"]
        elif mode == "AAI":
            params = ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width", "ARP"]
        elif mode == "VOO":
            params = ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"]
        elif mode == "VVI":
            params = ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width", "VRP"]
        else:
            params = []

        # Display entries
        for p in params:
            row = tk.Frame(self.form_frame)
            row.pack(pady=2, fill="x")

            ttk.Label(row, text=p, width=20, anchor="w").pack(side="left", padx=5)

            entry = ttk.Entry(row, width=12)
            entry.pack(side="left", padx=5)
            self.widgets[p] = entry

            # Placeholder for current pacemaker value
            current_label = ttk.Label(row, text="On-Device: --", width=15, anchor="w", foreground="gray")
            current_label.pack(side="left", padx=5)

    def upload_to_pacemaker(self):
        if not self.controller.pacemaker_connected:
            self.upload_msg.config(text="Cannot upload - Pacemaker not connected", foreground="red")
            return
        
        # Collect parameters and update the parameter manager
        for param_name, entry in self.widgets.items():
            value = entry.get().strip()
            if not value:
                self.upload_msg.config(text=f"Please enter value for {param_name}", foreground="red")
                return
            
            # Validate the parameter
            valid, msg = parameters.validate_param(param_name, value)
            if not valid:
                self.upload_msg.config(text=msg, foreground="red")
                return
            
            # Convert to appropriate format and set in parameter manager
            try:
                if param_name in ["Lower Rate Limit", "Upper Rate Limit", "ARP", "VRP"]:
                    # These are integer values
                    int_value = int(float(value))
                    if param_name == "Lower Rate Limit":
                        parameters.pacemaker_params.set_parameter('LRL', int_value)
                    elif param_name == "Upper Rate Limit":
                        parameters.pacemaker_params.set_parameter('URL', int_value)
                    elif param_name == "ARP":
                        parameters.pacemaker_params.set_parameter('ARP', int_value // 10)  # Convert to raw value
                    elif param_name == "VRP":
                        parameters.pacemaker_params.set_parameter('VRP', int_value // 10)  # Convert to raw value
                
                elif "Amplitude" in param_name:
                    # Convert voltage to raw value (multiply by 10)
                    raw_value = int(float(value) * 10)
                    if "Atrial" in param_name:
                        parameters.pacemaker_params.set_parameter('ATR_AMP', raw_value)
                    else:
                        parameters.pacemaker_params.set_parameter('VENT_AMP', raw_value)
                
                elif "Pulse Width" in param_name:
                    # Convert ms to raw value (multiply by 10)
                    raw_value = int(float(value) * 10)
                    if "Atrial" in param_name:
                        parameters.pacemaker_params.set_parameter('ATR_PULSE_WIDTH', raw_value)
                    else:
                        parameters.pacemaker_params.set_parameter('VENT_PULSE_WIDTH', raw_value)
                        
            except ValueError:
                self.upload_msg.config(text=f"Invalid value for {param_name}", foreground="red")
                return
        
        # Get the parameter bytes and send to pacemaker
        try:
            param_bytes = parameters.pacemaker_params.get_parameter_bytes()
            
            # Send raw parameters to pacemaker
            success = parameters.pacemaker_comm.send_raw_parameters(param_bytes)
            
            if success:
                self.upload_msg.config(text="✓ Parameters successfully uploaded to pacemaker", foreground="green")
                # Print the parameters for verification
                parameters.pacemaker_params.print_parameters()
            else:
                self.upload_msg.config(text="✗ Failed to upload parameters", foreground="red")
                
        except Exception as e:
            self.upload_msg.config(text=f"✗ Error: {str(e)}", foreground="red")

    def show_current_parameters(self):
        """Fetch and display current parameters from the pacemaker"""
        if not self.controller.pacemaker_connected:
            self.upload_msg.config(text="Cannot fetch parameters - Pacemaker not connected", foreground="red")
            return
        
        self.upload_msg.config(text="Requesting parameters from pacemaker...", foreground="blue")
        
        # Use a thread to avoid blocking the GUI
        from threading import Thread
        Thread(target=self._fetch_parameters_thread, daemon=True).start()

    def _fetch_parameters_thread(self):
        """Thread function to fetch parameters from pacemaker"""
        try:
            # Set to echo mode and send request
            parameters.pacemaker_params.set_echo_mode()
            echo_bytes = parameters.pacemaker_params.get_parameter_bytes()
            
            # Send echo request to pacemaker
            success = parameters.pacemaker_comm.send_raw_parameters(echo_bytes)
            
            if success:
                # Wait for response
                time.sleep(1)
                
                # Read response from pacemaker
                if parameters.pacemaker_comm.ser.in_waiting >= 18:
                    response = parameters.pacemaker_comm.ser.read(18)
                    
                    # Update the parameters from the response
                    self._update_parameters_from_response(response)
                    
                    # Switch back to parameter mode for future uploads
                    parameters.pacemaker_params.set_parameter_mode()
                    
                    # Update GUI in main thread
                    self.after(0, lambda: self.upload_msg.config(
                        text="✓ Successfully fetched parameters from pacemaker", 
                        foreground="green"
                    ))
                else:
                    self.after(0, lambda: self.upload_msg.config(
                        text="✗ No response from pacemaker", 
                        foreground="red"
                    ))
            else:
                self.after(0, lambda: self.upload_msg.config(
                    text="✗ Failed to send echo request", 
                    foreground="red"
                ))
                
        except Exception as e:
            self.after(0, lambda: self.upload_msg.config(
                text=f"✗ Error fetching parameters: {str(e)}", 
                foreground="red"
            ))

    def _update_parameters_from_response(self, response_bytes):
        """Update parameter manager and display from pacemaker response"""
        if len(response_bytes) != 18:
            print(f"Invalid response length: {len(response_bytes)} bytes")
            return
        
        try:
            # Update the parameter manager with the received bytes
            parameters.pacemaker_params.set_parameters_from_bytes(response_bytes)
            
            # Get user-friendly parameter summary
            summary = parameters.pacemaker_params.get_parameter_summary()
            
            # Format the display text
            display_text = f"""Mode: {summary['mode']}
Lower Rate Limit: {summary['lrl']} ppm
Upper Rate Limit: {summary['url']} ppm
Maximum Sensor Rate: {summary['msr']} ppm

Atrial Amplitude: {summary['atrial_amp']:.1f} V
Ventricular Amplitude: {summary['ventricular_amp']:.1f} V

Atrial Pulse Width: {summary['atrial_pw']:.1f} ms
Ventricular Pulse Width: {summary['ventricular_pw']:.1f} ms

Atrial Sensitivity: {summary['atrial_sens']:.1f} mV
Ventricular Sensitivity: {summary['ventricular_sens']:.1f} mV

ARP: {summary['arp']} ms
VRP: {summary['vrp']} ms

Activity Threshold: {summary['activity_threshold']}
Reaction Time: {summary['reaction_time']} s
Response Factor: {summary['response_factor']}
Recovery Time: {summary['recovery_time']} min"""
            
            # Update the display in the main thread
            self.after(0, lambda: self._update_parameters_display(display_text))
            
        except Exception as e:
            print(f"Error updating parameters from response: {e}")

    def _update_parameters_display(self, display_text):
        """Update the parameters text display"""
        self.params_text.config(state="normal")
        self.params_text.delete(1.0, tk.END)
        self.params_text.insert(1.0, display_text)
        self.params_text.config(state="disabled")

    def go_back(self):
        self.controller.show_frame(ModeSelectPage)

if __name__ == "__main__":
    app = Main()
    app.mainloop()