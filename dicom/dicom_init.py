import datetime
import tzlocal

from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid, UID, BasicTextSRStorage, GeneralECGWaveformStorage

PARAM_UNITS = {
    "Lower Rate Limit": "ppm",
    "Upper Rate Limit": "ppm",
    "Atrial Amplitude": "V",
    "Ventricular Amplitude": "V",
    "Atrial Pulse Width": "ms",
    "Ventricular Pulse Width": "ms",
    "Atrial Sensitivity": "mV",
    "Ventricular Sensitivity": "mV",
    "ARP": "ms",
    "VRP": "ms",
    "PVARP": "ms",
    "Hysteresis": "ppm",
    "Rate Smoothing": "%",
}

MODE_PARAMETERS = {
    "AAO": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
    "VOO": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
    "AAI": ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width",
            "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
    "VVI": ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width",
            "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"],
}

def param_sequence(mode):
    mode_item = Dataset()
    mode_item.ValueType = "CONTAINER"

    mode_concept = Dataset()
    mode_concept.CodeValue = f"BRADY_{mode}"
    mode_concept.CodingSchemeDesignator = "99EPIC"
    mode_concept.CodeMeaning = f"{mode} Bradycardia Parameters"
    mode_item.ConceptNameCodeSequence = [mode_concept]

    mode_item.ContentSequence = []
    for param_name in MODE_PARAMETERS[mode]:
        param_item = Dataset()
        param_item.ValueType = "NUM"

        concept = Dataset()
        concept.CodeValue = param_name.replace(" ","_").upper()
        concept.CodingSchemeDesignator = "99EPIC"
        concept.CodeMeaning = param_name

        units = Dataset()
        units.CodeValue = PARAM_UNITS.get(param_name, "")
        units.CodingSchemeDesignator = "UCUM"
        units.CodeMeaning = PARAM_UNITS.get(param_name, "")

        mv = Dataset()
        mv.NumericValue = 0
        mv.MeasurementUnitsCodeSequence = [units]
        
        param_item.ConceptNameCodeSequence = [concept]
        param_item.MeasuredValueSequence = [mv]
    
        mode_item.ContentSequence.append(param_item)
    return mode_item

def patient_info_init(patientID, DCM_FILE):
    # Required values for file meta information
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = BasicTextSRStorage # Basic Text SR SOP class
    file_meta.MediaStorageSOPInstanceUID = generate_uid() # random
    file_meta.ImplementationClassUID = UID("1.2.826.0.1.3680043.8.498.28725601842973686838759477676316050660") # constant
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = Dataset()
    ds.Modality = "SR"
    ds.is_little_endian = True
    ds.is_implicit_VR = False

    # Set creation date/time
    dt = datetime.datetime.now(tzlocal.get_localzone())
    ds.ContentDate = dt.strftime("%Y%m%d") # format YYYYMMDD
    ds.ContentTime = dt.strftime("%H%M%S") # format HHMMSS
    # Set modification date/time
    ds.InstanceCreationDate = ds.ContentDate
    ds.InstanceCreationTime = ds.ContentTime

    # Set shared default information
    ds.PatientName = "Test^Firstname"
    ds.PatientID = str(patientID)
    ds.StudyInstanceUID = '1.2.826.0.1.3680043.8.498.23100930851283483050097974441450083943'

    # Set unique default information
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesDescription = "Patient Information"
    ds.PatientBirthDate = "19990101"
    ds.PatientSex = "M"
    concept = Dataset()
    concept.CodeValue = "PACEMAKER_DEVICE_INFO"
    concept.CodingSchemeDesignator = "99EPIC"
    concept.CodeMeaning = "Pacemaker Device Info"
    ds.ConceptNameCodeSequence = [concept]
    ds.DeviceSerialNumber = ""
    ds.DeviceModelName = ""
    ds.DeviceManufacturer = ""

    # Add file meta information
    ds.file_meta = file_meta

    ds.save_as(DCM_FILE, enforce_file_format=True)

