import os
import pydicom
import random
from dicom.dicom import init_dir, get_parameter, set_parameter

# 1. Set test patient info
username = "test_user"
patientID = "12345"

# 2. Initialize DICOM files
paths = init_dir(username, patientID)

# 3. Verify that files exist
for key, path in paths.items():
    if os.path.exists(path):
        print(f"[OK] {key} exists at {path}")
    else:
        print(f"[ERROR] {key} is missing at {path}")

# 4. Load each DICOM and check basic fields
for key, path in paths.items():
    ds = pydicom.dcmread(path)
    print(f"\n=== {key} Summary ===")
    print(f"Patient ID: {ds.PatientID}")
    print(f"Patient Name: {ds.PatientName}")
    print(f"Modality: {ds.Modality}")
    print(f"Study UID: {ds.StudyInstanceUID}")
    if hasattr(ds, "WaveformSequence"):
        print(f"Waveform Channels: {len(ds.WaveformSequence)}")
        for seq in ds.WaveformSequence:
            print(f" - {seq.MultiplexGroupLabel}, Samples: {seq.NumberOfWaveformSamples}")
    if hasattr(ds, "ContentSequence"):
        print(f"Content Items: {len(ds.ContentSequence)}")

# 5. Load ST DICOM parameter field
test_paths = {
    "BRADY_PARAM_DCM" : paths["BRADY_PARAM_DCM"],
    "TEMP_PARAM_DCM"  : paths["TEMP_PARAM_DCM"],
    }

MODE_PARAMETERS = {
    "AAO": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
    "VOO": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
    "AAI": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width",
            "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
    "VVI": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width",
            "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"],
}

for key, path in test_paths.items():
    print(f"\n=== Reading {key} Parameters ===")
    for mode in MODE_PARAMETERS:
        print(f"{mode}")
        for parameter in MODE_PARAMETERS[mode]:
            print(f"{parameter}: {get_parameter(path, mode, parameter, True)}")

# 6. Set ST DICOM parameter field
for key, path in test_paths.items():
    print(f"\n=== Setting {key} Parameters ===")
    for mode in MODE_PARAMETERS:
        print(f"{mode}")
        for parameter in MODE_PARAMETERS[mode]:
            print(f"{parameter}: {set_parameter(path, mode, parameter, random.randrange(1, 500))}")

for key, path in test_paths.items():
    print(f"\n=== Reading NEW {key} Parameters ===")
    for mode in MODE_PARAMETERS:
        print(f"{mode}")
        for parameter in MODE_PARAMETERS[mode]:
            print(f"{parameter}: {get_parameter(path, mode, parameter, True)}")