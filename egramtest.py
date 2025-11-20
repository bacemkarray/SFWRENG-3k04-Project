import serial
import time
import struct
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np

class RealEgramReader:
    def __init__(self, port='COM5', baudrate=115200, max_samples=200):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.max_samples = max_samples
        
        # Data buffers
        self.ventricular_data = deque([0] * max_samples, maxlen=max_samples)
        self.atrial_data = deque([0] * max_samples, maxlen=max_samples)
        self.timestamps = deque(range(-max_samples, 0), maxlen=max_samples)
        
        # Setup plot
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.setup_plots()
        
    def setup_plots(self):
        """Initialize the plots"""
        self.ax1.clear()
        self.ax2.clear()
        
        self.vent_line, = self.ax1.plot([], [], 'r-', linewidth=1, label='Ventricular')
        self.atr_line, = self.ax2.plot([], [], 'b-', linewidth=1, label='Atrial')
        
        self.ax1.set_title('Ventricular Egram - Real-time')
        self.ax1.set_ylabel('ADC Value')
        self.ax1.set_ylim(0, 70000)
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend()
        
        self.ax2.set_title('Atrial Egram - Real-time') 
        self.ax2.set_ylabel('ADC Value')
        self.ax2.set_xlabel('Time (samples)')
        self.ax2.set_ylim(0, 70000)
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend()
        
        plt.tight_layout()
    
    def update_plot(self, frame):
        """Update the plot with new data"""
        # Read data from serial
        if self.ser.in_waiting >= 4:
            data = self.ser.read(4)
            
            if len(data) == 4:
                # Interpret as 16-bit unsigned integers (based on your data)
                vent = int.from_bytes(data[0:2], 'little', signed=False)
                atr = int.from_bytes(data[2:4], 'little', signed=False)
                
                # Add new data
                self.ventricular_data.append(vent)
                self.atrial_data.append(atr)
                self.timestamps.append(self.timestamps[-1] + 1)
        
        # Update plot data
        self.vent_line.set_data(self.timestamps, self.ventricular_data)
        self.atr_line.set_data(self.timestamps, self.atrial_data)
        
        # Update x-axis limits
        self.ax1.set_xlim(self.timestamps[0], self.timestamps[-1])
        self.ax2.set_xlim(self.timestamps[0], self.timestamps[-1])
        
        return self.vent_line, self.atr_line
    
    def start(self):
        """Start the real-time plot"""
        print("Starting real-time egram display...")
        print("Close the plot window to stop")
        ani = animation.FuncAnimation(self.fig, self.update_plot, interval=50, blit=False)
        plt.show()
    
    def close(self):
        """Close serial connection"""
        self.ser.close()

