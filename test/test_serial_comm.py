import os
import sys
# Ensure project root is on sys.path so tests can import serial_comm from a sibling directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
from serial_comm import PacemakerSerial

def test_connection():
    pm = PacemakerSerial()
    
    # List ports
    ports = pm.list_ports()
    print("Available ports:", ports)
    
    if ports:
        # Connect to first port
        success, result = pm.connect(ports[0][0])
        print(f"Connection: {success}, {result}")
        
        if success:
            # Test echo
            if pm.echo_test():
                print("Echo test: PASS")
            
            # Test programming
            params = {
                'Lower Rate Limit': 60,
                'Upper Rate Limit': 120,
                'Atrial Amplitude': 3.5,
                'Ventricular Amplitude': 3.5,
                'Atrial Pulse Width': 0.4,
                'Ventricular Pulse Width': 0.4
            }
            
            success, msg = pm.program_parameters('VVI', params)
            print(f"Programming: {success}, {msg}")
            
            # Disconnect
            pm.disconnect()

if __name__ == "__main__":
    test_connection()