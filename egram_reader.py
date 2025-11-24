import serial
import struct
import time
from threading import Thread

class EgramReader:
    def __init__(self, serial_connection):
        self.ser = serial_connection  # Use existing connection
        self.running = False
        self.data_buffer = []
        
    def read_packet(self):
        """Read and decode one 8-byte packet"""
        if self.ser and self.ser.in_waiting >= 8:
            raw_bytes = self.ser.read(8)
            
            if len(raw_bytes) == 8:
                # Decode as signed 16-bit integers
                atrial = struct.unpack('<h', raw_bytes[0:2])[0]
                ventricular = struct.unpack('<h', raw_bytes[2:4])[0]
                unknown = struct.unpack('<h', raw_bytes[4:6])[0]
                marker = struct.unpack('<h', raw_bytes[6:8])[0]
                
                return {
                    'atrial': atrial,
                    'ventricular': ventricular,
                    'unknown': unknown,
                    'marker': marker,
                    'raw_bytes': raw_bytes
                }
        return None
        
    # ... rest of your methods (remove connect/disconnect since we use existing connection)
        
    def start_streaming(self, callback=None, num_samples=100):
        """Start streaming egram data"""
        def stream():
            samples_collected = 0
            self.running = True
            
            while self.running and samples_collected < num_samples:
                packet = self.read_packet()
                
                if packet:
                    self.data_buffer.append(packet)
                    samples_collected += 1
                    
                    # Call callback if provided
                    if callback:
                        callback(packet)
                    
                    # Optional: slow down if needed
                    time.sleep(0.01)
            
            self.running = False
            
        thread = Thread(target=stream, daemon=True)
        thread.start()
        
    def get_egram_data(self, num_samples=50):
        """Get egram data for display"""
        atrial_data = []
        ventricular_data = []
        
        self.start_streaming(num_samples=num_samples)
        
        # Wait for data collection
        time.sleep(2)
        
        for packet in self.data_buffer[-num_samples:]:  # Get latest samples
            atrial_data.append(packet['atrial'])
            ventricular_data.append(packet['ventricular'])
            
        return atrial_data, ventricular_data