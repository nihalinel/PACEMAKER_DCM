# gui/main_interface.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
from dicom.dicom import init_dir, get_parameter, set_parameter, get_ecg_waveform
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np

class DCMMainInterface:
    # Define parameter ranges for validation
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
        # "Activity Threshold": ["V-Low", "Low", "Med-Low", "Med", "Med-High", "High", "V-High"],
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
                 "Reaction Time", "Response Factor", "Recovery Time"],
        "VOOR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude", "Ventricular Pulse Width", 
                 "Reaction Time", "Response Factor", "Recovery Time"],
        "AAIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Atrial Amplitude", "Atrial Pulse Width",
                "Atrial Sensitivity", "ARP", "PVARP", "Hysteresis", "Rate Smoothing", 
                "Reaction Time", "Response Factor", "Recovery Time"],
        "VVIR": ["Lower Rate Limit", "Upper Rate Limit", "Maximum Sensor Rate", "Ventricular Amplitude", "Ventricular Pulse Width",
                "Ventricular Sensitivity", "VRP", "Hysteresis", "Rate Smoothing", 
                "Reaction Time", "Response Factor", "Recovery Time"],
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
        "Reaction Time": ("Reaction Time (s)", "s"),
        "Response Factor": ("Response Factor", ""),
        "Recovery Time": ("Recovery Time", "min"),
        #"Activity Threshold": ("Activity Threshold", ""),
    }
    
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
        
        # Initialize parameters
        self.create_main_interface()
        self.current_parameters = self.load_user_parameters()

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
        # Status bar showing connection and telemetry status (Req 4,5,6,7)
        status_frame = ttk.LabelFrame(parent, text="System Status", padding="5")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Connection indicator (Requirement 4)
        ttk.Label(status_frame, text="Connection:").grid(row=0, column=0, padx=5)
        self.connection_indicator = tk.Label(status_frame, text="●", font=("Arial", 16), fg="red")
        self.connection_indicator.grid(row=0, column=1)
        self.connection_text = ttk.Label(status_frame, text="Disconnected")
        self.connection_text.grid(row=0, column=2, padx=5)
        
        # Telemetry indicator (Requirements 5, 6)
        ttk.Label(status_frame, text="Telemetry:").grid(row=0, column=3, padx=(20, 5))
        self.telemetry_indicator = tk.Label(status_frame, text="●", font=("Arial", 16), fg="gray")
        self.telemetry_indicator.grid(row=0, column=4)
        self.telemetry_text = ttk.Label(status_frame, text="N/A")
        self.telemetry_text.grid(row=0, column=5, padx=5)
        
        # Device ID (Requirement 7)
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
        # Control buttons panel (Requirement 2)
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
        
        # Simulation controls (for testing requirements 5,6,7)
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
        # Parameter display area (Requirement 3)
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
            min_val, max_val = self.PARAMETER_RANGES[param_key]
            
            # Create label
            label = ttk.Label(self.scrollable_frame, text=label_text)
            label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            # Create entry
            entry = ttk.Entry(self.scrollable_frame, width=15)
            entry.grid(row=row, column=1, padx=5, pady=5)
            
            # Ensure current_parameters exists
            if not hasattr(self, "current_parameters") or self.current_parameters is None:
                self.current_parameters = {}

            # Get default value
            default_value = self.current_parameters.get(param_key, self.get_nominal_value(param_key))
            entry.insert(0, str(default_value))
            
            self.parameter_entries[param_key] = entry
            
            # Create range label
            range_label = ttk.Label(self.scrollable_frame, text=f"[{min_val}-{max_val}]", 
                                   foreground="gray")
            range_label.grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)
            
            # Store widgets for future reference
            self.parameter_widgets[param_key] = {
                'label': label,
                'entry': entry,
                'range': range_label
            }

    # Function to plot waveform
    def plot_waveform(self):
        if self.lead_type == "Atrial Lead" or self.lead_type == "Ventricular Lead":
            filepath = self.paths["LEAD_WAVFRM_DCM"]
        elif self.lead_type == "Surface Lead":
            filepath = self.paths["SURFACE_ECG_DCM"]
        else:
            return
        
        data = get_ecg_waveform(filepath, self.lead_type)
        print(f"{self.lead_type}: dtype={data.dtype}, min={np.min(data)}, max={np.max(data)}, len={len(data)}")
        
        # ensure data is numeric
        if data is None or len(data) == 0:
            self.ax.clear()
            self.ax.set_title(f"{self.lead_type} Waveform")
            self.ax.set_xlabel("Sample #")
            self.ax.set_ylabel("Amplitude")
            self.ax.text(0.5, 0.5, "No Data", transform=self.ax.transAxes,
                        ha='center', va='center', fontsize=12, color='gray')
            self.canvas.draw()
            return

        data = np.array(data, dtype=float)  # <-- Convert to numeric
        self.ax.clear()
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
        # Get nominal/default value for a parameter
        nominal_values = {
            "Lower Rate Limit": 60,
            "Upper Rate Limit": 120,
            "Maximum Sensor Rate": 120,
            "Atrial Amplitude": 3.5,
            "Atrial Pulse Width": 0.4,
            "Ventricular Amplitude": 3.5,
            "Ventricular Pulse Width": 0.4,
            "Atrial Sensitivity": 0.75,
            "Ventricular Sensitivity": 2.5,
            "VRP": 320,
            "ARP": 250,
            "PVARP": 250,
            "Hysteresis": 60,
            "Rate Smoothing": 0,
            "Reaction Time": 30,
            "Response Factor": 8,
            "Recovery Time": 5,
        }
        return nominal_values.get(param_key, 0)
    
    def on_mode_change(self, event=None):
        # Handle mode change event
        new_mode = self.mode_var.get()
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.current_mode_label.config(text=self.current_mode)
            self.display_mode_parameters()
            self.current_parameters = self.current_json_data.get(self.current_mode, {})
            self.display_mode_parameters()
            messagebox.showinfo("Mode Changed", f"Switched to {self.current_mode} mode")

    def on_lead_change(self, event=None):
        # Handle mode change event
        new_lead = self.lead_var.get()
        if new_lead != self.lead_type:
            self.lead_type = new_lead
            self.plot_waveform()
            messagebox.showinfo("Lead Changed", f"Switched to {self.lead_type} lead")

    def switch_parameter_set(self):
        # Switch between Bradycardia and Temporary parameters
        new_type = "TEMP" if self.current_param_type == "BRADY" else "BRADY"

        # confirm switch
        if not messagebox.askyesno("Switch Parameter Set",
                                   f"Switch from {self.current_param_type} to {new_type} parameters?\nUnsaved changes will be lost!"
        ):
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
        self.display_mode_parameters()
        self.current_parameters = self.current_json_data.get(self.current_mode, {})
        self.load_user_parameters()
        self.display_mode_parameters()
        messagebox.showinfo("Parameter Set Switched", f"Now editing {new_type} parameters.")
    
    def validate_parameter(self, param_key, value):
        # Validate a parameter value against its allowed range
        try:
            num_value = float(value)
            min_val, max_val = self.PARAMETER_RANGES[param_key]
            
            if num_value < min_val or num_value > max_val:
                return False, f"{self.PARAMETER_LABELS[param_key][0]} must be between {min_val} and {max_val}"
            
            return True, ""
        except ValueError:
            return False, f"{self.PARAMETER_LABELS[param_key][0]} must be a valid number"
    
    def validate_all_parameters(self):
        # Validate all current parameter values
        errors = []
        
        # First, validate ranges for all parameters
        for param_key, entry in self.parameter_entries.items():
            value = entry.get()
            is_valid, error_msg = self.validate_parameter(param_key, value)
            
            if not is_valid:
                errors.append(error_msg)
        
        # If no range errors, check inter-parameter constraints
        if not errors:
            try:
                # Check LRL vs URL constraint (only if both exist in current mode)
                if 'Lower Rate Limit' in self.parameter_entries and 'Upper Rate Limit' in self.parameter_entries:
                    lrl = float(self.parameter_entries['Lower Rate Limit'].get())
                    url = float(self.parameter_entries['Upper Rate Limit'].get())
                    
                    if lrl > url:
                        errors.append("Lower Rate Limit cannot be greater than Upper Rate Limit")
            except ValueError:
                pass  # Already caught by range validation
        
        return errors
    
    def create_action_buttons(self, parent):
        # Bottom action buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save Parameters", command=self.save_parameters, 
                   style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Revert Changes", command=self.revert_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Logout", command=self.logout).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Back to Patient Selection", command=self.back_to_patient_selection).pack(side=tk.LEFT, padx=5)
    
    # Device control methods
    
    def connect_device(self):
        # Connect to simulated device (Requirement 4)
        device_id = f"PM-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.connected_device = device_id
        self.connection_status = "Connected"
        
        self.connection_indicator.config(fg="green")
        self.connection_text.config(text="Connected")
        self.device_label.config(text=device_id)
        self.telemetry_indicator.config(fg="green")
        self.telemetry_text.config(text="OK")
        
        # Check if different device (Requirement 7)
        if self.last_device and self.last_device != device_id:
            self.device_warning.config(text="⚠ Different Device!")
            self.root.after(5000, lambda: self.device_warning.config(text=""))
        
        self.last_device = device_id
        messagebox.showinfo("Connected", f"Connected to device:\n{device_id}")
    
    def disconnect_device(self):
        # Disconnect from device
        self.connection_status = "Disconnected"
        self.connection_indicator.config(fg="red")
        self.connection_text.config(text="Disconnected")
        self.telemetry_indicator.config(fg="gray")
        self.telemetry_text.config(text="N/A")
        messagebox.showinfo("Disconnected", "Device disconnected")
    
    def simulate_telemetry_loss(self, reason):
        # Simulate telemetry loss (Requirements 5, 6)
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
        # Restore telemetry connection
        if self.connection_status == "Connected":
            self.telemetry_indicator.config(fg="green")
            self.telemetry_text.config(text="OK")
    
    def simulate_different_device(self):
        # Simulate detecting different device (Requirement 7)
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
        # Interrogate device for parameters
        if self.connection_status != "Connected":
            messagebox.showwarning("Warning", "Please connect to a device first")
            return
        messagebox.showinfo("Interrogate", "Device parameters retrieved successfully")
    
    def program_parameters(self):
        # Program parameters to device
        if self.connection_status != "Connected":
            messagebox.showwarning("Warning", "Please connect to a device first")
            return
        
        # Validate parameters before programming
        errors = self.validate_all_parameters()
        if errors:
            messagebox.showerror("Validation Error", 
                               "Cannot program parameters:\n\n" + "\n".join(errors))
            return
        
        if messagebox.askyesno("Program Device", 
                              f"Program these {self.current_mode} parameters to the connected device?\n\n"
                              "This will update the pacemaker settings."):
            # In Deliverable 2, this would send parameters via serial communication
            # For now, just simulate success
            messagebox.showinfo("Success", 
                              f"Parameters programmed successfully to device:\n{self.connected_device}\n\n"
                              "Mode: " + self.current_mode)
            
            # Auto-save to DCM after successful programming (good practice)
            self.save_parameters_silent()
    
    def reset_to_nominal(self):
        # Reset parameters to nominal values for current mode
        if messagebox.askyesno("Reset to Nominal", 
                              f"Reset all {self.current_mode} parameters to nominal values?"):
            for param_key in self.parameter_entries.keys():
                nominal_value = self.get_nominal_value(param_key)
                self.parameter_entries[param_key].delete(0, tk.END)
                self.parameter_entries[param_key].insert(0, str(nominal_value))
            messagebox.showinfo("Reset", f"Parameters reset to nominal values for {self.current_mode} mode")
    
    def revert_changes(self):
        # Revert parameters to last saved values
        if messagebox.askyesno("Revert Changes", "Discard all unsaved changes?"):
            for param_key, entry in self.parameter_entries.items():
                saved_value = self.current_parameters.get(param_key, self.get_nominal_value(param_key))
                entry.delete(0, tk.END)
                entry.insert(0, str(saved_value))
            messagebox.showinfo("Reverted", "Parameters restored to last saved values")
    
    def save_parameters(self):
        # Save parameters to DCM local storage
        errors = self.validate_all_parameters()
        
        if errors:
            messagebox.showerror("Validation Error", 
                               "Cannot save parameters:\n\n" + "\n".join(errors))
            return

        # Update current parameters
        for key, entry in self.parameter_entries.items():
            try:
                value = float(entry.get())
                self.current_parameters[key] = value
                self.current_json_data[self.current_mode][key] = value
                set_parameter(self.current_dcm_path, self.current_mode, key, value)
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for {key}")
                return

        # Save to file
        with open(self.json_path, 'w') as f:
            json.dump(self.brady_data, f, indent=4)
        messagebox.showinfo("Saved", f"Parameters saved to DCM storage for user: {self.username}")
    
    def save_parameters_silent(self):
        # Save parameters without showing success message (used after programming)     
        for key, entry in self.parameter_entries.items():
            try:
                value = float(entry.get())
                self.current_parameters[key] = value
                self.current_json_data[self.current_mode][key] = value
                set_parameter(self.current_dcm_path, self.current_mode, key, value)
            except ValueError:
                return

        with open(self.json_path, 'w') as f:
            json.dump(self.brady_data, f, indent=4)
    
    def logout(self):
        # Logout and return to login
        if messagebox.askyesno("Logout", "Logout and return to login screen?"):
            self.save_parameters_silent()
            # Remove JSON files
            for path in [self.brady_json_path, self.temp_json_path]:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception as e:
                    print(f"Could not remove path: {e}")

            # Restart login window
            self.root.destroy()
            import gui.login
            gui.login.main()

    def back_to_patient_selection(self):
        # Return to the patient selection window.
        if messagebox.askyesno("Return", "Return to patient selection? Unsaved changes will be lost."):
            self.save_parameters_silent()
            # Remove JSON files
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
    
    # Data persistence
    
    def load_user_parameters(self): 
        # Update title and status labels
        self.root.title(f"PACEMAKER DCM - {self.current_param_type} - User: {self.username}")
        # Load user-specific parameters 
        params = {}

        for param, entry in self.parameter_entries.items():
            entry.delete(0, tk.END)
            entry_value = self.current_json_data.get(self.current_mode, {}).get(param, self.get_nominal_value(param))
            entry.insert(0, entry_value)
            params[param] = entry_value

        return params
    
    # def save_user_parameters(self, param_file):
    #     # Save user-specific parameters
    #     # Create data directory if it doesn't exist
    #     os.makedirs(param_file, exist_ok=True)
        
    #     with open(param_file, 'w') as f:
    #         json.dump(self.current_parameters, f, indent=2)