# comm/serial_comm.py
import serial
import serial.tools.list_ports
import struct
import time


class PacemakerSerial:
    """Handles serial communication with FRDM-K64F pacemaker"""

    # Protocol constants
    SYNC_BYTE = 0x16
    ACK_BYTE = 0x06
    NACK_BYTE = 0x15

    # Commands
    CMD_ECHO = 0x22
    CMD_SET_PARAMS = 0x55
    CMD_GET_PARAMS = 0x56
    CMD_GET_EGM = 0x57

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
    def echo_test(self):
        try:
            packet = bytes([self.SYNC_BYTE, self.CMD_ECHO])
            self.serial_port.write(packet)
            self.serial_port.flush()
            resp = self.serial_port.read(2)
            return (
                len(resp) == 2
                and resp[0] == self.SYNC_BYTE
                and resp[1] == self.ACK_BYTE
            )
        except:
            return False

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

        # UNUSED byte (byte 18)
        buf.append(0)

        # ATR_CMP_REF_PWM
        buf.append(int(p["ATR_CMP_REF_PWM"]))
        # VENT_CMP_REF_PWM
        buf.append(int(p["VENT_CMP_REF_PWM"]))

        # REACTION_TIME
        buf += struct.pack('<H', int(p["REACTION_TIME"]))
        # RECOVERY_TIME
        buf += struct.pack('<H', int(p["RECOVERY_TIME"]))

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

        # Ensure payload is exactly 31 bytes
        while len(buf) < 31:
            buf.append(0)

        return bytes(buf)

    def program_parameters(self, mode, parameters):
        try:
            payload = self._encode_parameters(mode, parameters)
            packet = bytearray([self.SYNC_BYTE, self.CMD_SET_PARAMS])
            packet.extend(payload)
            self.serial_port.write(packet)
            self.serial_port.flush()

            resp = self.serial_port.read(2)
            if len(resp) == 2 and resp[0] == self.SYNC_BYTE and resp[1] == self.ACK_BYTE:
                return True, "Parameters accepted"
            return False, "Rejected or no response"
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

        # ARP
        param["ARP"] = struct.unpack_from('<H', data, offset)[0]; offset += 2
        # VRP
        param["VRP"] = struct.unpack_from('<H', data, offset)[0]; offset += 2

        # ATR_PULSE_AMP
        param["ATR_PULSE_AMP"] = struct.unpack_from('<f', data, offset)[0]; offset += 4
        # VENT_PULSE_AMP
        param["VENT_PULSE_AMP"] = struct.unpack_from('<f', data, offset)[0]; offset += 4

        # ATR_WIDTH
        param["ATR_PULSE_WIDTH"] = struct.unpack_from('<H', data, offset)[0]; offset += 2
        # VENT_WIDTH
        param["VENT_PULSE_WIDTH"] = struct.unpack_from('<H', data, offset)[0]; offset += 2

        # ATR_CMP_REF_PWM
        param["ATR_CMP_REF_PWM"] = data[offset]; offset += 1
        # VENT_CMP_REF_PWM
        param["VENT_CMP_REF_PWM"] = data[offset]; offset += 1

        # REACTION_TIME
        param["REACTION_TIME"] = struct.unpack_from('<H', data, offset)[0]; offset += 2
        # RECOVERY_TIME
        param["RECOVERY_TIME"] = struct.unpack_from('<H', data, offset)[0]; offset += 2

        # FIXED_AV_DELAY
        param["FIXED_AV_DELAY"] = data[offset]; offset += 1
        # RESPONSE_FACTOR
        param["RESPONSE_FACTOR"] = data[offset]; offset += 1
        # ACTIVITY_THRESHOLD
        param["ACTIVITY_THRESHOLD"] = data[offset]; offset += 1
        # LRL
        param["LRL"] = data[offset]; offset += 1
        # URL
        param["URL"] = data[offset]; offset += 1
        # MSR
        param["MSR"] = data[offset]; offset += 1

        return param

    def interrogate_device(self):
        try:
            # Request 88-byte parameter packet
            pkt = bytes([self.SYNC_BYTE, self.CMD_ECHO])
            self.serial_port.write(pkt)
            self.serial_port.flush()

            data = self.serial_port.read(88)
            print(len(data))
            if len(data) != 88:
                return False, "Incomplete data"
            return True, self._decode_parameters(data)
        except Exception as e:
            return False, str(e)

    # ---------------------------------------------------------
    # READ ATR/VENT SIGNALS (EGM)
    # ---------------------------------------------------------
    def decode_signals(self, data88):
        vent = struct.unpack('<11f', data88[:44])
        atr = struct.unpack('<11f', data88[44:88])
        return vent, atr

    def get_signals(self):
        pkt = bytes([self.SYNC_BYTE, self.CMD_GET_EGM])
        self.serial_port.write(pkt)
        self.serial_port.flush()
        resp = self.serial_port.read(90)
        if len(resp) < 90:
            return False, ([], [])
        if resp[0] != self.SYNC_BYTE or resp[1] != self.ACK_BYTE:
            return False, ([], [])
        return True, self.decode_signals(resp[2:90])

    # ---------------------------------------------------------
    # MODE CODE MAPPING
    # ---------------------------------------------------------
    def _mode_to_code(self, mode):
        mapping = {
            "AOO": 1, "VOO": 2, "AAI": 3, "VVI": 4,
            "AOOR": 5, "VOOR": 6, "AAIR": 7, "VVIR": 8
        }
        return mapping.get(mode, 0)