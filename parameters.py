import serial
import struct
import time
from typing import Tuple

PARAMETER_RULES = {
    "Lower Rate Limit": (50, 175),
    "Upper Rate Limit": (50, 175),
    "Maximum Sensor Rate": (50, 175),
    "Fixed AV Delay": (70, 300),
    "Atrial Amplitude": (0.5, 7.0),
    "Atrial Pulse Width": (0.05, 1.9),
    "Atrial Sensitivity": (0.25, 10.0),
    "Ventricular Amplitude": (0.5, 7.0),
    "Ventricular Pulse Width": (0.05, 1.9),
    "Ventricular Sensitivity": (0.25, 10.0),
    "ARP": (150, 500),
    "VRP": (150, 500)
}

# Mode mapping
MODE_MAP = {
    "AOO": 5,
    "AAI": 6, 
    "VOO": 7,
    "VVI": 8
}

def validate_param(param_name, value):
    rule = PARAMETER_RULES.get(param_name)
    try:
        val = float(value)
    except ValueError:
        return False, f"{param_name} must be numeric."

    low, high = rule
    if not (low <= val <= high):
        return False, f"{param_name} must be between {low} and {high}."
    
    return True, ""

class PacemakerCommunicator:
    def __init__(self, port='COM5', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.connected = False
        
    def connect(self):
        """Establish connection with pacemaker"""
        try:
            if self.ser is None:
                self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            elif not self.ser.is_open:
                self.ser.open()
                
            self.connected = True
            print(f"Connected to {self.port}")
            return True
        except serial.SerialException as e:
            print(f"Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False
        print("Disconnected")
    
    def send_parameters(self, mode: str, params: dict) -> Tuple[bool, str]:
        """Send parameters to pacemaker"""
        if not self.connected:
            return False, "Not connected to pacemaker"
        
        try:
            # Get mode code
            mode_code = MODE_MAP.get(mode, 8)  # Default to VVI
            
            # Extract parameters with defaults
            lrl = int(params.get("Lower Rate Limit", 60))
            url = int(params.get("Upper Rate Limit", 120))
            atrial_amp = float(params.get("Atrial Amplitude", 3.5))
            ventricular_amp = float(params.get("Ventricular Amplitude", 3.5))
            atrial_pw = float(params.get("Atrial Pulse Width", 0.4))
            ventricular_pw = float(params.get("Ventricular Pulse Width", 0.4))
            arp = int(params.get("ARP", 250))
            vrp = int(params.get("VRP", 320))
            
            # Create parameter packet
            param_data = struct.pack("=BHHHffffHH",
                mode_code,          # 1 byte - mode
                lrl,                # 2 bytes - lower rate limit
                url,                # 2 bytes - upper rate limit  
                120,                # 2 bytes - max sensor rate (default)
                atrial_amp,         # 4 bytes - atrial amplitude
                ventricular_amp,    # 4 bytes - ventricular amplitude  
                atrial_pw,          # 4 bytes - atrial pulse width
                ventricular_pw,     # 4 bytes - ventricular pulse width
                arp,                # 2 bytes - ARP
                vrp                 # 2 bytes - VRP
            )
            
            # Send command (0x01 for parameters)
            command = struct.pack("=B", 0x01)
            full_message = command + param_data
            
            # Add checksum
            checksum = self._calculate_checksum(full_message)
            full_message += struct.pack("=B", checksum)
            
            # Send to pacemaker
            self.ser.write(full_message)
            print(f"Sent {mode} parameters to pacemaker")
            
            # Wait for acknowledgment
            time.sleep(0.5)
            if self.ser.in_waiting > 0:
                ack = self.ser.read(1)
                if ack and ack[0] == 0x06:  # ACK
                    return True, "Parameters successfully sent and acknowledged"
            
            return True, "Parameters sent (no ACK received)"  # Still return True for testing
                
        except Exception as e:
            return False, f"Communication error: {e}"
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate simple checksum for error detection"""
        return sum(data) & 0xFF
    
    def read_egram(self, duration: float = 5.0):
        """Read egram data from pacemaker"""
        if not self.connected:
            print("Not connected to pacemaker")
            return None, None
        
        try:
            # Send egram request command
            request = struct.pack("=B33x", 0x55)
            self.ser.write(request)
            
            print(f"Reading egram data for {duration} seconds...")
            atrial_data = []
            ventricular_data = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                if self.ser.in_waiting >= 81:  # 80 bytes data + 1 control byte
                    data = self.ser.read(81)
                    control_byte = data[0]
                    
                    if control_byte == 0:  # ECG data
                        # Unpack egram data (20 floats)
                        egram_data = struct.unpack("=20f", data[1:])
                        atrial_data.extend(egram_data[:10])
                        ventricular_data.extend(egram_data[10:])
                    
                time.sleep(0.1)
            
            return atrial_data, ventricular_data
                
        except Exception as e:
            print(f"Egram read error: {e}")
            return None, None

# Create the global communicator instance
pacemaker_comm = PacemakerCommunicator()