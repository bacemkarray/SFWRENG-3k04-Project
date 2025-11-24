# parameters.py

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
    
    def check_connection(self) -> bool:
        """Check if the pacemaker is still connected"""
        if not self.ser or not self.ser.is_open:
            self.connected = False
            return False
        
        try:
            # Try to read the port status - if it fails, we're disconnected
            self.ser.in_waiting
            self.connected = True
            return True
        except (serial.SerialException, OSError):
            # Port is disconnected
            self.connected = False
            return False
    
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
            print(f"Reading egram data for {duration} seconds...")
            atrial_data = []
            ventricular_data = []
            start_time = time.time()
            samples_collected = 0
            
            # Clear any existing data in the buffer first
            if self.ser.in_waiting > 0:
                self.ser.read(self.ser.in_waiting)
            
            while time.time() - start_time < duration:
                if self.ser.in_waiting >= 4:
                    data = self.ser.read(4)
                    
                    if len(data) == 4:
                        # Interpret as 16-bit unsigned integers
                        vent = int.from_bytes(data[0:2], 'little', signed=False)
                        atr = int.from_bytes(data[2:4], 'little', signed=False)
                        
                        ventricular_data.append(vent)
                        atrial_data.append(atr)
                        samples_collected += 1
                
                time.sleep(0.001)  # 1ms delay for high sampling rate
            
            print(f"Collected {samples_collected} egram samples")
            
            if samples_collected == 0:
                print("No egram data received - is the heart simulator running?")
                return None, None
                
            return atrial_data, ventricular_data
                
        except Exception as e:
            print(f"Egram read error: {e}")
            return None, None

    def send_raw_parameters(self, param_bytes: bytes) -> bool:
        """Send raw parameter bytes to pacemaker"""
        if not self.connected:
            return False
        
        try:
            self.ser.write(param_bytes)
            print(f"Sent {len(param_bytes)} bytes to pacemaker")
            return True
        except Exception as e:
            print(f"Failed to send parameters: {e}")
            return False

class PacemakerParameters:
    def __init__(self):
        # Initialize with default values according to the protocol
        self.parameters = {
            # Byte 1: Always 0x16 (SYNC)
            'SYNC': 0x16,
            
            # Byte 2: Function Code (0x55 for set parameters, 0x22 for echo)
            'FnCode': 0x55,
            
            # Byte 3: Mode (1-8)
            'Mode': 1,  # Default to AOO
            
            # Byte 4: Lower Rate Limit (30-175 ppm)
            'LRL': 60,
            
            # Byte 5: Upper Rate Limit (50-175 ppm)
            'URL': 120,
            
            # Byte 6: Maximum Sensor Rate (50-175 ppm)
            'MSR': 120,
            
            # Byte 7: Atrial Amplitude (0-50 = 0-5.0V when divided by 10)
            'ATR_AMP': 25,  # 2.5V
            
            # Byte 8: Ventricular Amplitude (0-50 = 0-5.0V when divided by 10)
            'VENT_AMP': 25,  # 2.5V
            
            # Byte 9: Atrial Pulse Width (1-19 = 0.1-1.9ms when divided by 10)
            'ATR_PULSE_WIDTH': 10,  # 1.0ms
            
            # Byte 10: Ventricular Pulse Width (1-19 = 0.1-1.9ms when divided by 10)
            'VENT_PULSE_WIDTH': 10,  # 1.0ms
            
            # Byte 11: Atrial Sensitivity (10-100 = 1.0-10.0mV when divided by 10)
            'ATR_SENS': 50,  # 5.0mV
            
            # Byte 12: Ventricular Sensitivity (10-100 = 1.0-10.0mV when divided by 10)
            'VENT_SENS': 50,  # 5.0mV
            
            # Byte 13: VRP (15-50 = 150-500ms when multiplied by 10)
            'VRP': 25,  # 250ms
            
            # Byte 14: ARP (15-50 = 150-500ms when multiplied by 10)
            'ARP': 25,  # 250ms
            
            # Byte 15: Activity Threshold (0-255, unclear range)
            'ACTIVITY_THRESHOLD': 10,
            
            # Byte 16: Reaction Time (10-50 seconds)
            'REACTION_TIME': 30,
            
            # Byte 17: Response Factor (1-16)
            'RESPONSE_FACTOR': 8,
            
            # Byte 18: Recovery Time (2-16 minutes)
            'RECOVERY_TIME': 5
        }
        
        # Mode mapping for user-friendly names
        self.mode_mapping = {
            'AOO': 1, 'VOO': 2, 'AAI': 3, 'VVI': 4,
            'AOOR': 5, 'VOOR': 6, 'AAIR': 7, 'VVIR': 8
        }
        
        # Reverse mode mapping for display
        self.mode_names = {v: k for k, v in self.mode_mapping.items()}

    def set_parameter(self, param_name: str, value: int) -> bool:
        """
        Set a parameter with validation
        
        Args:
            param_name: Name of the parameter to set
            value: Value to set
            
        Returns:
            bool: True if successful, False if validation failed
        """
        if param_name not in self.parameters:
            print(f"Error: Unknown parameter '{param_name}'")
            return False
        
        # Parameter validation rules
        validation_rules = {
            'SYNC': (0x16, 0x16),  # Must always be 0x16
            'FnCode': (0x22, 0x55),  # Either 0x22 or 0x55
            'Mode': (1, 8),
            'LRL': (30, 175),
            'URL': (50, 175),
            'MSR': (50, 175),
            'ATR_AMP': (0, 50),
            'VENT_AMP': (0, 50),
            'ATR_PULSE_WIDTH': (1, 19),
            'VENT_PULSE_WIDTH': (1, 19),
            'ATR_SENS': (10, 100),
            'VENT_SENS': (10, 100),
            'VRP': (15, 50),
            'ARP': (15, 50),
            'ACTIVITY_THRESHOLD': (0, 255),
            'REACTION_TIME': (10, 50),
            'RESPONSE_FACTOR': (1, 16),
            'RECOVERY_TIME': (2, 16)
        }
        
        min_val, max_val = validation_rules.get(param_name, (0, 255))
        
        if not (min_val <= value <= max_val):
            print(f"Error: {param_name} must be between {min_val} and {max_val}")
            return False
        
        self.parameters[param_name] = value
        print(f"Set {param_name} = {value}")
        return True

    def set_mode(self, mode_name: str) -> bool:
        """
        Set pacing mode by name
        
        Args:
            mode_name: Mode name (AOO, VOO, AAI, VVI, AOOR, VOOR, AAIR, VVIR)
            
        Returns:
            bool: True if successful, False if invalid mode
        """
        mode_code = self.mode_mapping.get(mode_name.upper())
        if mode_code is None:
            print(f"Error: Invalid mode '{mode_name}'. Must be one of: {list(self.mode_mapping.keys())}")
            return False
        
        self.parameters['Mode'] = mode_code
        print(f"Set mode to {mode_name} (code: {mode_code})")
        return True

    def get_parameter(self, param_name: str) -> int:
        """
        Get a parameter value
        
        Args:
            param_name: Name of the parameter
            
        Returns:
            int: Parameter value, or None if parameter doesn't exist
        """
        return self.parameters.get(param_name)

    def get_mode_name(self) -> str:
        """
        Get current mode as user-friendly name
        
        Returns:
            str: Mode name
        """
        mode_code = self.parameters['Mode']
        return self.mode_names.get(mode_code, f"Unknown ({mode_code})")

    def get_parameter_bytes(self) -> bytes:
        """
        Convert all parameters to 18-byte packet for serial transmission
        
        Returns:
            bytes: 18-byte packet ready to send to pacemaker
        """
        byte_array = bytearray(18)
        
        # Pack all parameters in order
        byte_array[0] = self.parameters['SYNC']
        byte_array[1] = self.parameters['FnCode']
        byte_array[2] = self.parameters['Mode']
        byte_array[3] = self.parameters['LRL']
        byte_array[4] = self.parameters['URL']
        byte_array[5] = self.parameters['MSR']
        byte_array[6] = self.parameters['ATR_AMP']
        byte_array[7] = self.parameters['VENT_AMP']
        byte_array[8] = self.parameters['ATR_PULSE_WIDTH']
        byte_array[9] = self.parameters['VENT_PULSE_WIDTH']
        byte_array[10] = self.parameters['ATR_SENS']
        byte_array[11] = self.parameters['VENT_SENS']
        byte_array[12] = self.parameters['VRP']
        byte_array[13] = self.parameters['ARP']
        byte_array[14] = self.parameters['ACTIVITY_THRESHOLD']
        byte_array[15] = self.parameters['REACTION_TIME']
        byte_array[16] = self.parameters['RESPONSE_FACTOR']
        byte_array[17] = self.parameters['RECOVERY_TIME']
        
        return bytes(byte_array)

    def set_echo_mode(self):
        """Set function code to echo mode (request pacemaker to echo current values)"""
        self.parameters['FnCode'] = 0x22
        print("Set to echo mode (0x22)")

    def set_parameter_mode(self):
        """Set function code to parameter mode (send parameters to pacemaker)"""
        self.parameters['FnCode'] = 0x55
        print("Set to parameter mode (0x55)")

    def print_parameters(self):
        """Print all current parameters in a formatted way"""
        print("\n" + "="*50)
        print("CURRENT PACEMAKER PARAMETERS")
        print("="*50)
        
        print(f"Mode: {self.get_mode_name()} (Code: {self.parameters['Mode']})")
        print(f"Function: {'Echo (0x22)' if self.parameters['FnCode'] == 0x22 else 'Set Parameters (0x55)'}")
        print()
        
        # Rate parameters
        print("RATES:")
        print(f"  Lower Rate Limit: {self.parameters['LRL']} ppm")
        print(f"  Upper Rate Limit: {self.parameters['URL']} ppm")
        print(f"  Maximum Sensor Rate: {self.parameters['MSR']} ppm")
        print()
        
        # Amplitude parameters (with converted values)
        print("AMPLITUDES:")
        print(f"  Atrial: {self.parameters['ATR_AMP']/10:.1f}V (raw: {self.parameters['ATR_AMP']})")
        print(f"  Ventricular: {self.parameters['VENT_AMP']/10:.1f}V (raw: {self.parameters['VENT_AMP']})")
        print()
        
        # Pulse Width parameters (with converted values)
        print("PULSE WIDTHS:")
        print(f"  Atrial: {self.parameters['ATR_PULSE_WIDTH']/10:.1f}ms (raw: {self.parameters['ATR_PULSE_WIDTH']})")
        print(f"  Ventricular: {self.parameters['VENT_PULSE_WIDTH']/10:.1f}ms (raw: {self.parameters['VENT_PULSE_WIDTH']})")
        print()
        
        # Sensitivity parameters (with converted values)
        print("SENSITIVITIES:")
        print(f"  Atrial: {self.parameters['ATR_SENS']/10:.1f}mV (raw: {self.parameters['ATR_SENS']})")
        print(f"  Ventricular: {self.parameters['VENT_SENS']/10:.1f}mV (raw: {self.parameters['VENT_SENS']})")
        print()
        
        # Refractory periods (with converted values)
        print("REFRACTORY PERIODS:")
        print(f"  ARP: {self.parameters['ARP']*10}ms (raw: {self.parameters['ARP']})")
        print(f"  VRP: {self.parameters['VRP']*10}ms (raw: {self.parameters['VRP']})")
        print()
        
        # Sensor parameters
        print("SENSOR PARAMETERS:")
        print(f"  Activity Threshold: {self.parameters['ACTIVITY_THRESHOLD']}")
        print(f"  Reaction Time: {self.parameters['REACTION_TIME']}s")
        print(f"  Response Factor: {self.parameters['RESPONSE_FACTOR']}")
        print(f"  Recovery Time: {self.parameters['RECOVERY_TIME']}min")
        
        print("="*50)

    def get_parameter_summary(self) -> dict:
        """
        Get a summary of parameters with converted values for display
        
        Returns:
            dict: Parameter summary with user-friendly values
        """
        return {
            'mode': self.get_mode_name(),
            'lrl': self.parameters['LRL'],
            'url': self.parameters['URL'],
            'msr': self.parameters['MSR'],
            'atrial_amp': self.parameters['ATR_AMP'] / 10,
            'ventricular_amp': self.parameters['VENT_AMP'] / 10,
            'atrial_pw': self.parameters['ATR_PULSE_WIDTH'] / 10,
            'ventricular_pw': self.parameters['VENT_PULSE_WIDTH'] / 10,
            'atrial_sens': self.parameters['ATR_SENS'] / 10,
            'ventricular_sens': self.parameters['VENT_SENS'] / 10,
            'arp': self.parameters['ARP'] * 10,
            'vrp': self.parameters['VRP'] * 10,
            'activity_threshold': self.parameters['ACTIVITY_THRESHOLD'],
            'reaction_time': self.parameters['REACTION_TIME'],
            'response_factor': self.parameters['RESPONSE_FACTOR'],
            'recovery_time': self.parameters['RECOVERY_TIME']
        }

# Create global instances
pacemaker_comm = PacemakerCommunicator()
pacemaker_params = PacemakerParameters()