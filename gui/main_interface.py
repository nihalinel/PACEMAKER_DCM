# gui/main_interface.py
import tkinter as tk
from tkinter import ttk, messagebox
import time
import json
import os
from datetime import datetime
from dicom.dicom import init_dir, get_parameter, set_parameter, get_ecg_waveform
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from comm.serial_comm import PacemakerSerial

class ActivityThresholdWrapper:
    """
    Wrapper class that makes Activity Threshold dropdown behave like an Entry widget.
    This allows consistent interface for reading/writing parameter values.
    """
    def __init__(self, string_var, combobox):
        self.var = string_var
        self.combobox = combobox

 
    
    def get(self):
        """Return the current dropdown value (string like 'Med')"""
        return self.var.get()
    
    def delete(self, start, end):
        """Clear the value (for consistency with Entry interface)"""
        pass  # Combobox doesn't need this
    
    def insert(self, index, value):
        """Set the dropdown value"""
        if value in DCMMainInterface.ACTIVITY_THRESHOLD_OPTIONS:
            self.var.set(value)
        else:
            self.var.set("Med")  # Default fallback


class DCMMainInterface:
    
    # PARAMETER MAPPINGS (GUI <-> Serial Protocol)
    GUI_TO_SERIAL_MAPPING = {
        "Lower Rate Limit": "LRL",
        "Upper Rate Limit": "URL",
        "Maximum Sensor Rate": "MSR",
        "Atrial Amplitude": "ATR_PULSE_AMP",
        "Ventricular Amplitude": "VENT_PULSE_AMP",
        "Atrial Pulse Width": "ATR_PULSE_WIDTH",
        "Ventricular Pulse Width": "VENT_PULSE_WIDTH",
        "Atrial Sensitivity": "ATR_CMP_REF_PWM",
        "Ventricular Sensitivity": "VENT_CMP_REF_PWM",
        "ARP": "ARP",
        "VRP": "VRP",
        "Reaction Time": "REACTION_TIME",
        "Response Factor": "RESPONSE_FACTOR",
        "Recovery Time": "RECOVERY_TIME",
        "Activity Threshold": "ACTIVITY_THRESHOLD",
    }

    # Reverse mapping for interrogate (serial -> GUI)
    SERIAL_TO_GUI_MAPPING = {v: k for k, v in GUI_TO_SERIAL_MAPPING.items()}
    
    # Activity Threshold dropdown values
    # Maps display string to float value for serial protocol
    ACTIVITY_THRESHOLD_OPTIONS = ["V-Low", "Low", "Med-Low", "Med", "Med-High", "High", "V-High"]
    ACTIVITY_THRESHOLD_TO_FLOAT = {
        "V-Low": 1.05,
        "Low": 1.1,
        "Med-Low": 1.2,
        "Med": 1.3,
        "Med-High": 1.4,
        "High": 1.5,
        "V-High": 1.6
    }
    FLOAT_TO_ACTIVITY_THRESHOLD = {v: k for k, v in ACTIVITY_THRESHOLD_TO_FLOAT.items()}
    
    ''' UNIT CONVERSION CONSTANTS '''
    
    # Pulse Width
    PULSE_WIDTH_MULTIPLIER = 25  # GUI_ms * 25 = serial_value
    
    # Sensitivity to PWM conversion
    SENSITIVITY_PWM_BASE = 25      # PWM value at 0 mV
    SENSITIVITY_PWM_SCALE = 23     # PWM increase per mV (so 10mV -> 255)
    
    # PARAMETER RANGES AND DEFINITIONS
    PARAMETER_RANGES = {
        "Lower Rate Limit": (30, 175),
        "Upper Rate Limit": (50, 175),
        "Maximum Sensor Rate": (50, 175),
        "Atrial Amplitude": (0.0, 7.0),
        "Atrial Pulse Width": (0.05, 1.9),
        "Ventricular Amplitude": (0.0, 7.0),
        "Ventricular Pulse Width": (0.05, 1.9),
        "Atrial Sensitivity": (0.0, 10.0),
        "Ventricular Sensitivity": (0.0, 10.0),
        "VRP": (150, 500),
        "ARP": (150, 500),
        "PVARP": (150, 500),
        "Hysteresis": (30, 175),
        "Rate Smoothing": (0, 25),
        "Reaction Time": (10, 50),
        "Response Factor": (1, 16),
        "Recovery Time": (2, 16),
    }
    
    # Define mode-specific parameters
    MODE_PARAMETERS = {
        "AOO" : ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width"],
        "VOO" : ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width"],
        "AAI" : ["Lower Rate Limit", "Upper Rate Limit", "Atrial Amplitude", "Atrial Pulse Width",
                "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing"],
        "VVI" : ["Lower Rate Limit", "Upper Rate Limit", "Ventricular Amplitude", "Ventricular Pulse Width",
                "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing"],
        "AOOR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Atrial Amplitude", "Atrial Pulse Width", 
                 "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
        "VOOR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude", "Ventricular Pulse Width", 
                 "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
        "AAIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Atrial Amplitude", "Atrial Pulse Width",
                "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing", 
                "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
        "VVIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude", "Ventricular Pulse Width",
                "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing", 
                "Activity Threshold", "Reaction Time", "Response Factor", "Recovery Time"],
    }
    
    # Parameter display names
    PARAMETER_LABELS = {
        "Lower Rate Limit": ("Lower Rate Limit (ppm)", "ppm"),
        "Upper Rate Limit": ("Upper Rate Limit (ppm)", "ppm"),
        "Maximum Sensor Rate": ("Maximum Sensor Rate (ppm)", "ppm"),
        "Atrial Amplitude": ("Atrial Amplitude (V)", "V"),
        "Atrial Pulse Width": ("Atrial Pulse Width (ms)", "ms"),
        "Ventricular Amplitude": ("Ventricular Amplitude (V)", "V"),
        "Ventricular Pulse Width": ("Ventricular Pulse Width (ms)", "ms"),
        "Atrial Sensitivity": ("Atrial Sensitivity (mV)", "mV"),
        "Ventricular Sensitivity": ("Ventricular Sensitivity (mV)", "mV"),
        "VRP": ("VRP (ms)", "ms"),
        "ARP": ("ARP (ms)", "ms"),
        "PVARP": ("PVARP (ms)", "ms"),
        "Hysteresis": ("Hysteresis (ppm)", "ppm"),
        "Rate Smoothing": ("Rate Smoothing (%)", "%"),
        "Activity Threshold": ("Activity Threshold", ""),
        "Reaction Time": ("Reaction Time (s)", "s"),
        "Response Factor": ("Response Factor", ""),
        "Recovery Time": ("Recovery Time (min)", "min"),
    }
    
    ''' UNIT CONVERSION METHODS '''
    
    def _convert_gui_to_serial(self, gui_key, gui_value):
        """
        Convert GUI parameter values to serial protocol values.
        Handles unit conversions between human-readable GUI and device protocol.
        """
        if gui_key == "Activity Threshold":
            # gui_value is the string like "Med", convert to float
            if isinstance(gui_value, str):
                return self.ACTIVITY_THRESHOLD_TO_FLOAT.get(gui_value, 1.3)  # Default Med
            return float(gui_value)  # Already a float from interrogate
        
        if gui_key in ["Atrial Pulse Width", "Ventricular Pulse Width"]:
            # Convert ms to device units (e.g., 0.4ms -> 10)
            return int(round(gui_value * self.PULSE_WIDTH_MULTIPLIER))
        
        # Sensitivity: GUI is in mV (0-10), serial expects PWM (0-255)
        if gui_key in ["Atrial Sensitivity", "Ventricular Sensitivity"]:
            # Linear mapping from mV to PWM
            # Higher sensitivity (lower mV threshold) = higher PWM value
            pwm = int(self.SENSITIVITY_PWM_BASE + (gui_value * self.SENSITIVITY_PWM_SCALE))
            return max(0, min(255, pwm))  # Clamp to valid PWM range
        
        # Amplitude: GUI is in V, serial expects float - no conversion needed
        if gui_key in ["Atrial Amplitude", "Ventricular Amplitude"]:
            return float(gui_value)
        
        # Rate limits, refractory periods: direct integer pass-through
        if gui_key in ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate",
                       "ARP", "VRP", "Reaction Time", "Recovery Time", "Response Factor"]:
            return int(gui_value)
        
        # Default: return as-is
        return gui_value
    
    def _convert_serial_to_gui(self, serial_key, serial_value):
        """
        Convert serial protocol values back to GUI display values.
        Reverses the unit conversions for device readback.
        """
        # Activity Threshold: serial is float, GUI expects string
        if serial_key == "ACTIVITY_THRESHOLD":
            # Find closest matching threshold value
            if serial_value in self.FLOAT_TO_ACTIVITY_THRESHOLD:
                return self.FLOAT_TO_ACTIVITY_THRESHOLD[serial_value]
            # Find closest match if exact value not found
            closest = min(self.FLOAT_TO_ACTIVITY_THRESHOLD.keys(), 
                         key=lambda x: abs(x - serial_value))
            return self.FLOAT_TO_ACTIVITY_THRESHOLD[closest]
        
        # Pulse Width: serial is integer counts, GUI expects ms
        if serial_key in ["ATR_PULSE_WIDTH", "VENT_PULSE_WIDTH"]:
            # Convert device units back to ms
            return round(serial_value / self.PULSE_WIDTH_MULTIPLIER, 2)
        
        # Sensitivity: serial is PWM (0-255), GUI expects mV (0-10)
        if serial_key in ["ATR_CMP_REF_PWM", "VENT_CMP_REF_PWM"]:
            # Reverse linear mapping from PWM to mV
            mv = (serial_value - self.SENSITIVITY_PWM_BASE) / self.SENSITIVITY_PWM_SCALE
            return round(max(0, min(10, mv)), 2)  # Clamp to valid range
        
        # Amplitude: serial is float, GUI expects float - no conversion needed
        if serial_key in ["ATR_PULSE_AMP", "VENT_PULSE_AMP"]:
            return round(float(serial_value), 2)
        
        # Default: return as-is
        return serial_value
    
    def _get_serial_defaults(self):
        """
        Get default serial parameter values for parameters not shown in current mode.
        These match the Simulink INIT state defaults.
        """
        return {
            "response_type": 1,      # 1 = parameter echo mode, 0 = signal mode
            "ARP": 250,              # ms
            "VRP": 320,              # ms
            "ATR_PULSE_AMP": 3.5,    # V
            "VENT_PULSE_AMP": 3.5,   # V
            "ATR_PULSE_WIDTH": 10,   # device units (0.4ms * 25)
            "VENT_PULSE_WIDTH": 10,  # device units
            "ATR_CMP_REF_PWM": 90,   # PWM value
            "VENT_CMP_REF_PWM": 90,  # PWM value
            "REACTION_TIME": 30,     # seconds
            "RECOVERY_TIME": 5,      # minutes
            "FIXED_AV_DELAY": 150,   # ms
            "RESPONSE_FACTOR": 8,
            "ACTIVITY_THRESHOLD": 1.3,  # Med (float value)
            "LRL": 60,               # ppm
            "URL": 120,              # ppm
            "MSR": 120,              # ppm
        }
    
    ''' INITIALIZATION '''
    
    def __init__(self, root, username, patientID):
        self.root = root
        self.username = username
        self.patientID = patientID
        self.root.title(f"PACEMAKER DCM - User: {username}")
        self.root.geometry("900x700")

        # Initialize current mode
        self.current_mode = "AOO"
        self.current_param_type = "BRADY"
        self.lead_type = "Atrial Lead"
        
        # Get base directory
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Get patient directory and initalize JSON
        self.patient_dir = os.path.join(self.BASE_DIR, "data", self.username, self.patientID)
        os.makedirs(self.patient_dir, exist_ok=True)
        self.brady_json_path = os.path.join(self.patient_dir, "brady_params.json")
        self.temp_json_path = os.path.join(self.patient_dir, "temp_params.json")
        self.paths = init_dir(self.username, self.patientID)
        self.initialize_json_files()

        self.json_path = self.brady_json_path
        self.current_json_data = self.brady_data if self.current_param_type == "BRADY" else self.temp_data
        self.current_dcm_path = self.paths["BRADY_PARAM_DCM"] if self.current_param_type == "BRADY" else self.paths["TEMP_PARAM_DCM"]
        
        # Simulated device connection state
        self.connected_device = None
        self.connection_status = "Disconnected"
        self.last_device = None
        
        # Add serial communication
        self.pacemaker_serial = PacemakerSerial()
        
        # Flag to prevent multiple rapid button clicks
        self._programming_in_progress = False
        self._interrogating_in_progress = False
        
        # Initialize parameters
        self.create_main_interface()
        self.current_parameters = self.load_user_parameters()

        self.atrium_buffer = np.zeros(500)
        self.vent_buffer = np.zeros(500)
        
        # IMPORTANT — plot the buffer, NOT a static array
        self.atrium_curve = self.waveformPlot.plot(self.atrium_buffer, pen='r')
        self.vent_curve = self.waveformPlot.plot(self.vent_buffer, pen='b')

        self.streaming_enabled = False

        self.root.mainloop()

    def initialize_json_files(self):
        self.brady_data = self.load_or_create_json(self.brady_json_path, "BRADY_PARAM_DCM")
        self.temp_data  = self.load_or_create_json(self.temp_json_path, "TEMP_PARAM_DCM")

    def load_or_create_json(self, json_path, dicom_key):
        # Create or load JSON containing pacing parameters for all modes.
        if os.path.exists(json_path):
            # Load existing session
            with open(json_path, "r") as f:
               data = json.load(f)
            return data
            
        data = {}
        # Initialize from DICOM files
        for mode, params in self.MODE_PARAMETERS.items():
            data[mode] = {}
            for param in params:
                val = get_parameter(self.paths[dicom_key], mode, param)
                data[mode][param] = val if val is not None else ""
        
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        return data
    
    ''' GUI CREATION METHODS '''
    
    def create_main_interface(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Create all interface components
        self.create_status_bar(main_frame)
        self.create_mode_selector(main_frame)
        self.create_control_panel(main_frame)
        self.create_parameter_display(main_frame)
        self.create_ecg_display(main_frame)
        self.create_action_buttons(main_frame)
    
    def create_status_bar(self, parent):
        # Status bar showing connection and telemetry status
        status_frame = ttk.LabelFrame(parent, text="System Status", padding="5")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Connection indicator
        ttk.Label(status_frame, text="Connection:").grid(row=0, column=0, padx=5)
        self.connection_indicator = tk.Label(status_frame, text="●", font=("Arial", 16), fg="red")
        self.connection_indicator.grid(row=0, column=1)
        self.connection_text = ttk.Label(status_frame, text="Disconnected")
        self.connection_text.grid(row=0, column=2, padx=5)
        
        # Telemetry indicator
        ttk.Label(status_frame, text="Telemetry:").grid(row=0, column=3, padx=(20, 5))
        self.telemetry_indicator = tk.Label(status_frame, text="●", font=("Arial", 16), fg="gray")
        self.telemetry_indicator.grid(row=0, column=4)
        self.telemetry_text = ttk.Label(status_frame, text="N/A")
        self.telemetry_text.grid(row=0, column=5, padx=5)
        
        # Device ID
        ttk.Label(status_frame, text="Device ID:").grid(row=0, column=6, padx=(20, 5))
        self.device_label = ttk.Label(status_frame, text="None", foreground="blue")
        self.device_label.grid(row=0, column=7, padx=5)
        
        # Different device warning
        self.device_warning = ttk.Label(status_frame, text="", foreground="orange", font=("Arial", 9, "bold"))
        self.device_warning.grid(row=0, column=8, padx=10)
    
    def create_mode_selector(self, parent):
        # Mode selection dropdown
        mode_frame = ttk.LabelFrame(parent, text="Pacing Mode Selection", padding="5")
        mode_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(mode_frame, text="Mode:").grid(row=0, column=0, padx=5)
        
        self.mode_var = tk.StringVar(value=self.current_mode)
        mode_dropdown = ttk.Combobox(mode_frame, textvariable=self.mode_var, 
                                      values=list(self.MODE_PARAMETERS.keys()),
                                      state="readonly", width=15)
        mode_dropdown.grid(row=0, column=1, padx=5)
        mode_dropdown.bind("<<ComboboxSelected>>", self.on_mode_change)
        
        ttk.Label(mode_frame, text="Current Mode:", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=(20, 5))
        self.current_mode_label = ttk.Label(mode_frame, text=self.current_mode, 
                                           font=("Arial", 10, "bold"), foreground="blue")
        self.current_mode_label.grid(row=0, column=3, padx=5)

        ttk.Label(mode_frame, text="Current Set:", font=("Arial", 10, "bold")).grid(row=0, column=4, padx=(20, 5))
        self.current_set_label = ttk.Label(mode_frame, text=self.current_param_type, 
                                           font=("Arial", 10, "bold"), foreground="blue")
        self.current_set_label.grid(row=0, column=5, padx=5)
    
    def create_control_panel(self, parent):
        # Control buttons panel
        control_frame = ttk.LabelFrame(parent, text="Device Controls", padding="10")
        control_frame.grid(row=2, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        ttk.Label(control_frame, text="Connection:", font=("Arial", 9, "bold")).pack(pady=(5,2))
        ttk.Button(control_frame, text="Connect to Device", command=self.connect_device).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Disconnect", command=self.disconnect_device).pack(fill=tk.X, pady=2)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Label(control_frame, text="Device Operations:", font=("Arial", 9, "bold")).pack(pady=(5,2))
        ttk.Button(control_frame, text="Interrogate Device", command=self.interrogate_device).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Program Parameters", command=self.program_parameters).pack(fill=tk.X, pady=2)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Label(control_frame, text="Parameter Utilities:", font=("Arial", 9, "bold")).pack(pady=(5,2))
        ttk.Button(control_frame, text="Reset to Nominal", command=self.reset_to_nominal).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Switch Parameter Set", command=self.switch_parameter_set).pack(fill=tk.X, pady=2)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Simulation controls (for testing)
        ttk.Label(control_frame, text="Test Indicators:", font=("Arial", 9, "bold")).pack(pady=5)
        ttk.Button(control_frame, text="Simulate Out of Range", 
                   command=lambda: self.simulate_telemetry_loss("range")).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Simulate Noise", 
                   command=lambda: self.simulate_telemetry_loss("noise")).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Simulate Different Device", 
                   command=self.simulate_different_device).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Restore Telemetry", 
                   command=self.restore_telemetry).pack(fill=tk.X, pady=2)
    
    def create_parameter_display(self, parent):
        # Parameter display area
        param_frame = ttk.LabelFrame(parent, text="Programmable Parameters", padding="10")
        param_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create scrollable canvas
        canvas = tk.Canvas(param_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(param_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind("<Configure>", 
                             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.parameter_entries = {}
        self.parameter_widgets = {}
        
        # Display parameters for current mode
        self.display_mode_parameters()

    def set_ecg_waveform(self, atrium_waveform, vent_waveform):
        if self.streaming_enabled:
            # When streaming, store the LIVE 500-sample buffers
            self.stream_atrium = atrium_waveform
            self.stream_vent = vent_waveform
            return
    
        # When NOT streaming, store DICOM waveform
        self.ecg_atrial = atrium_waveform
        self.ecg_vent = vent_waveform

    def get_ecg_waveform(self):
        if self.streaming_enabled:
            return self.stream_atrium, self.stream_vent
        else:
            return self.ecg_atrial, self.ecg_vent
        
    def poll_streaming_data(self):
        atr11, vent11 = self.serial.get_signals()
    
        # Update rolling buffers
        self.atrium_buffer = np.concatenate((self.atrium_buffer[11:], atr11))
        self.vent_buffer   = np.concatenate((self.vent_buffer[11:], vent11))
    
        # Send 500-sample buffers into waveform system
        self.set_ecg_waveform(self.atrium_buffer, self.vent_buffer)

    def create_ecg_display(self, parent):
        # ECG waveform frame
        ecg_frame = ttk.LabelFrame(parent, text="ECG Waveform", padding="10")
        ecg_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10,0))

        # Dropdown to select lead
        self.lead_var = tk.StringVar(value=self.lead_type)
        lead_dropdown = ttk.Combobox(ecg_frame, textvariable=self.lead_var,
                                    values=["Atrial Lead", "Ventricular Lead", "Surface Lead"],
                                    state="readonly", width=25)
        lead_dropdown.pack(pady=(0,10))
        lead_dropdown.bind("<<ComboboxSelected>>", self.on_lead_change)

        # Matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(5,2))
        self.canvas = FigureCanvasTkAgg(self.fig, master=ecg_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.plot_waveform()
    
    def display_mode_parameters(self):
        # Display only parameters relevant to the current mode
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.parameter_entries.clear()
        self.parameter_widgets.clear()
        
        # Get parameters for current mode
        mode_params = self.MODE_PARAMETERS.get(self.current_mode, [])
        
        # Display each parameter
        for row, param_key in enumerate(mode_params):
            if param_key not in self.PARAMETER_LABELS:
                continue
                
            label_text, unit = self.PARAMETER_LABELS[param_key]
            
            # Create label
            label = ttk.Label(self.scrollable_frame, text=label_text)
            label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            # Ensure current_parameters exists
            if not hasattr(self, "current_parameters") or self.current_parameters is None:
                self.current_parameters = {}
            
            # for Activity Threshold dropdown
            if param_key == "Activity Threshold":
                # Get default value
                default_value = self.current_parameters.get(param_key, self.get_nominal_value(param_key))
                if default_value not in self.ACTIVITY_THRESHOLD_OPTIONS:
                    default_value = "Med"  # Fallback to nominal
                
                # Create StringVar and Combobox
                var = tk.StringVar(value=default_value)
                dropdown = ttk.Combobox(self.scrollable_frame, textvariable=var,
                                       values=self.ACTIVITY_THRESHOLD_OPTIONS,
                                       state="readonly", width=12)
                dropdown.grid(row=row, column=1, padx=5, pady=5)
                
                # Store reference (use a wrapper that mimics Entry interface)
                self.parameter_entries[param_key] = ActivityThresholdWrapper(var, dropdown)
                
                # Create range label
                range_label = ttk.Label(self.scrollable_frame, text="[V-Low...V-High]", 
                                       foreground="gray")
                range_label.grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
                
                # Store widgets
                self.parameter_widgets[param_key] = {
                    'label': label,
                    'entry': dropdown,
                    'range': range_label,
                    'var': var
                }
            else:
                # Regular numeric entry
                min_val, max_val = self.PARAMETER_RANGES[param_key]
                
                # Create entry
                entry = ttk.Entry(self.scrollable_frame, width=15)
                entry.grid(row=row, column=1, padx=5, pady=5)

                # Get default value
                default_value = self.current_parameters.get(param_key, self.get_nominal_value(param_key))
                entry.insert(0, str(default_value))
                
                self.parameter_entries[param_key] = entry
                
                # Create range label
                range_label = ttk.Label(self.scrollable_frame, text=f"[{min_val}-{max_val}]", 
                                       foreground="gray")
                range_label.grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
                
                # Store widgets
                self.parameter_widgets[param_key] = {
                    'label': label,
                    'entry': entry,
                    'range': range_label
                }

    def start_serial_stream(self):
        params = self.build_programming_params()
        params["response_type"] = 0
        self.serial.program_device(params)
    
        self.streaming_enabled = True
    
        # Timer for streaming
        self.stream_timer = QtCore.QTimer()
        self.stream_timer.timeout.connect(self.read_live_waveform)
        self.stream_timer.start(40)   # ~25 Hz or whatever you need

    def read_live_waveform(self):
        if not self.streaming_enabled:
            return
    
        atrium, vent = self.serial.get_signals()
    
        if atrium is None:
            return
    
        # Shift and append
        self.atrium_buffer = np.concatenate((self.atrium_buffer[11:], atrium))
        self.vent_buffer   = np.concatenate((self.vent_buffer[11:], vent))
    
        self.update_waveform_plot() 

    def start_streaming_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.poll_streaming_data)
        self.timer.start(50)     # 20 Hz update, adjust as needed

    def poll_streaming_data(self):
        if not self.streaming_enabled:
            return
    
        # Try to get new samples
        atrium_vals, vent_vals = serial_comm.get_signals()
    
        if atrium_vals is None:
            return
    
        # Append 11 samples, remove oldest 11
        self.atrium_buffer = np.concatenate([self.atrium_buffer[11:], atrium_vals])
        self.ventricle_buffer = np.concatenate([self.ventricle_buffer[11:], vent_vals])
    
        # Update plot
        self.update_waveform_plot()

    def update_waveform_plot(self):
        if self.waveform_dropdown.currentText() == "Atrial Lead":
            self.atrium_curve.setData(self.atrium_buffer)
        else:
            self.vent_curve.setData(self.vent_buffer)

    def plot_waveform(self):
        if self.lead_type == "Atrial Lead" or self.lead_type == "Ventricular Lead":
            filepath = self.paths["LEAD_WAVFRM_DCM"]
            data = get_ecg_waveform(filepath, self.lead_type)
        elif self.lead_type == "Surface Lead":
            # Load both atrial and ventricular waveforms
            atrial_path = self.paths["LEAD_WAVFRM_DCM"]
            ventricular_path = self.paths["LEAD_WAVFRM_DCM"]

            atrial_data = get_ecg_waveform(atrial_path, "Atrial Lead")
            ventricular_data = get_ecg_waveform(ventricular_path, "Ventricular Lead")

            # Ensure proper numpy types
            atrial_data = np.array(atrial_data, dtype=float)
            ventricular_data = np.array(ventricular_data, dtype=float)

            # Handle unequal lengths (truncate to min length)
            min_len = min(len(atrial_data), len(ventricular_data))
            atrial_data = atrial_data[:min_len]
            ventricular_data = ventricular_data[:min_len]

            # Plot both
            self.ax.clear()
            self.ax.plot(atrial_data, color='red', label='Atrial')
            self.ax.plot(ventricular_data, color='blue', label='Ventricular')

            self.ax.set_title("Surface Lead Waveform")
            self.ax.set_xlabel("Sample #")
            self.ax.set_ylabel("Amplitude")
            self.ax.legend()

            # Y-axis scaling
            ymin = min(np.min(atrial_data), np.min(ventricular_data))
            ymax = max(np.max(atrial_data), np.max(ventricular_data))
            if ymin == ymax:
                pad = 0.1 if ymin == 0 else abs(ymin) * 0.1
                ymin, ymax = ymin - pad, ymax + pad
            else:
                yrange = ymax - ymin
                ymin -= 0.1 * yrange
                ymax += 0.1 * yrange

            self.ax.set_ylim(ymin, ymax)
            self.ax.set_xlim(0, min_len)

            self.canvas.draw()
            return
        else:
            return

        # Existing logic for Atrial / Ventricular Lead only
        data = np.array(data, dtype=float)
        self.ax.clear()

        if self.lead_type == "Ventricular Lead":
            self.ax.plot(data, color='blue')
        else:
            self.ax.plot(data, color='red')

        self.ax.set_title(f"{self.lead_type} Waveform")
        self.ax.set_xlabel("Sample #")
        self.ax.set_ylabel("Amplitude")

        ymin, ymax = np.min(data), np.max(data)
        if ymin == ymax:
            pad = 0.1 if ymin == 0 else abs(ymin) * 0.1
            ymin, ymax = ymin - pad, ymax + pad
        else:
            yrange = ymax - ymin
            ymin -= 0.1 * yrange
            ymax += 0.1 * yrange

        self.ax.set_ylim(ymin, ymax)
        self.ax.set_xlim(0, len(data))

        self.canvas.draw()
    
    def get_nominal_value(self, param_key):
        
        # Get nominal/default value for a parameter (GUI units)
        nominal_values = {
            "Lower Rate Limit": 60,
            "Upper Rate Limit": 120,
            "Maximum Sensor Rate": 120,
            "Atrial Amplitude": 3.5,
            "Atrial Pulse Width": 0.4,
            "Ventricular Amplitude": 3.5,
            "Ventricular Pulse Width": 0.4,
            "Atrial Sensitivity": 2.5,
            "Ventricular Sensitivity": 2.5,
            "VRP": 320,
            "ARP": 250,
            "PVARP": 250,
            "Hysteresis": 60,
            "Rate Smoothing": 0,
            "Activity Threshold": "Med",
            "Reaction Time": 30,
            "Response Factor": 8,
            "Recovery Time": 5,
        }
        return nominal_values.get(param_key, 0)
    
    ''' EVENT HANDLERS '''
    
    def on_mode_change(self, event=None):
        new_mode = self.mode_var.get()
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.current_mode_label.config(text=self.current_mode)
            self.current_parameters = self.current_json_data.get(self.current_mode, {})
            self.display_mode_parameters()
            messagebox.showinfo("Mode Changed", f"Switched to {self.current_mode} mode")

    def on_lead_change(self, event=None):
        new_lead = self.lead_var.get()
        if new_lead != self.lead_type:
            self.lead_type = new_lead
            self.plot_waveform()
            messagebox.showinfo("Lead Changed", f"Switched to {self.lead_type} lead")

    def switch_parameter_set(self):
        new_type = "TEMP" if self.current_param_type == "BRADY" else "BRADY"

        if not messagebox.askyesno("Switch Parameter Set",
                                   f"Switch from {self.current_param_type} to {new_type} parameters?\nUnsaved changes will be lost!"):
            return
        
        self.save_parameters_silent()
        
        self.current_param_type = new_type
        if new_type == "BRADY":
            self.current_dcm_path = self.paths["BRADY_PARAM_DCM"]
            self.json_path = self.brady_json_path
            self.current_json_data = self.brady_data
        else:
            self.current_dcm_path = self.paths["TEMP_PARAM_DCM"]
            self.json_path = self.temp_json_path
            self.current_json_data = self.temp_data

        self.current_set_label.config(text=self.current_param_type)
        self.current_parameters = self.current_json_data.get(self.current_mode, {})
        self.load_user_parameters()
        self.display_mode_parameters()
        messagebox.showinfo("Parameter Set Switched", f"Now editing {new_type} parameters.")
    
    ''' VALIDATION '''
    
    def validate_parameter(self, param_key, value):
        # Activity Threshold dropdown
        if param_key == "Activity Threshold":
            if value in self.ACTIVITY_THRESHOLD_OPTIONS:
                return True, ""
            return False, f"Activity Threshold must be one of: {', '.join(self.ACTIVITY_THRESHOLD_OPTIONS)}"
        
        try:
            num_value = float(value)
            min_val, max_val = self.PARAMETER_RANGES[param_key]
            
            if num_value < min_val or num_value > max_val:
                return False, f"{self.PARAMETER_LABELS[param_key][0]} must be between {min_val} and {max_val}"
            
            return True, ""
        except ValueError:
            return False, f"{self.PARAMETER_LABELS[param_key][0]} must be a valid number"
    
    def validate_all_parameters(self):
        errors = []
        
        for param_key, entry in self.parameter_entries.items():
            value = entry.get()
            is_valid, error_msg = self.validate_parameter(param_key, value)
            
            if not is_valid:
                errors.append(error_msg)
        
        if not errors:
            try:
                if 'Lower Rate Limit' in self.parameter_entries and 'Upper Rate Limit' in self.parameter_entries:
                    lrl = float(self.parameter_entries['Lower Rate Limit'].get())
                    url = float(self.parameter_entries['Upper Rate Limit'].get())
                    
                    if lrl > url:
                        errors.append("Lower Rate Limit cannot be greater than Upper Rate Limit")
            except ValueError:
                pass
        
        return errors
    
    def create_action_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save Parameters", command=self.save_parameters, 
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Revert Changes", command=self.revert_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Logout", command=self.logout).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Back to Patient Selection", command=self.back_to_patient_selection).pack(side=tk.LEFT, padx=5)
    
    ''' DEVICE CONTROL METHODS '''
    
    def connect_device(self):
        """Connect to real pacemaker device via serial port"""
        ports = self.pacemaker_serial.list_ports()
        
        if not ports:
            messagebox.showerror("Error", "No COM ports available.\nEnsure pacemaker is connected via USB.")
            return
        
        # Create port selection dialog
        port_dialog = tk.Toplevel(self.root)
        port_dialog.title("Select COM Port")
        port_dialog.geometry("450x250")
        port_dialog.transient(self.root)
        port_dialog.grab_set()
        
        ttk.Label(port_dialog, text="Select pacemaker COM port:", 
                font=("Arial", 10, "bold")).pack(pady=10)
        
        port_var = tk.StringVar()
        port_list = ttk.Combobox(port_dialog, textvariable=port_var, 
                                values=[f"{p[0]} - {p[1]}" for p in ports],
                                state="readonly", width=50)
        port_list.pack(pady=10)
        if ports:
            port_list.current(0)
        
        status_label = ttk.Label(port_dialog, text="", foreground="blue")
        status_label.pack(pady=5)
    
        def do_connect():
            selected = port_var.get()
            if not selected:
                messagebox.showwarning("Warning", "Please select a COM port")
                return
                
            port_name = selected.split(' - ')[0]
            status_label.config(text="Connecting...", foreground="blue")
            port_dialog.update()
            
            success, result = self.pacemaker_serial.connect(port_name)
            
            if success:
                self.connected_device = result
                self.connection_status = "Connected"
                self.connection_indicator.config(fg="green")
                self.connection_text.config(text="Connected")
                self.device_label.config(text=result)
                self.telemetry_indicator.config(fg="green")
                self.telemetry_text.config(text="OK")
                
                if self.last_device and self.last_device != result:
                    self.device_warning.config(text="⚠ Different Device!")
                    self.root.after(5000, lambda: self.device_warning.config(text=""))
                
                self.last_device = result
                port_dialog.destroy()
                messagebox.showinfo("Connected", f"Connected to device:\n{result}\nPort: {port_name}")
            else:
                status_label.config(text=f"Connection failed: {result}", foreground="red")
                messagebox.showerror("Connection Failed", f"Failed to connect:\n{result}")
        
        button_frame = ttk.Frame(port_dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Connect", command=do_connect).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=port_dialog.destroy).pack(side=tk.LEFT, padx=5)
            
    def disconnect_device(self):
        """Disconnect from pacemaker"""
        self.pacemaker_serial.disconnect()
        self.connection_status = "Disconnected"
        self.connected_device = None
        self.connection_indicator.config(fg="red")
        self.connection_text.config(text="Disconnected")
        self.telemetry_indicator.config(fg="gray")
        self.telemetry_text.config(text="N/A")
        self.device_label.config(text="None")
        messagebox.showinfo("Disconnected", "Device disconnected")
    
    def simulate_telemetry_loss(self, reason):
        if self.connection_status != "Connected":
            messagebox.showwarning("Warning", "No device connected")
            return
        
        self.telemetry_indicator.config(fg="orange")
        if reason == "range":
            self.telemetry_text.config(text="Lost - Out of Range")
            messagebox.showwarning("Telemetry Loss", "Device out of range!")
        else:
            self.telemetry_text.config(text="Lost - Noise")
            messagebox.showwarning("Telemetry Loss", "Electromagnetic interference detected!")
    
    def restore_telemetry(self):
        if self.connection_status == "Connected":
            self.telemetry_indicator.config(fg="green")
            self.telemetry_text.config(text="OK")
    
    def simulate_different_device(self):
        if self.connection_status != "Connected":
            messagebox.showwarning("Warning", "No device connected")
            return
        
        old_device = self.connected_device
        new_device = f"PM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.connected_device = new_device
        self.device_label.config(text=new_device)
        self.device_warning.config(text="⚠ Different Device Detected!")
        
        messagebox.showwarning("Device Change", 
                              f"Different device detected!\n\nPrevious: {old_device}\nCurrent: {new_device}")
        self.root.after(5000, lambda: self.device_warning.config(text=""))
    
    def interrogate_device(self):
        """Read parameters from connected pacemaker with unit conversion"""

        self.streaming_enabled = False
        ok, data = self.pacemaker_serial.interrogate_device()
        self.streaming_enabled = True

        if not self.pacemaker_serial.connected:
            messagebox.showwarning("Warning", "Please connect to a device first")
            return
        
        
        # Prevent multiple rapid calls
        if self._interrogating_in_progress:
            return
        self._interrogating_in_progress = True
        
        # Show progress
        progress = tk.Toplevel(self.root)
        progress.title("Interrogating Device")
        progress.geometry("300x100")
        progress.transient(self.root)
        progress.grab_set()
        ttk.Label(progress, text="Reading parameters from device...", 
                font=("Arial", 10)).pack(pady=20)
        progress_bar = ttk.Progressbar(progress, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        progress.update()
        
        try:
            success, result = self.pacemaker_serial.interrogate_device()
            
            progress_bar.stop()
            progress.destroy()
            
            if success:
                # Map serial parameter names back to GUI names with unit conversion
                for serial_key, serial_value in result.items():
                    gui_key = self.SERIAL_TO_GUI_MAPPING.get(serial_key)
                    if gui_key and gui_key in self.parameter_entries:
                        # Convert serial value to GUI units
                        gui_value = self._convert_serial_to_gui(serial_key, serial_value)
                        
                        # Update GUI entry
                        self.parameter_entries[gui_key].delete(0, tk.END)
                        self.parameter_entries[gui_key].insert(0, str(gui_value))
                        
                        # Update internal data
                        self.current_parameters[gui_key] = gui_value
                        self.current_json_data[self.current_mode][gui_key] = gui_value
                
                messagebox.showinfo("Success", 
                                f"Device parameters retrieved successfully for {self.current_mode} mode")
            else:
                messagebox.showerror("Error", f"Failed to interrogate device:\n{result}")
        finally:
            self._interrogating_in_progress = False
    
    def program_parameters(self):
        """Program parameters to connected pacemaker with unit conversion"""

        self.streaming_enabled = False
        self.streaming_enabled = True

        if not self.pacemaker_serial.connected:
            messagebox.showwarning("Warning", "Please connect to a device first")
            return
        
        # Prevent multiple rapid calls
        if self._programming_in_progress:
            return
        self._programming_in_progress = True
        
        try:
            # Validate parameters before programming
            errors = self.validate_all_parameters()
            if errors:
                messagebox.showerror("Validation Error",
                                "Cannot program parameters:\n\n" + "\n".join(errors))
                return
            
            if not messagebox.askyesno("Program Device",
                                    f"Program these {self.current_mode} parameters to the connected device?\n\n"
                                    "This will update the pacemaker settings."):
                return
            
            # Start with default serial parameters
            serial_params = self._get_serial_defaults()
            
            # Override with actual GUI values, applying unit conversion
            for gui_key, entry in self.parameter_entries.items():
                try:
                    # Activity Threshold is a string dropdown, not a float
                    if gui_key == "Activity Threshold":
                        gui_value = entry.get()  # Returns string like "Med"
                    else:
                        gui_value = float(entry.get())
                    
                    serial_key = self.GUI_TO_SERIAL_MAPPING.get(gui_key, gui_key)
                    
                    # Convert GUI value to serial units
                    serial_value = self._convert_gui_to_serial(gui_key, gui_value)
                    serial_params[serial_key] = serial_value
                    
                except ValueError:
                    messagebox.showerror("Error", f"Invalid value for {gui_key}")
                    return
            
            # Debug: Print conversion results (only once)
            print(f"\n=== Programming {self.current_mode} ===")
            for gui_key, entry in self.parameter_entries.items():
                if gui_key == "Activity Threshold":
                    gui_val = entry.get()
                else:
                    gui_val = float(entry.get())
                serial_key = self.GUI_TO_SERIAL_MAPPING.get(gui_key, gui_key)
                serial_val = serial_params.get(serial_key)
                print(f"  {gui_key}: {gui_val} (GUI) -> {serial_key}: {serial_val} (Serial)")
            
            # Show progress
            progress = tk.Toplevel(self.root)
            progress.title("Programming Device")
            progress.geometry("300x100")
            progress.transient(self.root)
            progress.grab_set()
            ttk.Label(progress, text="Programming parameters to device...", 
                    font=("Arial", 10)).pack(pady=20)
            progress_bar = ttk.Progressbar(progress, mode='indeterminate')
            progress_bar.pack(pady=10, padx=20, fill=tk.X)
            progress_bar.start()
            progress.update()
            
            # Send to device
            success, message = self.pacemaker_serial.program_parameters(self.current_mode, serial_params)
            
            progress_bar.stop()
            progress.destroy()
            
            if success:
                time.sleep(0.3)
                messagebox.showinfo("Success",
                                f"{message}\n\nDevice: {self.connected_device}\nMode: {self.current_mode}")
                # Auto-save to DCM after successful programming
                self.save_parameters_silent()
            else:
                messagebox.showerror("Programming Failed", message)
        finally:
            self._programming_in_progress = False
    
    ''' PARAMETER MANAGEMENT '''
    
    def reset_to_nominal(self):
        if messagebox.askyesno("Reset to Nominal", 
                              f"Reset all {self.current_mode} parameters to nominal values?"):
            for param_key in self.parameter_entries.keys():
                nominal_value = self.get_nominal_value(param_key)
                self.parameter_entries[param_key].delete(0, tk.END)
                self.parameter_entries[param_key].insert(0, str(nominal_value))
            messagebox.showinfo("Reset", f"Parameters reset to nominal values for {self.current_mode} mode")
    
    def revert_changes(self):
        if messagebox.askyesno("Revert Changes", "Discard all unsaved changes?"):
            for param_key, entry in self.parameter_entries.items():
                saved_value = self.current_parameters.get(param_key, self.get_nominal_value(param_key))
                entry.delete(0, tk.END)
                entry.insert(0, str(saved_value))
            messagebox.showinfo("Reverted", "Parameters restored to last saved values")
    
    def save_parameters(self):
        errors = self.validate_all_parameters()
        
        if errors:
            messagebox.showerror("Validation Error", 
                               "Cannot save parameters:\n\n" + "\n".join(errors))
            return

        for key, entry in self.parameter_entries.items():
            try:
                # Activity Threshold is a string, not a float
                if key == "Activity Threshold":
                    value = entry.get()  # String like "Med"
                else:
                    value = float(entry.get())
                self.current_parameters[key] = value
                self.current_json_data[self.current_mode][key] = value
                set_parameter(self.current_dcm_path, self.current_mode, key, value)
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for {key}")
                return

        with open(self.json_path, 'w') as f:
            json.dump(self.current_json_data, f, indent=4)
        messagebox.showinfo("Saved", f"Parameters saved to DCM storage for user: {self.username}")
    
    def save_parameters_silent(self):
        for key, entry in self.parameter_entries.items():
            try:
                # Activity Threshold is a string, not a float
                if key == "Activity Threshold":
                    value = entry.get()  # String like "Med"
                else:
                    value = float(entry.get())
                self.current_parameters[key] = value
                self.current_json_data[self.current_mode][key] = value
                set_parameter(self.current_dcm_path, self.current_mode, key, value)
            except ValueError:
                return

        with open(self.json_path, 'w') as f:
            json.dump(self.current_json_data, f, indent=4)
    
    # =============================================================
    # SESSION MANAGEMENT
    # =============================================================
    
    def logout(self):
        if messagebox.askyesno("Logout", "Logout and return to login screen?"):
            self.save_parameters_silent()
            for path in [self.brady_json_path, self.temp_json_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    print(f"Could not remove path: {e}")

            self.root.destroy()
            import gui.login
            gui.login.main()

    def back_to_patient_selection(self):
        if messagebox.askyesno("Return", "Return to patient selection? Unsaved changes will be lost."):
            self.save_parameters_silent()
            for path in [self.brady_json_path, self.temp_json_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    print(f"Could not remove path: {e}")

            self.root.destroy()
            main_root = tk.Tk()
            from gui.patient_select import PatientSelectApp
            PatientSelectApp(main_root, self.username)
            main_root.mainloop()
    
    def load_user_parameters(self): 
        self.root.title(f"PACEMAKER DCM - {self.current_param_type} - User: {self.username}")
        params = {}

        for param, entry in self.parameter_entries.items():
            entry.delete(0, tk.END)
            entry_value = self.current_json_data.get(self.current_mode, {}).get(param, self.get_nominal_value(param))
            entry.insert(0, entry_value)
            params[param] = entry_value

        return params