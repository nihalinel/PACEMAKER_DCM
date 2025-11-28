import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comm"))
from serial_comm import PacemakerSerial

def test_all():
    pm = PacemakerSerial()

    print("\n=== 1. LIST PORTS ===")
    for dev, desc in pm.list_ports():
        print(dev, desc)

    print("\n=== 2. FIND JLINK PORT ===")
    port = pm.find_jlink_port()
    if not port:
        print("No JLink device found")
        return
    print("Using port:", port)

    print("\n=== 3. CONNECT ===")
    ok, msg = pm.connect(port)
    print("Connected:", ok, msg)
    if not ok:
        return
    
    print("\n=== 4. INTERROGATE DEVICE ===")
    ok, result = pm.interrogate_device()
    print("Interrogate:", ok)
    print(result)

    print("\n=== 5. PROGRAM PARAMETERS ===")
    params = {
        "response_type": 1,
        "ARP": 250,
        "VRP": 320,
        "ATR_PULSE_AMP": 3,
        "VENT_PULSE_AMP": 3,
        "ATR_PULSE_WIDTH": 10,
        "VENT_PULSE_WIDTH": 10,
        "ATR_CMP_REF_PWM": 62,
        "VENT_CMP_REF_PWM": 65,
        "REACTION_TIME": 30,
        "RECOVERY_TIME": 5,
        "FIXED_AV_DELAY": 250,
        "RESPONSE_FACTOR": 8,
        "ACTIVITY_THRESHOLD": 1,
        "LRL": 60,
        "URL": 120,
        "MSR": 150
    }
    ok, msg = pm.program_parameters("AAIR", params)
    print("Program parameters:", ok, msg)

    print("\n=== 6. ECHO TEST ===")
    success, message, diffs = pm.echo_test_parameters("AAIR", params)
    print(f"Echo Test: {success} {message}")
    if diffs:
        print("\nMismatches found:")
        for param, values in diffs.items():
            print(f"  {param}: sent={values['sent']}, received={values['received']}")
    else:
        print("✓ All parameters verified successfully!")

    print("\n=== 4. INTERROGATE DEVICE ===")
    ok, result = pm.interrogate_device()
    print("Interrogate:", ok)
    print(result)

    print("\n=== 7. READ ATR/VENT SIGNALS ===")
    params["response_type"] = 0
    ok, msg = pm.program_parameters("AAIR", params)
    ok, (vent, atr) = pm.get_signals()
    if ok:
        print("Ventricular:", vent)
        print("Atrial    :", atr)
    else:
        print("Failed to read signals")

    pm.disconnect()
    print("\n=== DONE ===")

if __name__ == "__main__":
    test_all()