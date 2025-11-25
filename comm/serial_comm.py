# comm/serial_comm.py
import serial
import serial.tools.list_ports
import struct
import time

class PacemakerSerial:
    """Handles serial communication with FRDM-K64F pacemaker"""
    
    # Communication protocol constants
    SYNC_BYTE = 0x16        # Start of transmission
    ACK_BYTE = 0x06         # Acknowledge
    NACK_BYTE = 0x15        # Not acknowledge
    
    # Command codes
    CMD_ECHO = 0x00         # Echo test
    CMD_SET_PARAMS = 0x55   # Program parameters
    CMD_GET_PARAMS = 0x56   # Interrogate device
    CMD_GET_EGM = 0x57      # Request electrogram data
    
    def __init__(self):
        self.serial_port = None
        self.connected = False
        self.device_id = None
        
    def list_ports(self):
        """List available COM ports"""
        ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in ports]
    
    def connect(self, port, baudrate=115200, timeout=2):
        """Connect to pacemaker via serial port"""
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )
            time.sleep(2)  # Wait for connection to stabilize
            
            # Test connection with echo
            if self.echo_test():
                self.connected = True
                self.device_id = self.get_device_id()
                return True, self.device_id
            else:
                self.serial_port.close()
                return False, "Echo test failed"
                
        except serial.SerialException as e:
            return False, str(e)
    
    def disconnect(self):
        """Disconnect from pacemaker"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connected = False
        self.device_id = None
    
    def echo_test(self):
        """Send echo command to verify connection"""
        try:
            # Send: SYNC + CMD_ECHO + test_data
            test_data = bytes([0x12, 0x34, 0x56, 0x78])
            packet = bytes([self.SYNC_BYTE, self.CMD_ECHO]) + test_data
            
            self.serial_port.write(packet)
            self.serial_port.flush()
            
            # Receive: SYNC + ACK + echoed_data
            response = self.serial_port.read(len(packet))
            
            return (len(response) == len(packet) and 
                    response[0] == self.SYNC_BYTE and
                    response[1] == self.ACK_BYTE and
                    response[2:] == test_data)
                    
        except Exception as e:
            print(f"Echo test error: {e}")
            return False
    
    def get_device_id(self):
        """Request device ID from pacemaker"""
        try:
            # Send device ID request
            packet = bytes([self.SYNC_BYTE, 0x58])  # CMD_GET_ID
            self.serial_port.write(packet)
            self.serial_port.flush()
            
            # Receive: SYNC + ACK + device_id (32 bits)
            response = self.serial_port.read(6)
            if len(response) == 6 and response[0] == self.SYNC_BYTE:
                device_id = struct.unpack('<I', response[2:6])[0]
                return f"PM-{device_id:08X}"
            
            return "Unknown"
            
        except Exception as e:
            print(f"Get device ID error: {e}")
            return "Unknown"
    
    def program_parameters(self, mode, parameters):
        """Send parameters to pacemaker"""
        try:
            # Encode parameters according to protocol
            param_bytes = self._encode_parameters(mode, parameters)
            
            # Build packet: SYNC + CMD + length + data + checksum
            packet = bytearray([self.SYNC_BYTE, self.CMD_SET_PARAMS, len(param_bytes)])
            packet.extend(param_bytes)
            checksum = self._calculate_checksum(packet[1:])
            packet.append(checksum)
            
            # Send packet
            self.serial_port.write(packet)
            self.serial_port.flush()
            
            # Wait for acknowledgment
            response = self.serial_port.read(2)
            
            if len(response) == 2 and response[0] == self.SYNC_BYTE:
                if response[1] == self.ACK_BYTE:
                    return True, "Parameters programmed successfully"
                else:
                    return False, "Device rejected parameters (NACK)"
            else:
                return False, "No response from device"
                
        except Exception as e:
            return False, f"Programming error: {str(e)}"
    
    def interrogate_device(self, mode):
        """Request current parameters from pacemaker"""
        try:
            # Send interrogate command for specific mode
            mode_code = self._mode_to_code(mode)
            packet = bytes([self.SYNC_BYTE, self.CMD_GET_PARAMS, mode_code])
            
            self.serial_port.write(packet)
            self.serial_port.flush()
            
            # Receive: SYNC + ACK + length + param_data
            header = self.serial_port.read(3)
            if len(header) == 3 and header[0] == self.SYNC_BYTE and header[1] == self.ACK_BYTE:
                length = header[2]
                param_data = self.serial_port.read(length)
                
                if len(param_data) == length:
                    parameters = self._decode_parameters(mode, param_data)
                    return True, parameters
            
            return False, "Failed to read parameters"
            
        except Exception as e:
            return False, f"Interrogation error: {str(e)}"
    
    def get_egram_data(self, channel, num_samples=500):
        """Request electrogram data from pacemaker"""
        try:
            # Send EGM request: SYNC + CMD + channel + num_samples
            packet = struct.pack('<BBHH', 
                                self.SYNC_BYTE, 
                                self.CMD_GET_EGM,
                                channel,  # 0=Atrial, 1=Ventricular, 2=Surface
                                num_samples)
            
            self.serial_port.write(packet)
            self.serial_port.flush()
            
            # Receive: SYNC + ACK + length + egm_data (16-bit samples)
            header = self.serial_port.read(4)
            if len(header) == 4 and header[0] == self.SYNC_BYTE and header[1] == self.ACK_BYTE:
                length = struct.unpack('<H', header[2:4])[0]
                raw_data = self.serial_port.read(length * 2)  # 2 bytes per sample
                
                if len(raw_data) == length * 2:
                    # Unpack 16-bit signed integers
                    samples = struct.unpack(f'<{length}h', raw_data)
                    # Convert to voltage (assuming 12-bit ADC, 3.3V reference)
                    voltage_samples = [s * 3.3 / 4096.0 for s in samples]
                    return True, voltage_samples
            
            return False, []
            
        except Exception as e:
            print(f"EGM request error: {e}")
            return False, []
    
    def _mode_to_code(self, mode):
        """Convert mode string to numeric code"""
        mode_map = {
            'AOO': 0x01, 'VOO': 0x02, 'AAI': 0x03, 'VVI': 0x04,
            'AOOR': 0x05, 'VOOR': 0x06, 'AAIR': 0x07, 'VVIR': 0x08
        }
        return mode_map.get(mode, 0x00)
    
    def _encode_parameters(self, mode, parameters):
        """Encode parameters into byte array according to protocol"""
        # Pack parameters as defined in srsVVI protocol
        # Example format: mode(1) + LRL(2) + URL(2) + amplitude(2) + width(2) + ...
        
        param_format = '<B'  # Mode byte
        param_values = [self._mode_to_code(mode)]
        
        # Add parameters based on mode (this is simplified - refer to actual protocol)
        param_format += 'HH'  # LRL, URL (uint16)
        param_values.extend([
            int(parameters.get('Lower Rate Limit', 60)),
            int(parameters.get('Upper Rate Limit', 120))
        ])
        
        param_format += 'HH'  # Amplitudes (uint16, scaled by 100)
        param_values.extend([
            int(parameters.get('Atrial Amplitude', 3.5) * 100),
            int(parameters.get('Ventricular Amplitude', 3.5) * 100)
        ])
        
        param_format += 'HH'  # Pulse widths (uint16, scaled by 100)
        param_values.extend([
            int(parameters.get('Atrial Pulse Width', 0.4) * 100),
            int(parameters.get('Ventricular Pulse Width', 0.4) * 100)
        ])
        
        # Add more parameters as needed...
        
        return struct.pack(param_format, *param_values)
    
    def _decode_parameters(self, mode, data):
        """Decode byte array into parameters dictionary"""
        # Unpack according to protocol
        values = struct.unpack('<BHHHHH', data[:13])  # Simplified example
        
        parameters = {
            'Lower Rate Limit': values[1],
            'Upper Rate Limit': values[2],
            'Atrial Amplitude': values[3] / 100.0,
            'Ventricular Amplitude': values[4] / 100.0,
            'Atrial Pulse Width': values[5] / 100.0,
            'Ventricular Pulse Width': values[6] / 100.0
        }
        
        return parameters
    
    def _calculate_checksum(self, data):
        """Calculate simple checksum (XOR of all bytes)"""
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum