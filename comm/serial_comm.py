# comm/serial_comm.py
import serial
import serial.tools.list_ports
import struct
import time


class PacemakerSerial:
    """Handles serial communication with FRDM-K64F pacemaker"""

    # Protocol constants
    SYNC_BYTE = 0x16

    # Commands
    CMD_ECHO = 0x22
    CMD_SET_PARAMS = 0x55

    def __init__(self):
        self.serial_port = None
        self.connected = False
        self.device_id = None

    # ---------------------------------------------------------
    # PORT FUNCTIONS
    # ---------------------------------------------------------
    def list_ports(self):
        ports = serial.tools.list_ports.comports()
        return [(p.device, p.description) for p in ports]

    def find_jlink_port(self):
        for dev, desc in self.list_ports():
            if desc.startswith("JLink"):
                return dev
        return None

    def connect(self, port, baudrate=115200, timeout=1):
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            time.sleep(1)
            self.connected =  self.serial_port and self.serial_port.is_open
            return self.connected, "Connected"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.serial_port = None
        self.connected = False

    # ---------------------------------------------------------
    # ECHO TEST
    # ---------------------------------------------------------
    def echo_test_parameters(self, mode, params):
        try:
            # Step 1: Program parameters
            print("  → Programming parameters...")
            prog_ok, prog_msg = self.program_parameters(mode, params)
            if not prog_ok:
                return False, f"Programming failed: {prog_msg}", {}
            # Step 2: Wait a bit for device to process
            time.sleep(0.3)
            self.serial_port.reset_input_buffer()
            time.sleep(0.1)
            # Step 3: Interrogate device
            print("  → Reading back parameters...")
            inter_ok, result = self.interrogate_device()
            if not inter_ok:
                return False, f"Interrogate failed: {result}", {}
            # Step 4: Compare parameters
            print("  → Comparing parameters...")
            differences = {}
            readback = result  # This is the dict returned from interrogate
            # Map your parameter names to what you sent
            comparisons = {
                'mode': (self._mode_to_code(mode), readback.get('mode')),
                'ARP': (int(params['ARP']), readback.get('ARP')),
                'VRP': (int(params['VRP']), readback.get('VRP')),
                'ATR_PULSE_AMP': (float(params['ATR_PULSE_AMP']), readback.get('ATR_PULSE_AMP')),
                'VENT_PULSE_AMP': (float(params['VENT_PULSE_AMP']), readback.get('VENT_PULSE_AMP')),
                'ATR_PULSE_WIDTH': (int(params['ATR_PULSE_WIDTH']), readback.get('ATR_PULSE_WIDTH')),
                'VENT_PULSE_WIDTH': (int(params['VENT_PULSE_WIDTH']), readback.get('VENT_PULSE_WIDTH')),
                'ATR_CMP_REF_PWM': (int(params['ATR_CMP_REF_PWM']), readback.get('ATR_CMP_REF_PWM')),
                'VENT_CMP_REF_PWM': (int(params['VENT_CMP_REF_PWM']), readback.get('VENT_CMP_REF_PWM')),
                'REACTION_TIME': (int(params['REACTION_TIME']), readback.get('REACTION_TIME')),
                'RECOVERY_TIME': (int(params['RECOVERY_TIME']), readback.get('RECOVERY_TIME')),
                'FIXED_AV_DELAY': (int(params['FIXED_AV_DELAY']), readback.get('FIXED_AV_DELAY')),
                'RESPONSE_FACTOR': (int(params['RESPONSE_FACTOR']), readback.get('RESPONSE_FACTOR')),
                'ACTIVITY_THRESHOLD': (int(params['ACTIVITY_THRESHOLD']), readback.get('ACTIVITY_THRESHOLD')),
                'LRL': (int(params['LRL']), readback.get('LRL')),
                'URL': (int(params['URL']), readback.get('URL')),
                'MSR': (int(params['MSR']), readback.get('MSR')),
            }
            # Check each parameter
            all_match = True
            for param_name, (sent, received) in comparisons.items():
                # For floats, use tolerance comparison
                if isinstance(sent, float):
                    tolerance = 0.01  # 1% tolerance for floating point
                    if abs(sent - received) > tolerance:
                        differences[param_name] = {'sent': sent, 'received': received}
                        all_match = False
                else:
                    if sent != received:
                        differences[param_name] = {'sent': sent, 'received': received}
                        all_match = False
            if all_match:
                return True, "All parameters match!", {}
            else:
                return False, f"Found {len(differences)} mismatches", differences
        except Exception as e:
            return False, f"Echo test error: {str(e)}", {}

    # ---------------------------------------------------------
    # SET PARAMETERS (Python → Simulink)
    # Payload = 31 bytes, mapped according to your final spec
    # Full packet = [0x16, 0x55] + payload = 34 bytes
    # ---------------------------------------------------------
    def _encode_parameters(self, mode, p):
        buf = bytearray()

        # RESPONSE_TYPE
        buf.append(p.get("response_type", 0))

        # MODE
        buf.append(self._mode_to_code(mode))

        # ARP
        buf += struct.pack('<H', int(p["ARP"]))
        # VRP
        buf += struct.pack('<H', int(p["VRP"]))

        # ATR_PULSE_AMP
        buf += struct.pack('<f', float(p["ATR_PULSE_AMP"]))
        # VENT_PULSE_AMP
        buf += struct.pack('<f', float(p["VENT_PULSE_AMP"]))

        # ATR_PULSE_WIDTH
        buf += struct.pack('<H', int(p["ATR_PULSE_WIDTH"]))
        # VENT_PULSE_WIDTH
        buf += struct.pack('<H', int(p["VENT_PULSE_WIDTH"]))

        # UNUSED byte (byte 21)
        buf.append(0)

        # ATR_CMP_REF_PWM
        buf.append(int(p["ATR_CMP_REF_PWM"]))
        # VENT_CMP_REF_PWM
        buf.append(int(p["VENT_CMP_REF_PWM"]))

        # REACTION_TIME
        buf += struct.pack('<H', int(p["REACTION_TIME"]))
        # RECOVERY_TIME
        buf += struct.pack('<H', int(p["RECOVERY_TIME"]))

        # UNUSED byte (byte 28)
        buf.append(0)

        # FIXED_AV_DELAY
        buf.append(int(p["FIXED_AV_DELAY"]))
        # RESPONSE_FACTOR
        buf.append(int(p["RESPONSE_FACTOR"]))
        # ACTIVITY_THRESHOLD
        buf.append(int(p["ACTIVITY_THRESHOLD"]))
        # LRL
        buf.append(int(p["LRL"]))
        # URL
        buf.append(int(p["URL"]))
        # MSR
        buf.append(int(p["MSR"]))

        # Ensure payload is exactly 32 bytes
        while len(buf) < 32:
            buf.append(0)

        return bytes(buf)

    def program_parameters(self, mode, parameters):
        try:
            payload = self._encode_parameters(mode, parameters)
            packet = bytearray([self.SYNC_BYTE, self.CMD_SET_PARAMS])  # Use bytearray
            packet.extend(payload)
            print("Packet length:", len(packet))
            print("Packet:", packet)
            self.serial_port.write(packet)
            self.serial_port.flush()

            # Just wait a moment for Simulink to process
            time.sleep(0.1)
    
            # resp = self.serial_port.read(88)
            # print("Data Length: ", len(resp))
            # print("Data: ", resp)
            # if len(resp) != 88:
            #     return False, "Incomplete data"
            return True, "Parameters accepted"
        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # INTERROGATE DEVICE (Simulink → Python, 88-byte always)
    # ---------------------------------------------------------
    def _decode_parameters(self, data):
        param = {}
        offset = 0
        param["response_type"] = data[offset]; offset += 1
        param["mode"] = data[offset]; offset += 1

        # ATR_PULSE_AMP
        param["ATR_PULSE_AMP"] = struct.unpack_from('<f', data, offset)[0]; offset += 4
        # VENT_PULSE_AMP
        param["VENT_PULSE_AMP"] = struct.unpack_from('<f', data, offset)[0]; offset += 4

        # ATR_WIDTH
        param["ATR_PULSE_WIDTH"] = struct.unpack_from('<H', data, offset)[0]; offset += 2
        # VENT_WIDTH
        param["VENT_PULSE_WIDTH"] = struct.unpack_from('<H', data, offset)[0]; offset += 2

        # LRL
        param["LRL"] = data[offset]; offset += 1

        # ARP
        param["ARP"] = struct.unpack_from('<H', data, offset)[0]; offset += 2
        # VRP
        param["VRP"] = struct.unpack_from('<H', data, offset)[0]; offset += 2

        # ATR_CMP_REF_PWM
        param["ATR_CMP_REF_PWM"] = data[offset]; offset += 1
        # VENT_CMP_REF_PWM
        param["VENT_CMP_REF_PWM"] = data[offset]; offset += 1

        # MSR
        param["MSR"] = data[offset]; offset += 1
        # RESPONSE_FACTOR
        param["RESPONSE_FACTOR"] = data[offset]; offset += 1

        # REACTION_TIME
        param["REACTION_TIME"] = struct.unpack_from('<H', data, offset)[0]; offset += 2
        # RECOVERY_TIME
        param["RECOVERY_TIME"] = struct.unpack_from('<H', data, offset)[0]; offset += 2

        # ACTIVITY_THRESHOLD
        param["ACTIVITY_THRESHOLD"] = data[offset]; offset += 1
        # URL
        param["URL"] = data[offset]; offset += 1
        # FIXED_AV_DELAY
        param["FIXED_AV_DELAY"] = data[offset]; offset += 1

        return param

    def interrogate_device(self):
        try:
            # CRITICAL: Clear any leftover data in buffer         
            self.serial_port.reset_input_buffer()         
            time.sleep(0.05)  # Brief pause after clearing

            # Request 88-byte parameter packet
            pkt = bytearray([self.SYNC_BYTE, self.CMD_ECHO])
            pkt.extend([0x00] * 32)
            print("Packet: ", pkt)
            self.serial_port.write(pkt)
            self.serial_port.flush()

            time.sleep(0.1)

            data = self.serial_port.read(88)
            print("Data Length: ", len(data))
            print("Data: ", data)
            if len(data) != 88:
                return False, "Incomplete data"
            return True, self._decode_parameters(data)
        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # READ ATR/VENT SIGNALS (EGM)
    # ---------------------------------------------------------
    def decode_signals(self, data88):
        if len(data88) != 88:
            raise ValueError(f"Expected 88-byte signal packet, got {len(data88)}")
        vent = struct.unpack('<11f', data88[:44])
        atr = struct.unpack('<11f', data88[44:88])
        return vent, atr

    def get_signals(self):
        try:
            # CRITICAL: Clear any leftover data in buffer         
            self.serial_port.reset_input_buffer()         
            time.sleep(0.05)  # Brief pause after clearing

            pkt = bytearray([self.SYNC_BYTE, self.CMD_ECHO])
            pkt.extend([0x00] * 32)
            self.serial_port.write(pkt)
            self.serial_port.flush()

            time.sleep(0.1)

            resp = self.serial_port.read(88)
            print("Signals: ", resp)
            if len(resp) != 88:
                return False, ([], [])
            vent, atr = self.decode_signals(resp)
            return True, (vent, atr)
        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # MODE CODE MAPPING
    # ---------------------------------------------------------
    def _mode_to_code(self, mode):
        mapping = {
            "AOO": 1, "VOO": 2, "AAI": 3, "VVI": 4,
            "AOOR": 5, "VOOR": 6, "AAIR": 7, "VVIR": 8
        }
        return mapping.get(mode, 0)