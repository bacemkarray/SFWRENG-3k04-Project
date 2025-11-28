import serial
import time
import keyboard  # You may need to install this with `pip install keyboard`

# ---------------------------
# Configuration
# ---------------------------
PORT = 'COM3'         # Replace with your pacemaker's COM port
BAUD = 115200         # Must match your Simulink serial settings
TIMEOUT = 0.1         # Serial read timeout in seconds

# ---------------------------
# Open serial port
# ---------------------------
ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
print("Serial port opened. Press 'e' to send an echo packet and 's' to send a set packet.")

# ---------------------------
# Build the echo packet
# ---------------------------
def build_packet_echo():
    return bytearray([
        0x16,       # SYNC / command code (example)
        0x22,       # FnCode (example, triggers ECHO_PARAM)

        # For the echo packet, the two bytes above must be those specific values
        # The rest of the values for the bytes doesn't matter since 
        # the pacemaker will just echo its current values back.
        
        1,          # MODE
        60,         # LRL
        120,        # URL
        120,        # MSR
        35,         # ATR_AMP
        35,         # VENT_AMP
        4,          # ATR_PULSE_WIDTH
        4,          # VENT_PULSE_WIDTH
        75,         # Atrial Sensitivity
        75,         # Ventricular Sensitivity
        32,         # VRP
        25,         # ARP
        10,         # Activity Threshold
        30,         # Reaction Time
        8,          # Response Factor
        5           # Recovery Time
    ])

# ---------------------------
# Build the set packet
# ---------------------------
def build_packet_set():
    return bytearray([
        0x16,       # SYNC / command code (example)
        0x55,       # FnCode (example, triggers ECHO_PARAM)
        5,          # MODE
        80,         # LRL
        120,        # URL
        120,        # MSR
        35,         # ATR_AMP
        35,         # VENT_AMP
        4,          # ATR_PULSE_WIDTH
        4,          # VENT_PULSE_WIDTH
        75,         # Atrial Sensitivity
        75,         # Ventricular Sensitivity
        32,         # VRP
        25,         # ARP
        10,         # Activity Threshold
        30,         # Reaction Time
        8,          # Response Factor
        5           # Recovery Time
    ])

def build_egram_echo():
    return bytearray([
        0x16,
        0x43
    ])

# ---------------------------
# Main loop
# ---------------------------
try:
    while True:
        # 1) Monitor incoming pacemaker data
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            if data:
                print("Received data:", data)
                print("Hex:", [hex(b) for b in data])

        # 2) Check for key press to send echo packet
        if keyboard.is_pressed('e'):  # Press 'e' to send
            packet = build_packet_echo()
            ser.write(packet)
            print("Echo packet sent to pacemaker!")
            time.sleep(0.3)  # small delay to avoid multiple sends on a single key press
        
        if keyboard.is_pressed('s'):  # Press 's' to send
            packet = build_packet_set()
            ser.write(packet)
            print("Set packet sent to pacemaker!")
            time.sleep(0.3)  # small delay to avoid multiple sends on a single key press

        
        if keyboard.is_pressed('a'):  # Press 'a' to send
            packet = build_egram_echo()
            ser.write(packet)
            print("egram packet sent to pacemaker!")
            time.sleep(0.3)  # small delay to avoid multiple sends on a single key press
        # Small delay to avoid CPU overuse
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nMonitoring stopped by user.")
    # Serial port remains open