def bradycardia_param_init(patientID, DCM_FILE):
    # Required values for file meta information
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = BasicTextSRStorage # Basic Text SR SOP class
    file_meta.MediaStorageSOPInstanceUID = generate_uid() # random
    file_meta.ImplementationClassUID = UID("1.2.826.0.1.3680043.8.498.28725601842973686838759477676316050660") # constant
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = Dataset()
    ds.Modality = "SR"
    ds.is_little_endian = True
    ds.is_implicit_VR = False

    # Set creation date/time
    dt = datetime.datetime.now(tzlocal.get_localzone())
    ds.ContentDate = dt.strftime("%Y%m%d") # format YYYYMMDD
    ds.ContentTime = dt.strftime("%H%M%S") # format HHMMSS
    # Set modification date/time
    ds.InstanceCreationDate = ds.ContentDate
    ds.InstanceCreationTime = ds.ContentTime

    # Set shared default information
    ds.PatientName = "Test^Firstname"
    ds.PatientID = str(patientID)
    ds.StudyInstanceUID = '1.2.826.0.1.3680043.8.498.23100930851283483050097974441450083943'

    # Set unique default information
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesDescription = "Bradycardia Parameters"
    ds.DeviceSerialNumber = ""

    ds.ValueType = "CONTAINER"
    concept = Dataset()
    concept.CodeValue = "BRADY_PARAM"
    concept.CodingSchemeDesignator = "99EPIC"
    concept.CodeMeaning = "Bradycardia Parameters"
    ds.ConceptNameCodeSequence = [concept]

    ds.ContentSequence = []
    for mode in MODE_PARAMETERS:
        ds.ContentSequence.append(param_sequence(mode))

    # Add file meta information
    ds.file_meta = file_meta

    ds.save_as(DCM_FILE, enforce_file_format=True)

def temporary_param_init(patientID, DCM_FILE):
    # Required values for file meta information
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = BasicTextSRStorage # Basic Text SR SOP class
    file_meta.MediaStorageSOPInstanceUID = generate_uid() # random
    file_meta.ImplementationClassUID = UID("1.2.826.0.1.3680043.8.498.28725601842973686838759477676316050660") # constant
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = Dataset()
    ds.Modality = "SR"
    ds.is_little_endian = True
    ds.is_implicit_VR = False

    # Set creation date/time
    dt = datetime.datetime.now(tzlocal.get_localzone())
    ds.ContentDate = dt.strftime("%Y%m%d") # format YYYYMMDD
    ds.ContentTime = dt.strftime("%H%M%S") # format HHMMSS
    # Set modification date/time
    ds.InstanceCreationDate = ds.ContentDate
    ds.InstanceCreationTime = ds.ContentTime

    # Set shared default information
    ds.PatientName = "Test^Firstname"
    ds.PatientID = str(patientID)
    ds.StudyInstanceUID = '1.2.826.0.1.3680043.8.498.23100930851283483050097974441450083943'

    # Set unique default information
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesDescription = "Temporary Parameters"
    ds.DeviceSerialNumber = ""

    ds.ValueType = "CONTAINER"
    concept = Dataset()
    concept.CodeValue = "TEMP_PARAM"
    concept.CodingSchemeDesignator = "99EPIC"
    concept.CodeMeaning = "Temporary Parameters"
    ds.ConceptNameCodeSequence = [concept]  

    ds.ContentSequence = []
    for mode in MODE_PARAMETERS:
        ds.ContentSequence.append(param_sequence(mode))

    # Add file meta information
    ds.file_meta = file_meta

    ds.save_as(DCM_FILE, enforce_file_format=True)

def lead_waveform_init(patientID, DCM_FILE):
    # Required values for file meta information
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = GeneralECGWaveformStorage # ECG Waveform SOP class
    file_meta.MediaStorageSOPInstanceUID = generate_uid() # random
    file_meta.ImplementationClassUID = UID("1.2.826.0.1.3680043.8.498.28725601842973686838759477676316050660") # constant
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = Dataset()
    ds.Modality = "ECG"
    ds.is_little_endian = True
    ds.is_implicit_VR = False

    # Set creation date/time
    dt = datetime.datetime.now(tzlocal.get_localzone())
    # Set modification date/time
    ds.ContentDate = dt.strftime("%Y%m%d") # format YYYYMMDD
    ds.ContentTime = dt.strftime("%H%M%S") # format   HHMMSS
    ds.AcquisitionDateTime = f"{ds.ContentDate}{ds.ContentTime}"

    # Set shared default information
    ds.PatientName = "Test^Firstname"
    ds.PatientID = str(patientID)
    ds.StudyInstanceUID = '1.2.826.0.1.3680043.8.498.23100930851283483050097974441450083943'

    ds.WaveformSequence = []
    ecg_leads = ["Atrial", "Ventricular"]

    for lead_name in ecg_leads:
        # Waveform sequence
        seq = Dataset()
        seq.MultiplexGroupLabel = f"{lead_name} Lead"
        seq.NumberOfWaveformChannels = 1
        seq.NumberOfWaveformSamples = 0
        seq.SamplingFrequency = 1000.0
        seq.WaveformBitsAllocated = 16
        seq.WaveformBitsStored = 16
        seq.WaveformSampleInterpretation = "SS"
        seq.WaveformOriginality = "ORIGINAL"
        seq.WaveformData = b""
        seq.ChannelDefinitionSequence = []

        # Define channel
        ch = Dataset()
        ch.ChannelNumber = 1
        ch.ChannelLabel = lead_name
        ch.ChannelSampleSkew = 0
        ch.WaveformBitsStored = 16
        ch.ChannelSourceSequence = [Dataset()]
        ch.ChannelSourceSequence[0].CodeValue = lead_name
        ch.ChannelSourceSequence[0].CodingSchemeDesignator = "99LOCAL"
        ch.ChannelSourceSequence[0].CodeMeaning = f"Lead {lead_name}"
        ch.ChannelSensitivity = 1.0  # µV per bit (placeholder)
        ch.ChannelSensitivityUnitsSequence = [Dataset()]
        ch.ChannelSensitivityUnitsSequence[0].CodeValue = "V"
        ch.ChannelSensitivityUnitsSequence[0].CodingSchemeDesignator = "UCUM"
        ch.ChannelSensitivityUnitsSequence[0].CodeMeaning = "millivolt"
        ch.ChannelBaseline = 0

        seq.ChannelDefinitionSequence.append(ch)

        ds.WaveformSequence.append(seq)

    # Set unique default information
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesDescription = "Atrial/Ventricular Lead ECG"
    ds.WaveformOriginality = "ORIGINAL"

    # Add file meta information
    ds.file_meta = file_meta

    ds.save_as(DCM_FILE, enforce_file_format=True)

