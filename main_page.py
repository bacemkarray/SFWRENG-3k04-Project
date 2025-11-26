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
        self.geometry("700x700")
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
        
        self.upload_button = ttk.Button(button_frame, text="Upload to Pacemaker",
                                command=self.upload_to_pacemaker)
        self.upload_button.pack(side="left", padx=5)

        self.show_params_button = ttk.Button(button_frame, text="Show Current Parameters",
                                    command=self.show_current_parameters)
        self.show_params_button.pack(side="left", padx=5)

        self.measured_params = {
            # Byte 1: Always 0x16 (SYNC)
            'SYNC': 0,
            
            # Byte 2: Function Code (0x55 for set parameters, 0x22 for echo)
            'FnCode': 0,
            
            # Byte 3: Mode (1-8)
            'Mode': 0,  # Default to AOO
            
            # Byte 4: Lower Rate Limit (30-175 ppm)
            'Lower Rate Limit': 0,
            
            # Byte 5: Upper Rate Limit (50-175 ppm)
            'Upper Rate Limit': 0,
            
            # Byte 6: Maximum Sensor Rate (50-175 ppm)
            'MSR': 0,
            
            # Byte 7: Atrial Amplitude (0-50 = 0-5.0V when divided by 10)
            'Atrial Amplitude': 0,  # 2.5V
            
            # Byte 8: Ventricular Amplitude (0-50 = 0-5.0V when divided by 10)
            'Ventricular Amplitude': 0,  # 2.5V
            
            # Byte 9: Atrial Pulse Width (1-19 = 0.1-1.9ms when divided by 10)
            'Atrial Pulse Width': 0,  # 1.0ms
            
            # Byte 10: Ventricular Pulse Width (1-19 = 0.1-1.9ms when divided by 10)
            'Ventricular Pulse Width': 0,  # 1.0ms
            
            # Byte 11: Atrial Sensitivity (10-100 = 1.0-10.0mV when divided by 10)
            'ATR_SENS': 0,  # 5.0mV
            
            # Byte 12: Ventricular Sensitivity (10-100 = 1.0-10.0mV when divided by 10)
            'VENT_SENS': 0,  # 5.0mV
            
            # Byte 13: VRP (15-50 = 150-500ms when multiplied by 10)
            'VRP': 0,  # 250ms
            
            # Byte 14: ARP (15-50 = 150-500ms when multiplied by 10)
            'ARP': 0,  # 250ms
            
            # Byte 15: Activity Threshold (0-255, unclear range)
            'ACTIVITY_THRESHOLD': 0,
            
            # Byte 16: Reaction Time (10-50 seconds)
            'REACTION_TIME': 0,
            
            # Byte 17: Response Factor (1-16)
            'RESPONSE_FACTOR': 0,
            
            # Byte 18: Recovery Time (2-16 minutes)
            'RECOVERY_TIME': 0
        }
        

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

            # Get current value from parameter manager
            current_value = parameters.pacemaker_params.get_parameter(p)
            display_value = self._format_display_value(p, current_value)
            
            current_label = ttk.Label(row, text=f"On-Device: {display_value}", width=15, anchor="w", foreground="gray")
            current_label.pack(side="left", padx=5)

    def _format_display_value(self, param_name, raw_value):
        """Convert raw parameter value to display format"""
        if raw_value is None:
            return "N/A"
        
        if "Amplitude" in param_name:
            return f"{raw_value/10:.1f}V"
        elif "Pulse Width" in param_name:
            return f"{raw_value/10:.1f}ms"
        elif param_name in ["ARP", "VRP"]:
            return f"{raw_value*10}ms"
        elif param_name in ["ATR_SENS", "VENT_SENS"]:
            return f"{raw_value/10:.1f}mV"
        else:
            return str(raw_value)

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
                        parameters.pacemaker_params.set_parameter('Lower Rate Limit', int_value)
                    elif param_name == "Upper Rate Limit":
                        parameters.pacemaker_params.set_parameter('Upper Rate Limit', int_value)
                    elif param_name == "ARP":
                        parameters.pacemaker_params.set_parameter('ARP', int_value // 10)  # Convert to raw value
                    elif param_name == "VRP":
                        parameters.pacemaker_params.set_parameter('VRP', int_value // 10)  # Convert to raw value
                
                elif "Amplitude" in param_name:
                    # Convert voltage to raw value (multiply by 10)
                    raw_value = int(float(value) * 10)
                    if "Atrial" in param_name:
                        parameters.pacemaker_params.set_parameter('Atrial Amplitude', raw_value)
                    else:
                        parameters.pacemaker_params.set_parameter('Ventricular Amplitude', raw_value)
                
                elif "Pulse Width" in param_name:
                    # Convert ms to raw value (multiply by 10)
                    raw_value = int(float(value) * 10)
                    if "Atrial" in param_name:
                        parameters.pacemaker_params.set_parameter('Atrial Pulse Width', raw_value)
                    else:
                        parameters.pacemaker_params.set_parameter('Ventricular Pulse Width', raw_value)
                        
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
            # Clear the serial buffer first
            if parameters.pacemaker_comm.ser.in_waiting > 0:
                parameters.pacemaker_comm.ser.read(parameters.pacemaker_comm.ser.in_waiting)
            
            # Set to echo mode and send request
            parameters.pacemaker_params.set_echo_mode()
            echo_bytes = parameters.pacemaker_params.get_parameter_bytes()
            
            # Send echo request to pacemaker
            success = parameters.pacemaker_comm.send_raw_parameters(echo_bytes)
            
            if success:
                # Wait longer for response and read available data
                time.sleep(2)  # Increased from 1 second
                
                # Read response from pacemaker
                if parameters.pacemaker_comm.ser.in_waiting >= 18:
                    response = parameters.pacemaker_comm.ser.read(18)
                    
                    print(f"Received {len(response)} bytes from pacemaker:")
                    for i, byte in enumerate(response):
                        print(f"  Byte {i}: {byte} (0x{byte:02x})")
                    
                    # Update the parameters from the response
                    self._update_parameters_from_response(response)
                    
                    # Refresh the display in main thread
                    self.after(0, self._refresh_display)
                    
                    # Switch back to parameter mode for future uploads
                    parameters.pacemaker_params.set_parameter_mode()
                    
                    # Update GUI in main thread
                    self.after(0, lambda: self.upload_msg.config(
                        text="✓ Successfully fetched parameters from pacemaker", 
                        foreground="green"
                    ))
                else:
                    bytes_available = parameters.pacemaker_comm.ser.in_waiting
                    self.after(0, lambda: self.upload_msg.config(
                        text=f"✗ No response from pacemaker (only {bytes_available} bytes available)", 
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

    def _refresh_display(self):
        """Refresh the parameter display with current values"""
        self.show_parameters()

    def _update_parameters_from_response(self, response_bytes):
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

    def go_back(self):
        self.controller.show_frame(ModeSelectPage)

import csv
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

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
        ttk.Button(control_frame, text="Test with CSV", command=self.test_with_csv).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Clear Graph", command=self.clear_display).pack(side="left", padx=5)
        
        ttk.Button(self, text="Back to Mode Select", command=self.go_back).pack(pady=5)
        
        # Create matplotlib figure for graphing
        self.fig = Figure(figsize=(6, 4), dpi=100)
        
        # Create single plot for both signals
        self.ax = self.fig.add_subplot(111)
        
        # Configure plot
        self.ax.set_title('Egram Signals', fontsize=10)
        self.ax.set_xlabel('Time (s)', fontsize=8)
        self.ax.set_ylabel('Amplitude', fontsize=8)
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(['Atrial', 'Ventricular'], loc='upper right', fontsize=8)
        
        self.fig.tight_layout()
        
        # Embed the figure in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Data storage for plotting
        self.time_data = []
        self.atrial_data = []
        self.ventricular_data = []
        self.start_time = None
        
        # Control flag for continuous reading
        self.reading_egram = False
        
        # Display window parameters (show last N seconds)
        self.display_window = 5.0  # Show last 5 seconds
        
        # Lines for real-time plotting
        self.atrial_line, = self.ax.plot([], [], 'b-', linewidth=1, label='Atrial')
        self.ventricular_line, = self.ax.plot([], [], 'r-', linewidth=1, label='Ventricular')
        self.ax.legend()
        
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
        
        # Start reading in a separate thread
        thread = Thread(target=self._fetch_egram_thread, daemon=True)
        thread.start()
    
    def stop_egram(self):
        """Stop the egram reading"""
        self.reading_egram = False
        self.egram_msg.config(text="Egram reading stopped", foreground="blue")
    
    def clear_display(self):
        """Clear the egram display"""
        self.time_data.clear()
        self.atrial_data.clear()
        self.ventricular_data.clear()
        
        self.atrial_line.set_data([], [])
        self.ventricular_line.set_data([], [])
        
        self.ax.relim()
        self.ax.autoscale_view()
        
        self.canvas.draw()
        self.egram_msg.config(text="Display cleared", foreground="blue")
    
    def test_with_csv(self):
        """Load and display data from heart_data.csv for testing"""
        if self.reading_egram:
            self.egram_msg.config(text="Stop current egram reading first", foreground="orange")
            return
        
        # Check if CSV file exists
        csv_path = "heart_data.csv"
        if not os.path.exists(csv_path):
            self.egram_msg.config(text="✗ heart_data.csv not found", foreground="red")
            return
        
        self.reading_egram = True
        self.start_time = time.time()
        self.egram_msg.config(text="Loading test data from CSV...", foreground="green")
        
        # Start CSV reading in a separate thread
        thread = Thread(target=self._read_csv_thread, args=(csv_path,), daemon=True)
        thread.start()
    
    def _read_csv_thread(self, csv_path):
        """Thread function to read and display CSV data"""
        try:
            sample_count = 0
            
            with open(csv_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    if not self.reading_egram:
                        break
                    
                    # Parse the CSV row
                    time_val = float(row['Time(s)'])
                    ventricular = int(row['Ventricular'])
                    atrial = int(row['Atrial'])
                    
                    sample_count += 1
                    
                    # Update plot data
                    self.after(0, lambda t=time_val, a=atrial, v=ventricular: 
                              self._add_data_point(t, a, v))
                    
                    # Update plot every 10 samples
                    if sample_count % 10 == 0:
                        self.after(0, self._update_plot)
                    
                    # Simulate real-time playback
                    time.sleep(0.01)  # 10ms between samples
                
                # Final plot update
                self.after(0, self._update_plot)
            
            self.reading_egram = False
            self.after(0, lambda c=sample_count: self.egram_msg.config(
                text=f"✓ Played back {c} samples from CSV", 
                foreground="green"
            ))
                
        except Exception as e:
            self.reading_egram = False
            self.after(0, lambda: self.egram_msg.config(
                text=f"✗ Error reading CSV: {str(e)}", 
                foreground="red"
            ))
    
    def _fetch_egram_thread(self):
        """Thread function to continuously fetch egram data from pacemaker"""
        try:
            # Clear the serial buffer first
            if parameters.pacemaker_comm.ser.in_waiting > 0:
                parameters.pacemaker_comm.ser.read(parameters.pacemaker_comm.ser.in_waiting)
            
            sample_count = 0
            
            while self.reading_egram:
                # Check if pacemaker is still connected
                if not self.controller.pacemaker_connected:
                    self.after(0, lambda: self.egram_msg.config(
                        text="✗ Pacemaker disconnected", 
                        foreground="red"
                    ))
                    self.reading_egram = False
                    break
                
                # Read 16 bytes of egram data
                if parameters.pacemaker_comm.ser.in_waiting >= 16:
                    egram_data = parameters.pacemaker_comm.ser.read(16)
                    
                    if len(egram_data) == 16:
                        # Calculate elapsed time
                        current_time = time.time() - self.start_time
                        
                        # Parse 4 atrial samples (2 bytes each)
                        for i in range(0, 8, 2):
                            sample = int.from_bytes(egram_data[i:i+2], 'little', signed=False)
                            # Add time offset for each sample (assuming ~1ms between samples)
                            sample_time = current_time + (i/8) * 0.004
                            self.after(0, lambda t=sample_time, a=sample, v=0: 
                                      self._add_data_point(t, a, v))
                        
                        # Parse 4 ventricular samples (2 bytes each)
                        for i in range(8, 16, 2):
                            sample = int.from_bytes(egram_data[i:i+2], 'little', signed=False)
                            idx = i - 8
                            sample_time = current_time + (idx/8) * 0.004
                            # Update ventricular data for this time point
                            if len(self.ventricular_data) > 0:
                                self.ventricular_data[-4 + idx//2] = sample
                        
                        sample_count += 1
                        
                        # Update plot periodically
                        if sample_count % 10 == 0:
                            self.after(0, self._update_plot)
                
                time.sleep(0.01)  # Small delay
            
            # Final update
            self.after(0, lambda c=sample_count: self.egram_msg.config(
                text=f"✓ Captured {c} egram samples", 
                foreground="green"
            ))
                
        except Exception as e:
            self.reading_egram = False
            self.after(0, lambda: self.egram_msg.config(
                text=f"✗ Error reading egram: {str(e)}", 
                foreground="red"
            ))
    
    def _add_data_point(self, time_val, atrial_val, ventricular_val):
        """Add a data point to the plot buffers"""
        self.time_data.append(time_val)
        self.atrial_data.append(atrial_val)
        self.ventricular_data.append(ventricular_val)
        
        # Keep only last 1000 points to prevent memory issues
        if len(self.time_data) > 1000:
            self.time_data.pop(0)
            self.atrial_data.pop(0)
            self.ventricular_data.pop(0)
    
    def _update_plot(self):
        """Update the matplotlib plot with current data"""
        try:
            if len(self.time_data) == 0:
                return
            
            # Update line data
            self.atrial_line.set_data(self.time_data, self.atrial_data)
            self.ventricular_line.set_data(self.time_data, self.ventricular_data)
            
            # Get the latest time value
            latest_time = self.time_data[-1]
            
            # Set x-axis limits to show a scrolling window
            self.ax.set_xlim(latest_time - self.display_window, latest_time)
            
            # Auto-scale y-axis only
            self.ax.relim()
            self.ax.autoscale_view(scalex=False, scaley=True)
            
            # Redraw canvas
            self.canvas.draw()
            
        except Exception as e:
            print(f"Plot update error: {e}")
    
    def go_back(self):
        # Stop reading if still active
        if self.reading_egram:
            self.stop_egram()
            time.sleep(0.5)  # Give thread time to stop
        
        self.controller.show_frame(ModeSelectPage)


if __name__ == "__main__":
    app = Main()
    app.mainloop()