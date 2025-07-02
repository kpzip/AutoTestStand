from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime

import client.server_comms as server_comms
import client.running_supply_tests as running_supply_tests
from client.scroll_frame import VerticalScrolledFrame

running_tests_toplevel = None

running_tests_list_frame = None

prev_lst = None

def refresh_tests_list(alert=False, force_rerender=False):
	global prev_lst
	try:
		lst = server_comms.get_reports_list()

		if lst != prev_lst or force_rerender:
			prev_lst = lst
			for c in running_tests_list_frame.winfo_children():
				c.destroy()
	
			running_tests_list_frame.columnconfigure((1, 2, 3, 4), weight=1)
			Label(running_tests_list_frame, text="Test Bench").grid(row=1, column=1)
			Label(running_tests_list_frame, text="Date/Time").grid(row=1, column=2)
			Label(running_tests_list_frame, text="Status").grid(row=1, column=3)
			Label(running_tests_list_frame, text="Pass/Fail").grid(row=1, column=4)
			for i in range(len(lst.tests)):
				test = lst.tests[i]
				Label(running_tests_list_frame, text=test.bench.name).grid(row=i+2, column=1)
				Label(running_tests_list_frame, text=datetime.fromtimestamp(test.time).strftime("%m/%d/%Y %H:%M:%S")).grid(row=i+2, column=2)
				text = "Finished" if test.status == "completed" else ("Running" if test.status == "running" else "Queued")
				Label(running_tests_list_frame, text=text).grid(row=i+2, column=3)
				Label(running_tests_list_frame, text="-").grid(row=i+2, column=4)
				is_finished = test.status == "completed"
				Button(running_tests_list_frame, width=10, text="Details", command=lambda bench_id=test.bench.tbid, t=test.time, isf=is_finished: running_supply_tests.running_supply_tests_window(running_tests_toplevel, bench_id, t, isf)).grid(row=i+2, column=5)
	except Exception as e:
		if alert:
			messagebox.showerror(title="Error", message=f"Unable to load running tests: {str(e)}", parent=running_tests_toplevel)

def running_tests_window(root):
	global running_tests_toplevel, running_tests_list_frame
	if running_tests_toplevel is None or not running_tests_toplevel.winfo_exists():
		running_tests_toplevel = Toplevel(root)
		running_tests_toplevel.title("Running Tests")
		running_tests_toplevel.geometry("800x400")
		
		running_tests_frame = ttk.Frame(running_tests_toplevel)
		running_tests_frame.pack(expand=True, fill=BOTH)
		
		
		running_tests_list_frame_outer = ttk.Frame(running_tests_frame, padding="12 12 12 12")
		running_tests_list_frame_outer.pack(expand=True, fill=BOTH, side=TOP)

		scroll_frame = VerticalScrolledFrame(running_tests_list_frame_outer)
		scroll_frame.pack(expand=True, fill=BOTH, side=TOP)
	
		running_tests_list_frame = scroll_frame.interior
		
		refresh_tests_list(alert=True, force_rerender=True)

		def refresh():
			refresh_tests_list()
			running_tests_toplevel.after(2000, refresh)
		
		running_tests_toplevel.after(2000, refresh)
		
		bottom_bar = ttk.Frame(running_tests_frame)
		bottom_bar.pack(fill="x", side=TOP)
		
		Button(bottom_bar, text="Ok", width=10, command=lambda: running_tests_toplevel.destroy()).pack(side=RIGHT, padx=12, pady=12)
		
	else:
		running_tests_toplevel.lift()
