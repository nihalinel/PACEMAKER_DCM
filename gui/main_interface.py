# gui/main_interface.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

class DCMMainInterface:
    def __init__(self, root, username):
        self.root = root
        self.username = username
        self.root.title(f"PACEMAKER DCM - User: {username}")
        self.root.geometry("900x700")
        
        # Get base directory (same as your auth.py logic)
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Simulated device connection state
        self.connected_device = None
        self.connection_status = "Disconnected"
        self.last_device = None
        
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
        main_frame.rowconfigure(1, weight=1)
        
        # Create all interface components
        self.create_status_bar(main_frame)
        self.create_control_panel(main_frame)
        self.create_parameter_display(main_frame)
        self.create_action_buttons(main_frame)
    
    def create_status_bar(self, parent):
        """Status bar showing connection and telemetry status (Req 4,5,6,7)"""
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
    
    def create_control_panel(self, parent):
        # Control buttons panel (Requirement 2)
        control_frame = ttk.LabelFrame(parent, text="Device Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
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
        """Parameter display area (Requirement 3)"""
        param_frame = ttk.LabelFrame(parent, text="Programmable Parameters", padding="10")
        param_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create scrollable canvas
        canvas = tk.Canvas(param_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(param_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", 
                             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        self.parameter_entries = {}
        
        # Parameters from deliverable spec
        parameters = [
            ("Lower Rate Limit (ppm)", "lower_rate_limit", 30, 175, 60),
            ("Upper Rate Limit (ppm)", "upper_rate_limit", 50, 175, 120),
            ("Atrial Amplitude (V)", "atrial_amplitude", 0.0, 7.0, 3.5),
            ("Atrial Pulse Width (ms)", "atrial_pulse_width", 0.05, 1.9, 0.4),
            ("Ventricular Amplitude (V)", "ventricular_amplitude", 0.0, 7.0, 3.5),
            ("Ventricular Pulse Width (ms)", "ventricular_pulse_width", 0.05, 1.9, 0.4),
            ("VRP (ms)", "vrp", 150, 500, 320),
            ("ARP (ms)", "arp", 150, 500, 250),
        ]
        
        for row, (label, key, min_val, max_val, default) in enumerate(parameters):
            ttk.Label(scrollable_frame, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
            
            entry = ttk.Entry(scrollable_frame, width=15)
            entry.grid(row=row, column=1, padx=5, pady=5)
            entry.insert(0, str(self.current_parameters.get(key, default)))
            self.parameter_entries[key] = entry
            
            ttk.Label(scrollable_frame, text=f"[{min_val}-{max_val}]", foreground="gray").grid(
                row=row, column=2, sticky=tk.W, padx=5, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_action_buttons(self, parent):
        # Bottom action buttons
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
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
        if messagebox.askyesno("Program", "Program these parameters to the device?"):
            messagebox.showinfo("Success", "Parameters programmed successfully")
    
    def reset_to_nominal(self):
        # Reset parameters to nominal values
        nominal = {
            "lower_rate_limit": 60, "upper_rate_limit": 120,
            "atrial_amplitude": 3.5, "atrial_pulse_width": 0.4,
            "ventricular_amplitude": 3.5, "ventricular_pulse_width": 0.4,
            "vrp": 320, "arp": 250
        }
        for key, value in nominal.items():
            self.parameter_entries[key].delete(0, tk.END)
            self.parameter_entries[key].insert(0, str(value))
        messagebox.showinfo("Reset", "Parameters reset to nominal values")
    
    def apply_changes(self):
        # Apply parameter changes
        try:
            for key, entry in self.parameter_entries.items():
                self.current_parameters[key] = float(entry.get())
            messagebox.showinfo("Applied", "Parameters updated")
        except ValueError:
            messagebox.showerror("Error", "Invalid parameter value")
    
    def save_parameters(self):
        # Save parameters to file
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
                return json.load(f)
        except FileNotFoundError:
            return {
                "lower_rate_limit": 60, "upper_rate_limit": 120,
                "atrial_amplitude": 3.5, "atrial_pulse_width": 0.4,
                "ventricular_amplitude": 3.5, "ventricular_pulse_width": 0.4,
                "vrp": 320, "arp": 250
            }
    
    def save_user_parameters(self):
        # Save user-specific parameters
        # Create data directory if it doesn't exist
        data_dir = os.path.join(self.BASE_DIR, "data")
        os.makedirs(data_dir, exist_ok=True)
        
        param_file = os.path.join(data_dir, f"params_{self.username}.json")
        with open(param_file, 'w') as f:
            json.dump(self.current_parameters, f, indent=2)