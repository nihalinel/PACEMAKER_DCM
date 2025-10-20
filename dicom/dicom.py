import os

import pydicom
from pydicom import dcmread

from .dicom_init import patient_info_init, bradycardia_param_init, temporary_param_init, lead_waveform_init, surface_ecg_init

# Initialization of DICOM files for an account's given patient
def init_dir(username, patientID):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # get base directory of your project
    PATIENT_DIR = os.path.join(BASE_DIR, "data", str(username), str(patientID)) # user-patient-specific folder in data
    os.makedirs(PATIENT_DIR, exist_ok=True) # create all directories if they don't exist

    # DICOM file paths
    paths = {
        "PT_INFO_DCM"     : os.path.join(PATIENT_DIR, "patient_info.dcm"),
        "BRADY_PARAM_DCM" : os.path.join(PATIENT_DIR, "brady_params_report.dcm"),
        "TEMP_PARAM_DCM"  : os.path.join(PATIENT_DIR, "temp_params_report.dcm"),
        "LEAD_WAVFRM_DCM" : os.path.join(PATIENT_DIR, "lead_waveform.dcm"),
        "SURFACE_ECG_DCM" : os.path.join(PATIENT_DIR, "surface_ecg.dcm"),
    }

    if not os.path.exists(paths["PT_INFO_DCM"]):
        patient_info_init(patientID, paths["PT_INFO_DCM"])
    if not os.path.exists(paths["BRADY_PARAM_DCM"]):
        bradycardia_param_init(patientID, paths["BRADY_PARAM_DCM"])
    if not os.path.exists(paths["TEMP_PARAM_DCM"]):
        temporary_param_init(patientID, paths["TEMP_PARAM_DCM"])
    if not os.path.exists(paths["LEAD_WAVFRM_DCM"]):
        lead_waveform_init(patientID, paths["LEAD_WAVFRM_DCM"])
    if not os.path.exists(paths["SURFACE_ECG_DCM"]):
        surface_ecg_init(patientID, paths["SURFACE_ECG_DCM"])
        
    return paths

# Fetch the parameter value of a specified mode and file
def get_parameter(filepath, mode, parameter, unit_flag=False):
    ds = dcmread(filepath)

    # validation
    if ds.Modality != "SR":
        raise TypeError("File is not a Basic Text SR")
    
    # traverse modes
    for item in ds.ContentSequence:
        concept = item.ConceptNameCodeSequence[0]
        if concept.CodeValue == f"BRADY_{mode}":

            # traverse parameters
            for subitem in item.ContentSequence:
                subconcept = subitem.ConceptNameCodeSequence[0]
                if subconcept.CodeMeaning == parameter:

                    # returns value as float (or as a string with units)
                    try:
                        value = subitem.MeasuredValueSequence[0].NumericValue
                        if unit_flag:
                            units = subitem.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeMeaning
                            return f"{value} {units}"
                        else:
                            return value
                    # in case it doesn't exsist, is empty or the DICOM tag is missing
                    except (AttributeError, IndexError, KeyError):
                        return 0.0
    return 0.0

# Write the parameter with a new value of a specified mode and file
def set_parameter(filepath, mode, parameter, value):
    ds = dcmread(filepath)

    # validation
    if ds.Modality != "SR":
        raise TypeError("File is not a Basic Text SR")
    
    # traverse modes
    for item in ds.ContentSequence:
        concept = item.ConceptNameCodeSequence[0]
        if concept.CodeValue == f"BRADY_{mode}":

            # traverse parameters
            for subitem in item.ContentSequence:
                subconcept = subitem.ConceptNameCodeSequence[0]
                if subconcept.CodeMeaning == parameter:

                    # updates numeric value
                    try:
                        subitem.MeasuredValueSequence[0].NumericValue = float(value)
                        ds.save_as(filepath)
                        return True
                    # in case it doesn't exsist, is empty or the DICOM tag is missing
                    except (AttributeError, IndexError, KeyError):
                        raise("Numberic Value tag missing or invalid structure")
    
    # if we get here, parameter or mode wasn't found
    raise ValueError(f"Parameter '{parameter}' not found under mode '{mode}'")