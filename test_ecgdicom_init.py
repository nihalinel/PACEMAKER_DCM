import os
import pydicom
import wfdb
import numpy as np
import matplotlib.pyplot as plt

from dicom.dicom import init_dir, get_waveparam, set_waveparam

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

# 4. Load DICOM and check fields
wfdb_path = "C:/Users/bacTh/OneDrive - McMaster University/Documents/GitHub/PACEMAKER_DCM/data/test_user/12345/ECGdata/01"
record = wfdb.rdrecord(wfdb_path, physical=False)
fs = record.fs
signals = record.d_signal.astype(np.float32)
n_samples, n_channels = signals.shape
lead_labels = ["Atrial", "Ventricular"]

adc_gain = record.adc_gain
baseline = record.baseline

duration_sec = 12 # change to desired value (must be greater than 0)
n_samples = int(fs * duration_sec)
samples_d = signals[:n_samples, :]

ecg_path = paths["LEAD_WAVFRM_DCM"]
for i, label in enumerate(lead_labels):
    print(f"\n=== {label} Pre-Summary ===")
    print(f"SamplingFrequency: {get_waveparam(ecg_path, label, "SamplingFrequency")}")
    print(f"WaveformBitsAllocated: {get_waveparam(ecg_path, label, "WaveformBitsAllocated")}")
    print(f"NumberOfWaveformSamples {get_waveparam(ecg_path, label, "NumberOfWaveformSamples")}")
    print(f"ChannelSensitivity: {get_waveparam(ecg_path, label, "ChannelSensitivity")}")
    print(f"ChannelBaseline: {get_waveparam(ecg_path, label, "ChannelBaseline")}")
    
    set_waveparam(ecg_path, label, "SamplingFrequency", float(fs))
    set_waveparam(ecg_path, label, "WaveformBitsAllocated", 16)

    print(f"\n=== {label} Post-Summary ===")
    print(f"SamplingFrequency: {get_waveparam(ecg_path, label, "SamplingFrequency")}")
    print(f"WaveformBitsAllocated: {get_waveparam(ecg_path, label, "WaveformBitsAllocated")}")

    samples = samples_d[:, i].astype(np.int16)

    set_waveparam(ecg_path, label, "WaveformData", samples.tobytes())
    set_waveparam(ecg_path, label, "NumberOfWaveformSamples", len(samples))
    set_waveparam(ecg_path, label, "ChannelSensitivity", (1 / adc_gain[i]) * 1000)
    set_waveparam(ecg_path, label, "ChannelBaseline", baseline[i] / 1000)

    print(f"NumberOfWaveformSamples: {get_waveparam(ecg_path, label, "NumberOfWaveformSamples")}")
    print(f"ChannelSensitivity: {get_waveparam(ecg_path, label, "ChannelSensitivity")}")
    print(f"ChannelBaseline: {get_waveparam(ecg_path, label, "ChannelBaseline")}")

# 5. Visulaize Waveform Data for Verification
ds = pydicom.dcmread(ecg_path)
for i, wf_seq in enumerate(ds.WaveformSequence):
    label = wf_seq.MultiplexGroupLabel
    samples = wf_seq.NumberOfWaveformSamples
    fs = wf_seq.SamplingFrequency

    ch = wf_seq.ChannelDefinitionSequence[0]
    sensitivity = ch.ChannelSensitivity
    baseline = ch.ChannelBaseline

    adc_data = np.frombuffer(wf_seq.WaveformData, dtype=np.int16)

    voltage_mv = adc_data * sensitivity + baseline

    t = np.arange(samples) / fs

    plt.figure()
    plt.plot(t, voltage_mv, 'r-', linewidth=0.8)
    plt.title(f"{label} ({samples} samples @ {fs} Hz)")
    plt.xlabel("Time [s]")
    plt.ylabel("Amplitude (mV)")
    plt.grid(True)

plt.show()