def simple_egram_monitor(port='COM5', baudrate=115200, duration=30):
    """Simple monitor that prints the egram data with heart rate calculation"""
    ser = serial.Serial(port, baudrate, timeout=1)
    print("Simple Egram Monitor with Heart Rate Detection")
    print("V = Ventricular, A = Atrial")
    print("=" * 60)
    
    # For heart rate calculation
    last_vent_peak_time = None
    heart_rates = []
    
    try:
        start_time = time.time()
        sample_count = 0
        
        while time.time() - start_time < duration:
            if ser.in_waiting >= 4:
                data = ser.read(4)
                
                if len(data) == 4:
                    sample_count += 1
                    current_time = time.time()
                    
                    vent = int.from_bytes(data[0:2], 'little', signed=False)
                    atr = int.from_bytes(data[2:4], 'little', signed=False)
                    
                    # Detect ventricular peaks (QRS complex)
                    if vent > 60000:  # Threshold for detecting heartbeat
                        if last_vent_peak_time is not None:
                            # Calculate heart rate
                            rr_interval = current_time - last_vent_peak_time
                            heart_rate_bpm = 60 / rr_interval if rr_interval > 0 else 0
                            heart_rates.append(heart_rate_bpm)
                            
                            # Keep only last 10 rates for average
                            if len(heart_rates) > 10:
                                heart_rates.pop(0)
                            
                            avg_heart_rate = sum(heart_rates) / len(heart_rates)
                            
                            print(f"Sample {sample_count:4d}: ♥ Heartbeat! HR: {avg_heart_rate:5.1f} BPM")
                        else:
                            print(f"Sample {sample_count:4d}: ♥ First heartbeat detected")
                        
                        last_vent_peak_time = current_time
                    else:
                        # Normal sample
                        vent_bars = '█' * min(20, vent // 3000)
                        atr_bars = '█' * min(20, atr // 3000)
                        
                        print(f"Sample {sample_count:4d}: V: {vent:5d} [{vent_bars:20s}] A: {atr:5d} [{atr_bars:20s}]")
                
            time.sleep(0.01)  # 10ms delay
            
    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        ser.close()
        if heart_rates:
            avg_hr = sum(heart_rates) / len(heart_rates)
            print(f"\nAverage Heart Rate: {avg_hr:.1f} BPM")

def save_egram_data(port='COM5', baudrate=115200, duration=10, filename='egram_data.csv'):
    """Save egram data to CSV file for analysis"""
    import csv
    
    ser = serial.Serial(port, baudrate, timeout=1)
    print(f"Recording egram data for {duration} seconds...")
    
    data_points = []
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            if ser.in_waiting >= 4:
                data = ser.read(4)
                
                if len(data) == 4:
                    vent = int.from_bytes(data[0:2], 'little', signed=False)
                    atr = int.from_bytes(data[2:4], 'little', signed=False)
                    timestamp = time.time() - start_time
                    
                    data_points.append([timestamp, vent, atr])
            
            time.sleep(0.001)  # 1ms delay for high sampling rate
        
        # Save to CSV
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Time(s)', 'Ventricular', 'Atrial'])
            writer.writerows(data_points)
        
        print(f"Saved {len(data_points)} samples to {filename}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ser.close()

# Test the current data format
def test_data_format(port='COM5', baudrate=115200):
    """Test to confirm the data format"""
    ser = serial.Serial(port, baudrate, timeout=1)
    print("Testing data format...")
    
    samples_collected = 0
    try:
        while samples_collected < 10:
            if ser.in_waiting >= 4:
                data = ser.read(4)
                samples_collected += 1
                
                print(f"\nSample {samples_collected}:")
                print(f"Raw bytes: {data.hex()}")
                print(f"Bytes: {[f'0x{b:02x}' for b in data]}")
                
                # Test all possible interpretations
                vent_u = int.from_bytes(data[0:2], 'little', signed=False)
                atr_u = int.from_bytes(data[2:4], 'little', signed=False)
                
                vent_s = int.from_bytes(data[0:2], 'little', signed=True)
                atr_s = int.from_bytes(data[2:4], 'little', signed=True)
                
                print(f"Unsigned - V: {vent_u:5d}, A: {atr_u:5d}")
                print(f"Signed   - V: {vent_s:6d}, A: {atr_s:6d}")
                
    except KeyboardInterrupt:
        pass
    finally:
        ser.close()

if __name__ == "__main__":
    print("REAL EGRAM READER")
    print("Data format confirmed: 4 bytes (2V + 2A) as 16-bit unsigned")
    print("Choose an option:")
    print("1. Real-time plot (matplotlib)")
    print("2. Simple monitor with heart rate")
    print("3. Save data to CSV")
    print("4. Test data format")
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == "1":
        reader = RealEgramReader('COM5', 115200)
        try:
            reader.start()
        finally:
            reader.close()
    elif choice == "2":
        simple_egram_monitor('COM5', 115200, 30)
    elif choice == "3":
        save_egram_data('COM5', 115200, 10, 'heart_data.csv')
    elif choice == "4":
        test_data_format('COM5', 115200)
    else:
        print("Invalid choice")