import minimalmodbus
import tkinter as tk
from tkinter import messagebox, ttk

def change_modbus_address(serial_port, old_address, new_address, device_type):
    try:
        # Initialize the instrument with the current address [cite: 56]
        instrument = minimalmodbus.Instrument(serial_port, old_address)
        
        # Serial port setup per SenTec standards 
        instrument.serial.baudrate = 9600
        instrument.serial.bytesize = 8
        instrument.serial.parity = minimalmodbus.serial.PARITY_NONE
        instrument.serial.stopbits = 1
        instrument.serial.timeout = 1.0

        if device_type == "SenTec":
            # 1. Write new address to Offset 0 
            # Use Function Code 0x06 (Modify Data) [cite: 26, 44]
            instrument.write_register(0, new_address, functioncode=6)
            
            # 2. Update address to send the Save Command to the new ID
            instrument.address = new_address
            
            # 3. Permanent Save Instruction 
            # Writing 0 to Register 65535 saves to non-volatile user zone 
            instrument.write_register(65535, 0, functioncode=6)
            
            messagebox.showinfo("Success", f"SenTec: Address changed to {new_address} and saved to memory.")
        
        else: # Old Device logic from your original script
            # Uses original 0x0300 register and Function Code 0x10
            instrument.write_register(0x0300, new_address, functioncode=0x10)
            messagebox.showinfo("Success", f"Old Device: Address changed to {new_address}.")

    except minimalmodbus.ModbusException as e:
        messagebox.showerror("Modbus Error", f"Communication failed: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

def submit():
    try:
        port = port_entry.get()
        old_addr = int(old_address_entry.get())
        new_addr = int(new_address_entry.get())
        dev_type = device_var.get()
        
        if not (1 <= new_addr <= 255):
            messagebox.showwarning("Input Error", "Address must be between 1 and 255.")
            return
            
        change_modbus_address(port, old_addr, new_addr, dev_type)
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers for addresses.")

# GUI Setup
app = tk.Tk()
app.title("Modbus Address Tool")
app.geometry("400x320")

# Device Selection
tk.Label(app, text="Device Type:", font=('Arial', 10, 'bold')).pack(pady=5)
device_var = tk.StringVar(value="SenTec")
ttk.Radiobutton(app, text="SenTec (Offset 0 + Save)", variable=device_var, value="SenTec").pack()
ttk.Radiobutton(app, text="Old Device (Offset 0x0300)", variable=device_var, value="Old").pack()

# Inputs
tk.Label(app, text="Serial Port:").pack(pady=5)
port_entry = tk.Entry(app)
port_entry.insert(0, "/dev/ttyUSB0") 
port_entry.pack()

tk.Label(app, text="Current Address:").pack(pady=5)
old_address_entry = tk.Entry(app)
old_address_entry.pack()

tk.Label(app, text="New Address:").pack(pady=5)
new_address_entry = tk.Entry(app)
new_address_entry.pack()

# Action
submit_button = tk.Button(app, text="Change Address", command=submit, bg="#0078d7", fg="white")
submit_button.pack(pady=20)

app.mainloop()
