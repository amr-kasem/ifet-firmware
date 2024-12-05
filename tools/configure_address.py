import minimalmodbus
import tkinter as tk
from tkinter import messagebox

def change_modbus_address(serial_port, old_address, new_address):
    try:
        # Initialize the instrument with the old address
        instrument = minimalmodbus.Instrument(serial_port, old_address)
        instrument.serial.baudrate = 9600  # Set baudrate as needed
        instrument.serial.timeout = 1.0    # Adjust timeout as needed

        # Write the new address to the instrument's register (0x0300 is an example)
        instrument.write_register(0x0300, new_address, functioncode=0x10)  # Function code 16 writes to multiple registers

        # Show success message
        messagebox.showinfo("Success", f"Modbus RTU address changed from {old_address} to {new_address}")
    except minimalmodbus.ModbusException as e:
        messagebox.showerror("Modbus Exception", f"Modbus Exception: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

def submit():
    # Get values from entry fields
    serial_port = serial_port_entry.get()
    old_address = int(old_address_entry.get())
    new_address = int(new_address_entry.get())
    
    # Call the function to change the address
    change_modbus_address(serial_port, old_address, new_address)

# Create main application window
app = tk.Tk()
app.title("Modbus Address Changer")
app.geometry("400x200")

# Serial Port
tk.Label(app, text="Serial Port:").pack(pady=5)
serial_port_entry = tk.Entry(app)
serial_port_entry.pack(pady=5)

# Old Address
tk.Label(app, text="Current Modbus Address:").pack(pady=5)
old_address_entry = tk.Entry(app)
old_address_entry.pack(pady=5)

# New Address
tk.Label(app, text="New Modbus Address:").pack(pady=5)
new_address_entry = tk.Entry(app)
new_address_entry.pack(pady=5)

# Submit Button
submit_button = tk.Button(app, text="Change Address", command=submit)
submit_button.pack(pady=20)

# Start the GUI loop
app.mainloop()
