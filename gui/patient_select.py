import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import os
import json
import random
from pydicom import dcmread
from dicom.dicom import init_dir, save_dicom, set_parameter, set_ecg_waveform
import numpy as np

# Helper function to generate unique patient ID
def generate_patient_id(existing_ids):
    while True:
        pid = str(random.randint(10000, 99999))
        if pid not in existing_ids:
            return pid
        
# Set default paramters of
def default_parameters(paths):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
    default_dir = os.path.join(BASE_DIR, "data", "default_params.json")
    with open(default_dir, "r") as f:
        default_params = json.load(f)

    for mode, params in default_params.items():
        for param_name, value in params.items():
            set_parameter(paths["BRADY_PARAM_DCM"], mode, param_name, value)
            set_parameter(paths["TEMP_PARAM_DCM"], mode, param_name, value)


class PatientSelectApp:
    def __init__(self, root, username):
        self.username = username
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
        self.user_dir = os.path.join(BASE_DIR, "data", self.username)
        os.makedirs(self.user_dir, exist_ok=True)
        self.patients_file = os.path.join(self.user_dir, "patients.json")
        self.load_patients()

        self.selected_patient_id = None

        # Setup tkinter window
        self.root = root
        self.root.title(f"Select Patient - {self.username}")
        self.root.geometry("400x400")

        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Select a Patient", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        # Patient list
        self.listbox = tk.Listbox(main_frame, width=40, height=10)
        self.listbox.pack(fill="both", expand=True, pady=(0, 15))
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(10, 0))

        self.proceed_btn = tk.Button(button_frame, text="Proceed", width=12, command=self.proceed)
        self.proceed_btn.grid(row=0, column=0, padx=5)
        
        self.add_btn = tk.Button(button_frame, text="Add New Patient", width=15, command=self.add_patient)
        self.add_btn.grid(row=0, column=1, padx=5)
        
        self.remove_btn = tk.Button(button_frame, text="Remove Patient", width=15, command=self.remove_patient)
        self.remove_btn.grid(row=0, column=2, padx=5)

        self.refresh_list()
        self.root.mainloop()

    # Load patients from JSON
    def load_patients(self):
        if os.path.exists(self.patients_file):
            with open(self.patients_file, "r") as f:
                self.patients_data = json.load(f)
        else:
            self.patients_data = {"patients": []}

    # Save patients to JSON
    def save_patients(self):
        with open(self.patients_file, "w") as f:
            json.dump(self.patients_data, f, indent=2)

    # Refresh the listbox
    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for patient in self.patients_data["patients"]:
            display_name = f"{patient['name']} ({patient['patientID']})"
            self.listbox.insert(tk.END, display_name)

        # Disable proceed/remove if no patients
        if not self.patients_data["patients"]:
            self.proceed_btn.config(state=tk.DISABLED)
            self.remove_btn.config(state=tk.DISABLED)
        else:
            self.proceed_btn.config(state=tk.NORMAL)
            self.remove_btn.config(state=tk.DISABLED)  # initially disabled until selection

    # When a patient is selected
    def on_select(self, _event):
        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            self.selected_patient_id = self.patients_data["patients"][idx]["patientID"]
            self.remove_btn.config(state=tk.NORMAL)
        else:
            self.selected_patient_id = None
            self.remove_btn.config(state=tk.DISABLED)

    # Proceed to main interface
    def proceed(self):
        if self.selected_patient_id:
            self.root.destroy()
            from gui.main_interface import DCMMainInterface
            main_root = tk.Tk()
            DCMMainInterface(main_root, self.username, self.selected_patient_id)
            main_root.mainloop()
        else:
            messagebox.showwarning("No selection", "Please select a patient.")

    # Add new patient
    def add_patient(self):
        name = simpledialog.askstring("Patient Name", "Enter patient name:", parent=self.root)
        if not name:
            return
        birthdate = simpledialog.askstring("Birthdate", "Enter birthdate (YYYY-MM-DD):", parent=self.root)
        if not birthdate:
            return
        sex = simpledialog.askstring("Sex", "Enter sex (M/F):", parent=self.root)
        if not sex:
            return
        
        import re
        birthdate = birthdate.strip()
        sex = sex.strip().upper()

        # Validate birthdate format and sex
        if not re.match(r"\d{4}-\d{2}-\d{2}$", birthdate):
            messagebox.showerror("Invalid Date", "Birthdate must be in YYYY-MM-DD format")
            return
        if sex not in ["M", "F"]:
            messagebox.showerror("Invalid Sex", "Sex must be 'M' or 'F'")
            return

        existing_ids = [p["patientID"] for p in self.patients_data["patients"]]
        patient_id = generate_patient_id(existing_ids)

        # Create patient folder, initialize DICOMs and update patient_info
        paths = init_dir(self.username, patient_id)
        
        try:
            for file, path in paths.items():
                ds = dcmread(path)
                ds.PatientName = name
                ds.PatientID = patient_id
                if file == "PT_INFO_DCM":
                    ds.PatientSex = sex
                    ds.PatientBirthDate = birthdate.replace("-", "")
                # Example Waveform Data
                elif file == "LEAD_WAVFRM_DCM":
                    set_ecg_waveform(path, "Atrial Lead", np.sin(np.linspace(0, 4 * np.pi, 500)))
                    set_ecg_waveform(path, "Ventricular Lead", np.sin(np.linspace(0, 8 * np.pi, 500)))
                    continue
                elif file == "SURFACE_ECG_DCM":
                    set_ecg_waveform(path, "Surface Lead", np.sin(np.linspace(0, 2 * np.pi, 500)))
                    continue
                save_dicom(ds, path)
        except Exception as e:
            messagebox.showerror("DICOM Error", f"Failed to update patient_info: {e}")

        try:
            default_parameters(paths)
        except Exception as e:
            messagebox.showerror("DICOM Error", f"Failed to update parameters: {e}")

        # Add patient record
        new_patient = {
            "patientID": patient_id,
            "name": name,
            "birthdate": birthdate,
            "sex": sex
        }
        self.patients_data["patients"].append(new_patient)
        self.save_patients()
            
        self.refresh_list()

    # Remove selected patient
    def remove_patient(self):
        if not self.selected_patient_id:
            return
        confirm = messagebox.askyesno("Confirm Remove", "Are you sure you want to remove this patient?")
        if confirm:
            # Remove from JSON
            self.patients_data["patients"] = [
                p for p in self.patients_data["patients"] if p["patientID"] != self.selected_patient_id
            ]
            self.save_patients()
            # Remove patient folder
            patient_folder = os.path.join(self.user_dir, self.selected_patient_id)
            if os.path.exists(patient_folder):
                import shutil
                shutil.rmtree(patient_folder)
            self.selected_patient_id = None
            self.refresh_list()