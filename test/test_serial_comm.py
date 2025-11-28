"""
Test script for Pacemaker Serial Communication
Tests the serial protocol with GUI-style parameters and unit conversion
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comm"))
from serial_comm import PacemakerSerial


# =============================================================
# UNIT CONVERSION CONSTANTS (must match main_interface.py)
# =============================================================
PULSE_WIDTH_MULTIPLIER = 25    # GUI_ms * 25 = serial_value (0.4ms -> 10)
SENSITIVITY_PWM_BASE = 25      # PWM value at 0 mV
SENSITIVITY_PWM_SCALE = 23     # PWM increase per mV


def convert_gui_to_serial(gui_params):
    """
    Convert GUI-style parameters to serial protocol parameters.
    This mimics what main_interface.py does.
    """
    serial_params = {
        "response_type": gui_params.get("response_type", 1),
        "ARP": int(gui_params.get("ARP", 250)),
        "VRP": int(gui_params.get("VRP", 320)),
        "ATR_PULSE_AMP": float(gui_params.get("Atrial Amplitude", 3.5)),
        "VENT_PULSE_AMP": float(gui_params.get("Ventricular Amplitude", 3.5)),
        "ATR_PULSE_WIDTH": int(round(gui_params.get("Atrial Pulse Width", 0.4) * PULSE_WIDTH_MULTIPLIER)),
        "VENT_PULSE_WIDTH": int(round(gui_params.get("Ventricular Pulse Width", 0.4) * PULSE_WIDTH_MULTIPLIER)),
        "ATR_CMP_REF_PWM": int(SENSITIVITY_PWM_BASE + gui_params.get("Atrial Sensitivity", 2.5) * SENSITIVITY_PWM_SCALE),
        "VENT_CMP_REF_PWM": int(SENSITIVITY_PWM_BASE + gui_params.get("Ventricular Sensitivity", 2.5) * SENSITIVITY_PWM_SCALE),
        "REACTION_TIME": int(gui_params.get("Reaction Time", 30)),
        "RECOVERY_TIME": int(gui_params.get("Recovery Time", 5)),
        "FIXED_AV_DELAY": int(gui_params.get("FIXED_AV_DELAY", 150)),
        "RESPONSE_FACTOR": int(gui_params.get("Response Factor", 8)),
        "ACTIVITY_THRESHOLD": int(gui_params.get("ACTIVITY_THRESHOLD", 1)), 
        "LRL": int(gui_params.get("Lower Rate Limit", 60)),
        "URL": int(gui_params.get("Upper Rate Limit", 120)),
        "MSR": int(gui_params.get("Maximum Sensor Rate", 120)),
    }
    return serial_params


def convert_serial_to_gui(serial_params):
    """
    Convert serial protocol parameters back to GUI-style for verification.
    """
    gui_params = {
        "Lower Rate Limit": serial_params.get("LRL", 60),
        "Upper Rate Limit": serial_params.get("URL", 120),
        "Maximum Sensor Rate": serial_params.get("MSR", 120),
        "Atrial Amplitude": serial_params.get("ATR_PULSE_AMP", 3.5),
        "Ventricular Amplitude": serial_params.get("VENT_PULSE_AMP", 3.5),
        "Atrial Pulse Width": round(serial_params.get("ATR_PULSE_WIDTH", 10) / PULSE_WIDTH_MULTIPLIER, 2),
        "Ventricular Pulse Width": round(serial_params.get("VENT_PULSE_WIDTH", 10) / PULSE_WIDTH_MULTIPLIER, 2),
        "Atrial Sensitivity": round((serial_params.get("ATR_CMP_REF_PWM", 82) - SENSITIVITY_PWM_BASE) / SENSITIVITY_PWM_SCALE, 2),
        "Ventricular Sensitivity": round((serial_params.get("VENT_CMP_REF_PWM", 82) - SENSITIVITY_PWM_BASE) / SENSITIVITY_PWM_SCALE, 2),
        "ARP": serial_params.get("ARP", 250),
        "VRP": serial_params.get("VRP", 320),
        "Reaction Time": serial_params.get("REACTION_TIME", 30),
        "Recovery Time": serial_params.get("RECOVERY_TIME", 5),
        "Response Factor": serial_params.get("RESPONSE_FACTOR", 8),
    }
    return gui_params


def test_all():
    pm = PacemakerSerial()

    print("\n" + "="*60)
    print("PACEMAKER DCM SERIAL COMMUNICATION TEST")
    print("="*60)

    # =========================================================
    # 1. LIST PORTS
    # =========================================================
    print("\n=== 1. LIST AVAILABLE PORTS ===")
    ports = pm.list_ports()
    for dev, desc in ports:
        print(f"  {dev}: {desc}")
    
    if not ports:
        print("  No COM ports found!")
        return

    # =========================================================
    # 2. FIND JLINK PORT
    # =========================================================
    print("\n=== 2. FIND JLINK PORT ===")
    port = pm.find_jlink_port()
    if not port:
        print("  No JLink device found - using first available port")
        port = ports[0][0]
    print(f"  Using port: {port}")

    # =========================================================
    # 3. CONNECT
    # =========================================================
    print("\n=== 3. CONNECT TO DEVICE ===")
    ok, msg = pm.connect(port)
    print(f"  Connected: {ok}")
    print(f"  Message: {msg}")
    if not ok:
        return

    # =========================================================
    # 4. INITIAL INTERROGATE
    # =========================================================
    print("\n=== 4. INITIAL INTERROGATE ===")
    time.sleep(0.5)  # Give device time to stabilize
    ok, result = pm.interrogate_device()
    print(f"  Success: {ok}")
    if ok:
        print("  Raw serial parameters:")
        for key, val in result.items():
            print(f"    {key}: {val}")
        
        gui_equiv = convert_serial_to_gui(result)
        print("\n  Converted to GUI values:")
        for key, val in gui_equiv.items():
            print(f"    {key}: {val}")
    else:
        print(f"  Error: {result}")

    # =========================================================
    # 5. PROGRAM WITH GUI-STYLE PARAMETERS
    # =========================================================
    print("\n=== 5. PROGRAM WITH GUI-STYLE PARAMETERS ===")
    
    # Define parameters as a user would enter them in the GUI
    gui_params = {
        "response_type": 1,          # Echo mode
        "Lower Rate Limit": 70,      # ppm
        "Upper Rate Limit": 130,     # ppm
        "Maximum Sensor Rate": 140,  # ppm
        "Atrial Amplitude": 4.0,     # V
        "Ventricular Amplitude": 4.5,# V
        "Atrial Pulse Width": 0.5,   # ms (should become 13 in serial)
        "Ventricular Pulse Width": 0.6, # ms (should become 15 in serial)
        "Atrial Sensitivity": 3.0,   # mV (should become ~94 PWM)
        "Ventricular Sensitivity": 2.0, # mV (should become ~71 PWM)
        "ARP": 260,                  # ms
        "VRP": 330,                  # ms
        "Reaction Time": 35,         # s
        "Recovery Time": 8,          # min
        "Response Factor": 10,
        "FIXED_AV_DELAY": 160,
        "ACTIVITY_THRESHOLD": 4,
    }
    
    print("  GUI Parameters (as entered by user):")
    for key, val in gui_params.items():
        if key not in ["response_type", "FIXED_AV_DELAY", "ACTIVITY_THRESHOLD"]:
            print(f"    {key}: {val}")
    
    # Convert to serial format
    serial_params = convert_gui_to_serial(gui_params)
    
    print("\n  Converted Serial Parameters:")
    for key, val in serial_params.items():
        print(f"    {key}: {val}")
    
    # Send to device
    print("\n  Sending to device...")
    ok, msg = pm.program_parameters("AAIR", serial_params)
    print(f"  Success: {ok}")
    print(f"  Message: {msg}")

    # =========================================================
    # 6. VERIFY WITH ECHO TEST
    # =========================================================
    print("\n=== 6. VERIFY PARAMETERS (ECHO TEST) ===")
    time.sleep(0.5)  # Wait for device to process
    
    ok, result = pm.interrogate_device()
    print(f"  Interrogate success: {ok}")
    
    if ok:
        print("\n  Comparison (Sent vs Received):")
        print(f"  {'Parameter':<25} {'Sent':>10} {'Received':>10} {'Match':>8}")
        print("  " + "-"*55)
        
        all_match = True
        comparisons = [
            ("LRL", serial_params["LRL"], result.get("LRL")),
            ("URL", serial_params["URL"], result.get("URL")),
            ("MSR", serial_params["MSR"], result.get("MSR")),
            ("ATR_PULSE_AMP", serial_params["ATR_PULSE_AMP"], result.get("ATR_PULSE_AMP")),
            ("VENT_PULSE_AMP", serial_params["VENT_PULSE_AMP"], result.get("VENT_PULSE_AMP")),
            ("ATR_PULSE_WIDTH", serial_params["ATR_PULSE_WIDTH"], result.get("ATR_PULSE_WIDTH")),
            ("VENT_PULSE_WIDTH", serial_params["VENT_PULSE_WIDTH"], result.get("VENT_PULSE_WIDTH")),
            ("ATR_CMP_REF_PWM", serial_params["ATR_CMP_REF_PWM"], result.get("ATR_CMP_REF_PWM")),
            ("VENT_CMP_REF_PWM", serial_params["VENT_CMP_REF_PWM"], result.get("VENT_CMP_REF_PWM")),
            ("ARP", serial_params["ARP"], result.get("ARP")),
            ("VRP", serial_params["VRP"], result.get("VRP")),
            ("REACTION_TIME", serial_params["REACTION_TIME"], result.get("REACTION_TIME")),
            ("RECOVERY_TIME", serial_params["RECOVERY_TIME"], result.get("RECOVERY_TIME")),
            ("RESPONSE_FACTOR", serial_params["RESPONSE_FACTOR"], result.get("RESPONSE_FACTOR")),
        ]
        
        for name, sent, received in comparisons:
            if isinstance(sent, float):
                match = abs(sent - (received or 0)) < 0.01
            else:
                match = sent == received
            
            status = "✓" if match else "✗"
            if not match:
                all_match = False
            print(f"  {name:<25} {str(sent):>10} {str(received):>10} {status:>8}")
        
        print()
        if all_match:
            print("  ✓ ALL PARAMETERS VERIFIED SUCCESSFULLY!")
        else:
            print("  ✗ SOME PARAMETERS DID NOT MATCH")
    else:
        print(f"  Error: {result}")

    # =========================================================
    # 7. TEST SIGNAL MODE
    # =========================================================
    print("\n=== 7. TEST SIGNAL MODE ===")
    
    # Set response_type to 0 for signal mode
    signal_params = serial_params.copy()
    signal_params["response_type"] = 0
    
    print("  Setting response_type = 0 (signal mode)...")
    ok, msg = pm.program_parameters("AAIR", signal_params)
    print(f"  Program success: {ok}")
    
    time.sleep(0.3)
    
    print("  Reading signals...")
    ok, (vent, atr) = pm.get_signals()
    if ok:
        print(f"  Ventricular (11 floats): {vent[:5]}... (showing first 5)")
        print(f"  Atrial (11 floats):      {atr[:5]}... (showing first 5)")
    else:
        print(f"  Failed to read signals: {vent}")

    # =========================================================
    # 8. DISCONNECT
    # =========================================================
    print("\n=== 8. DISCONNECT ===")
    pm.disconnect()
    print("  Disconnected from device")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")


def test_conversion_only():
    """Test just the unit conversion without hardware"""
    print("\n=== UNIT CONVERSION TEST (No Hardware) ===\n")
    
    gui_params = {
        "Lower Rate Limit": 60,
        "Upper Rate Limit": 120,
        "Atrial Amplitude": 3.5,
        "Atrial Pulse Width": 0.4,  # ms
        "Atrial Sensitivity": 2.5,   # mV
        "ARP": 250,
    }
    
    print("GUI Parameters:")
    for k, v in gui_params.items():
        print(f"  {k}: {v}")
    
    serial = convert_gui_to_serial(gui_params)
    print("\nConverted to Serial:")
    print(f"  ATR_PULSE_WIDTH: {serial['ATR_PULSE_WIDTH']} (expected: 10)")
    print(f"  ATR_CMP_REF_PWM: {serial['ATR_CMP_REF_PWM']} (expected: ~82)")
    
    # Round-trip test
    gui_back = convert_serial_to_gui(serial)
    print("\nRound-trip back to GUI:")
    print(f"  Atrial Pulse Width: {gui_back['Atrial Pulse Width']} (original: 0.4)")
    print(f"  Atrial Sensitivity: {gui_back['Atrial Sensitivity']} (original: 2.5)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--conversion-only":
        test_conversion_only()
    else:
        test_all()