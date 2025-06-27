from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from datetime import datetime
from tkinter import messagebox

import client.server_comms as server_comms
import client.data_plotter as plotter

running_supply_tests_toplevel = None
running_supply_tests_list_frame = None

bench_id = None
test_time = None

def save_csv(channel: int, test_number: int, serial_number: str, supply_id: str):
	path = filedialog.asksaveasfilename(initialfile=server_comms.get_csv_file_name(channel, test_number, serial_number, supply_id), defaultextension=".csv", filetypes=[("Comma Separated Variable", "*.csv")], parent=running_supply_tests_toplevel)
	if path:
		try:
			server_comms.download_csv(bench_id, test_time, channel, test_number, serial_number, supply_id, path=path)
		except Exception as e:
			messagebox.showerror(title="Error", message=f"There was an error downloading the .csv file. {str(e)}", parent=running_supply_tests_toplevel)
		else:
			messagebox.showinfo(title="Success", message=f".csv file saved successfully.", parent=running_supply_tests_toplevel)

def plot_csv(channel: int, test_number: int, serial_number: str, supply_id: str):
	try:
		data = server_comms.download_csv(bench_id, test_time, channel, test_number, serial_number, supply_id)
		plotter.show_plots(data)
	except Exception as e:
		messagebox.showerror(title="Error", message=f"There was an error showing the graphs: {str(e)}", parent=running_supply_tests_toplevel)
	

def refresh_tests_list():
	lst = server_comms.get_supply_test_reports_list(bench_id, test_time)
	running_supply_tests_list_frame.columnconfigure((1, 2, 3, 4), weight=1)
	Label(running_supply_tests_list_frame, text="Channel").grid(row=1, column=1)
	Label(running_supply_tests_list_frame, text="Test No.").grid(row=1, column=2)
	Label(running_supply_tests_list_frame, text="Serial Number").grid(row=1, column=3)
	Label(running_supply_tests_list_frame, text="Supply Model").grid(row=1, column=4)
	Label(running_supply_tests_list_frame, text="Status").grid(row=1, column=5)
	for i in range(len(lst.tests)):
		test = lst.tests[i]
		Label(running_supply_tests_list_frame, text=str(test.channel)).grid(row=i+2, column=1)
		Label(running_supply_tests_list_frame, text=str(test.test_number)).grid(row=i+2, column=2)
		Label(running_supply_tests_list_frame, text=test.serial_num).grid(row=i+2, column=3)
		Label(running_supply_tests_list_frame, text=test.supply_type.name).grid(row=i+2, column=4)
		Label(running_supply_tests_list_frame, text="Finished").grid(row=i+2, column=5, padx=8)
		Button(running_supply_tests_list_frame, width=15, text="Download CSV", command=lambda c=test.channel, n=test.test_number, s=test.serial_num, t=test.supply_type.psid: save_csv(c, n, s, t)).grid(row=i+2, column=6)
		Button(running_supply_tests_list_frame, width=15, text="View Data", command=lambda c=test.channel, n=test.test_number, s=test.serial_num, t=test.supply_type.psid: plot_csv(c, n, s, t)).grid(row=i+2, column=7)

def running_supply_tests_window(root, tbid, time):
	global running_supply_tests_toplevel, running_supply_tests_list_frame, bench_id, test_time
	if running_supply_tests_toplevel is None or not running_supply_tests_toplevel.winfo_exists() or tbid != bench_id or time != test_time:
		if running_supply_tests_toplevel is not None:
			running_supply_tests_toplevel.destroy()
		bench_id = tbid
		test_time = time
		running_supply_tests_toplevel = Toplevel(root)
		running_supply_tests_toplevel.title("Running Tests")
		running_supply_tests_toplevel.geometry("1000x400")
		
		running_supply_tests_frame = ttk.Frame(running_supply_tests_toplevel)
		running_supply_tests_frame.pack(expand=True, fill=BOTH)
		
		
		running_supply_tests_list_frame = ttk.Frame(running_supply_tests_frame, padding="12 12 12 12")
		running_supply_tests_list_frame.pack(expand=True, fill=BOTH, side=TOP)
		
		refresh_tests_list()
		
		bottom_bar = ttk.Frame(running_supply_tests_frame)
		bottom_bar.pack(fill="x", side=TOP)
		
		Button(bottom_bar, text="Ok", width=10, command=lambda: running_supply_tests_toplevel.destroy()).pack(side=RIGHT, padx=12, pady=12)
		
	else:
		running_supply_tests_toplevel.lift()
