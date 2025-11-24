import serial
import time

def read_raw_bit_stream():
    PORT = 'COM5'
    BAUD = 115200
    
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        
        print("📡 Reading RAW BIT STREAM from COM5...")
        print("Press Ctrl+C to stop\n")
        print("BIT STREAM:")
        
        bit_count = 0
        line_bits = []
        
        while True:
            if ser.in_waiting > 0:
                # Read one byte
                raw_byte = ser.read(1)[0]
                
                # Convert to bits (LSB first - as transmitted)
                for i in range(8):
                    bit = (raw_byte >> i) & 1  # Get bit i (LSB first)
                    print(bit, end='')
                    line_bits.append(bit)
                    bit_count += 1
                    
                    # New line every 64 bits for readability
                    if bit_count % 64 == 0:
                        print()
                
                # Flush output
                import sys
                sys.stdout.flush()
            
            time.sleep(0.001)
            
    except KeyboardInterrupt:
        print(f"\n\nStopped. Total bits: {bit_count}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'ser' in locals():
            ser.close()

# EVEN RAWER - continuous stream with no formatting
def continuous_bit_stream():
    ser = serial.Serial('COM5', 115200, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    
    print("RAW CONTINUOUS BIT STREAM:")
    
    try:
        while True:
            if ser.in_waiting > 0:
                byte = ser.read(1)[0]
                for i in range(8):
                    bit = (byte >> i) & 1
                    print(bit, end='', flush=True)
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        ser.close()

# With timing visualization
def bit_stream_with_timing():
    ser = serial.Serial('COM5', 115200, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    
    print("BIT STREAM with byte markers:")
    print("[start]byte0[stop][start]byte1[stop]...")
    print()
    
    try:
        while True:
            if ser.in_waiting > 0:
                byte = ser.read(1)[0]
                print(f"0", end='')  # Start bit
                for i in range(8):
                    bit = (byte >> i) & 1  # LSB first
                    print(bit, end='')
                print("1", end='')  # Stop bit
                print(" ", end='', flush=True)  # Space between bytes
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        ser.close()
def data():
    ser = serial.Serial('COM5', 115200, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()


if __name__ == "__main__":
    print("Choose bit stream mode:")
    print("1. Raw bit stream (just 1s and 0s)")
    print("2. Continuous stream (no breaks)")
    print("3. With UART framing (start/stop bits)")
    
    choice = input("Enter 1, 2, or 3: ").strip()
    
    if choice == "1":
        read_raw_bit_stream()
    elif choice == "2":
        continuous_bit_stream()
    elif choice == "3":
        bit_stream_with_timing()
    else:
        print("Running raw bit stream...")
        read_raw_bit_stream()
