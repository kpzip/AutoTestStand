from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from datetime import datetime
from tkinter import messagebox

import client.server_comms as server_comms
import client.data_plotter as plotter
from client.scroll_frame import VerticalScrolledFrame

running_supply_tests_toplevel = None
running_supply_tests_list_frame = None

batch_uuid = None
has_results = None

prev_lst = None

def save_csv(channel: int, test_number: int):
	path = filedialog.asksaveasfilename(initialfile=server_comms.get_csv_file_name(channel, test_number), defaultextension=".csv", filetypes=[("Comma Separated Variable", "*.csv")], parent=running_supply_tests_toplevel)
	if path:
		try:
			server_comms.download_csv(batch_uuid, channel, test_number, path=path)
		except Exception as e:
			messagebox.showerror(title="Error", message=f"There was an error downloading the .csv file. {str(e)}", parent=running_supply_tests_toplevel)
		else:
			messagebox.showinfo(title="Success", message=f".csv file saved successfully.", parent=running_supply_tests_toplevel)

def plot_csv(channel: int, test_number: int):
	try:
		data = server_comms.download_csv(batch_uuid, channel, test_number)
		plotter.show_plots(data)
	except Exception as e:
		print(e)
		messagebox.showerror(title="Error", message=f"There was an error showing the graphs: {str(e)}", parent=running_supply_tests_toplevel)
	

def refresh_tests_list(alert=False, force_rerender=False):
	global prev_lst
	try:
		lst = server_comms.get_supply_test_reports_list(batch_uuid)
		if lst != prev_lst or force_rerender:
			prev_lst = lst
			running_supply_tests_list_frame.columnconfigure((1, 2, 3, 4, 5, 6), weight=1)
			Label(running_supply_tests_list_frame, text="Channel").grid(row=1, column=1)
			Label(running_supply_tests_list_frame, text="Test No.").grid(row=1, column=2)
			Label(running_supply_tests_list_frame, text="Serial Number").grid(row=1, column=3)
			Label(running_supply_tests_list_frame, text="Supply Model").grid(row=1, column=4)
			Label(running_supply_tests_list_frame, text="Status").grid(row=1, column=5)
			Label(running_supply_tests_list_frame, text="Pass/Fail").grid(row=1, column=6)
			for i in range(len(lst.tests)):
				test = lst.tests[i]
				Label(running_supply_tests_list_frame, text=str(test.channel)).grid(row=i+2, column=1)
				Label(running_supply_tests_list_frame, text=str(test.test_number)).grid(row=i+2, column=2)
				Label(running_supply_tests_list_frame, text=test.serial_num).grid(row=i+2, column=3)
				Label(running_supply_tests_list_frame, text=test.supply_type.name).grid(row=i+2, column=4)
				text = "Finished" if test.status == "completed" else ("Running" if test.status == "running" else "Queued")
				Label(running_supply_tests_list_frame, text=text).grid(row=i+2, column=5)
				state = NORMAL if test.status == "completed" else DISABLED
				Label(running_supply_tests_list_frame, text="-").grid(row=i+2, column=6, padx=25)
				Button(running_supply_tests_list_frame, state=state, width=15, text="Download CSV", command=lambda c=test.channel, n=test.test_number: save_csv(c, n)).grid(row=i+2, column=7)
				Button(running_supply_tests_list_frame, state=state, width=15, text="View Data", command=lambda c=test.channel, n=test.test_number: plot_csv(c, n)).grid(row=i+2, column=8)
	except Exception as e:
		if alert:
			messagebox.showerror(title="Error", message=f"Error loading test info: {str(e)}", parent=running_supply_tests_toplevel)

def running_supply_tests_window(root, uuid, is_finished: bool):
	global running_supply_tests_toplevel, running_supply_tests_list_frame, batch_uuid, has_results
	if running_supply_tests_toplevel is None or not running_supply_tests_toplevel.winfo_exists() or tbid != bench_id or time != test_time or has_results != is_finished:
		if running_supply_tests_toplevel is not None:
			running_supply_tests_toplevel.destroy()
		batch_uuid = uuid
		has_results = is_finished
		running_supply_tests_toplevel = Toplevel(root)
		running_supply_tests_toplevel.title("Running Tests")
		running_supply_tests_toplevel.geometry("1000x400")
		
		running_supply_tests_frame = ttk.Frame(running_supply_tests_toplevel)
		running_supply_tests_frame.pack(expand=True, fill=BOTH)
		
		running_supply_tests_list_frame_outer = ttk.Frame(running_supply_tests_frame, padding="12 12 12 12")
		running_supply_tests_list_frame_outer.pack(expand=True, fill=BOTH, side=TOP)

		scroll = VerticalScrolledFrame(running_supply_tests_list_frame_outer)
		scroll.pack(expand=True, fill=BOTH)
		
		running_supply_tests_list_frame = scroll.interior
		
		
		refresh_tests_list(alert=True, force_rerender=True)

		def refresh():
			refresh_tests_list()
			running_supply_tests_toplevel.after(2000, refresh)
		
		running_supply_tests_toplevel.after(2000, refresh)
		
		bottom_bar = ttk.Frame(running_supply_tests_frame)
		bottom_bar.pack(fill="x", side=TOP)
		
		Button(bottom_bar, text="Ok", width=10, command=lambda: running_supply_tests_toplevel.destroy()).pack(side=RIGHT, padx=12, pady=12)
		
	else:
		running_supply_tests_toplevel.lift()
