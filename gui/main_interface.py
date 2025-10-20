# gui/main_interface.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

class DCMMainInterface:
    # Define parameter ranges for validation
    PARAMETER_RANGES = {
        "lower_rate_limit": (30, 175),
        "upper_rate_limit": (50, 175),
        "atrial_amplitude": (0.0, 7.0),
        "atrial_pulse_width": (0.05, 1.9),
        "ventricular_amplitude": (0.0, 7.0),
        "ventricular_pulse_width": (0.05, 1.9),
        "vrp": (150, 500),
        "arp": (150, 500),
        "pvarp": (150, 500),
        "hysteresis": (30, 175),
        "rate_smoothing": (0, 25),
        "atrial_sensitivity": (0.0, 10.0),
        "ventricular_sensitivity": (0.0, 10.0),
    }
    
    # Define mode-specific parameters
    MODE_PARAMETERS = {
        "AOO": ["lower_rate_limit", "upper_rate_limit", "atrial_amplitude", "atrial_pulse_width"],
        "VOO": ["lower_rate_limit", "upper_rate_limit", "ventricular_amplitude", "ventricular_pulse_width"],
        "AAI": ["lower_rate_limit", "upper_rate_limit", "atrial_amplitude", "atrial_pulse_width",
                "atrial_sensitivity", "arp", "pvarp", "hysteresis", "rate_smoothing"],
        "VVI": ["lower_rate_limit", "upper_rate_limit", "ventricular_amplitude", "ventricular_pulse_width",
                "ventricular_sensitivity", "vrp", "hysteresis", "rate_smoothing"],
    }
    
    # Parameter display names
    PARAMETER_LABELS = {
        "lower_rate_limit": ("Lower Rate Limit (ppm)", "ppm"),
        "upper_rate_limit": ("Upper Rate Limit (ppm)", "ppm"),
        "atrial_amplitude": ("Atrial Amplitude (V)", "V"),
        "atrial_pulse_width": ("Atrial Pulse Width (ms)", "ms"),
        "ventricular_amplitude": ("Ventricular Amplitude (V)", "V"),
        "ventricular_pulse_width": ("Ventricular Pulse Width (ms)", "ms"),
        "vrp": ("VRP (ms)", "ms"),
        "arp": ("ARP (ms)", "ms"),
        "pvarp": ("PVARP (ms)", "ms"),
        "hysteresis": ("Hysteresis (ppm)", "ppm"),
        "rate_smoothing": ("Rate Smoothing (%)", "%"),
        "atrial_sensitivity": ("Atrial Sensitivity (mV)", "mV"),
        "ventricular_sensitivity": ("Ventricular Sensitivity (mV)", "mV"),
    }
    
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.root.title(f"PACEMAKER DCM - User: {username}")
        self.root.geometry("900x700")
        
        # Get base directory
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Simulated device connection state
        self.connected_device = None
        self.connection_status = "Disconnected"
        self.last_device = None
        
        # Initialize current mode
        self.current_mode = "VVI"
        
        # Initialize parameters
        self.current_parameters = self.load_user_parameters()
        
        self.create_main_interface()
    
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
    
    def create_control_panel(self, parent):
        # Control buttons panel (Requirement 2)
        control_frame = ttk.LabelFrame(parent, text="Device Controls", padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        ttk.Button(control_frame, text="Connect to Device", command=self.connect_device).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Disconnect", command=self.disconnect_device).pack(fill=tk.X, pady=5)
        
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Interrogate Device", command=self.interrogate_device).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Program Parameters", command=self.program_parameters).pack(fill=tk.X, pady=5)
        ttk.Button(control_frame, text="Reset to Nominal", command=self.reset_to_nominal).pack(fill=tk.X, pady=5)
        
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
    
    def get_nominal_value(self, param_key):
        # Get nominal/default value for a parameter
        nominal_values = {
            "lower_rate_limit": 60,
            "upper_rate_limit": 120,
            "atrial_amplitude": 3.5,
            "atrial_pulse_width": 0.4,
            "ventricular_amplitude": 3.5,
            "ventricular_pulse_width": 0.4,
            "vrp": 320,
            "arp": 250,
            "pvarp": 250,
            "hysteresis": 60,
            "rate_smoothing": 0,
            "atrial_sensitivity": 0.75,
            "ventricular_sensitivity": 2.5,
        }
        return nominal_values.get(param_key, 0)
    
    def on_mode_change(self, event=None):
        # Handle mode change event
        new_mode = self.mode_var.get()
        if new_mode != self.current_mode:
            self.current_mode = new_mode
            self.current_mode_label.config(text=self.current_mode)
            self.display_mode_parameters()
            messagebox.showinfo("Mode Changed", f"Switched to {self.current_mode} mode")
    
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
        
        for param_key, entry in self.parameter_entries.items():
            value = entry.get()
            is_valid, error_msg = self.validate_parameter(param_key, value)
            
            if not is_valid:
                errors.append(error_msg)
        
        return errors
    
    def create_action_buttons(self, parent):
        # Bottom action buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Apply Changes", command=self.apply_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Parameters", command=self.save_parameters).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Logout", command=self.logout).pack(side=tk.LEFT, padx=5)
    
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
        
        if messagebox.askyesno("Program", "Program these parameters to the device?"):
            messagebox.showinfo("Success", "Parameters programmed successfully")
    
    def reset_to_nominal(self):
        # Reset parameters to nominal values for current mode
        for param_key in self.parameter_entries.keys():
            nominal_value = self.get_nominal_value(param_key)
            self.parameter_entries[param_key].delete(0, tk.END)
            self.parameter_entries[param_key].insert(0, str(nominal_value))
        messagebox.showinfo("Reset", f"Parameters reset to nominal values for {self.current_mode} mode")
    
    def apply_changes(self):
        # Apply parameter changes with validation
        errors = self.validate_all_parameters()
        
        if errors:
            messagebox.showerror("Validation Error", 
                               "Cannot apply changes:\n\n" + "\n".join(errors))
            return
        
        try:
            for key, entry in self.parameter_entries.items():
                self.current_parameters[key] = float(entry.get())
            messagebox.showinfo("Applied", "Parameters updated successfully")
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter value")
    
    def save_parameters(self):
        # Save parameters to file with validation
        errors = self.validate_all_parameters()
        
        if errors:
            messagebox.showerror("Validation Error", 
                               "Cannot save parameters:\n\n" + "\n".join(errors))
            return
        
        # Update current parameters
        for key, entry in self.parameter_entries.items():
            try:
                self.current_parameters[key] = float(entry.get())
            except ValueError:
                messagebox.showerror("Error", f"Invalid value for {key}")
                return
        
        # Save current mode
        self.current_parameters['mode'] = self.current_mode
        
        # Save to file
        self.save_user_parameters()
        messagebox.showinfo("Saved", "Parameters saved successfully")
    
    def logout(self):
        # Logout and return to login
        if messagebox.askyesno("Logout", "Logout and return to login screen?"):
            self.root.destroy()
            # Restart login window
            import login
            login.main()
    
    # Data persistence
    
    def load_user_parameters(self):
        # Load user-specific parameters
        param_file = os.path.join(self.BASE_DIR, f"data/params_{self.username}.json")
        try:
            with open(param_file, 'r') as f:
                params = json.load(f)
                # Load saved mode if available
                if 'mode' in params:
                    self.current_mode = params['mode']
                return params
        except FileNotFoundError:
            # Return default parameters
            return {
                "lower_rate_limit": 60,
                "upper_rate_limit": 120,
                "atrial_amplitude": 3.5,
                "atrial_pulse_width": 0.4,
                "ventricular_amplitude": 3.5,
                "ventricular_pulse_width": 0.4,
                "vrp": 320,
                "arp": 250,
                "pvarp": 250,
                "hysteresis": 60,
                "rate_smoothing": 0,
                "atrial_sensitivity": 0.75,
                "ventricular_sensitivity": 2.5,
                "mode": "VVI"
            }
    
    def save_user_parameters(self):
        # Save user-specific parameters
        # Create data directory if it doesn't exist
        data_dir = os.path.join(self.BASE_DIR, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        param_file = os.path.join(data_dir, f"params_{self.username}.json")
        with open(param_file, 'w') as f:
            json.dump(self.current_parameters, f, indent=2)