def surface_ecg_init(patientID, DCM_FILE):
    # Required values for file meta information
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = GeneralECGWaveformStorage # ECG Waveform SOP class
    file_meta.MediaStorageSOPInstanceUID = generate_uid() # random
    file_meta.ImplementationClassUID = UID("1.2.826.0.1.3680043.8.498.28725601842973686838759477676316050660") # constant
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    ds = Dataset()
    ds.Modality = "ECG"
    ds.is_little_endian = True
    ds.is_implicit_VR = False

    # Set creation date/time
    dt = datetime.datetime.now(tzlocal.get_localzone())
    # Set modification date/time
    ds.ContentDate = dt.strftime("%Y%m%d") # format YYYYMMDD
    ds.ContentTime = dt.strftime("%H%M%S") # format HHMMSS
    ds.AcquisitionDateTime = f"{ds.ContentDate}{ds.ContentTime}"

    # Set shared default information
    ds.PatientName = "Test^Firstname"
    ds.PatientID = str(patientID)
    ds.StudyInstanceUID = '1.2.826.0.1.3680043.8.498.23100930851283483050097974441450083943'

    # List of Standard ECG leads
    ecg_leads = ["I", "II", "III", "aVR", "aVL", "aVF",
                 "V1", "V2", "V3", "V4", "V5", "V6"]

    # Multiplex group for all 12 channels
    ecg_seq = Dataset()
    ecg_seq.MultiplexGroupLabel = "Surface Lead"
    ecg_seq.NumberOfWaveformChannels = len(ecg_leads)
    ecg_seq.NumberOfWaveformSamples = 0
    ecg_seq.SamplingFrequency = 500.0
    ecg_seq.WaveformBitsAllocated = 16
    ecg_seq.WaveformBitsStored = 16
    ecg_seq.WaveformSampleInterpretation = "SS"
    ecg_seq.WaveformData = b""  # placeholder

    # Set channel definition sequence
    ecg_seq.ChannelDefinitionSequence = []
    for i, lead_name in enumerate(ecg_leads, start=1):
        ch = Dataset()
        ch.ChannelNumber = i
        ch.ChannelLabel = lead_name
        ch.ChannelSampleSkew = 0
        ch.WaveformBitsStored = 16
        ch.ChannelSourceSequence = [Dataset()]
        ch.ChannelSourceSequence[0].CodeValue = lead_name
        ch.ChannelSourceSequence[0].CodingSchemeDesignator = "99LOCAL"
        ch.ChannelSourceSequence[0].CodeMeaning = f"Lead {lead_name}"
        ch.ChannelSensitivity = 1.0 # µV per bit (placeholder; changes based on ACD) (0.1526 for 16-bit ADC, 2.44 for 12-bit ADC)
        ch.ChannelSensitivityUnitsSequence = [Dataset()]
        ch.ChannelSensitivityUnitsSequence[0].CodeValue = "mV"
        ch.ChannelSensitivityUnitsSequence[0].CodingSchemeDesignator = "UCUM"
        ch.ChannelSensitivityUnitsSequence[0].CodeMeaning = "millivolt"
        ch.ChannelBaseline = 0
        ecg_seq.ChannelDefinitionSequence.append(ch)

    ds.WaveformSequence = [ecg_seq]

    # Set unique default information
    ds.SeriesInstanceUID = generate_uid()
    ds.SeriesDescription = "Surface ECG"
    ds.WaveformOriginality = "ORIGINAL"

    # Add file meta information
    ds.file_meta = file_meta

    ds.save_as(DCM_FILE, enforce_file_format=True)