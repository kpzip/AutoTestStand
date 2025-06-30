from tkinter import *
from tkinter import ttk
from tkinter import messagebox

from common.power_supply import *
from common.test_bench import *

from client.create_tests import *
from client.util import *
from client.server_comms import *
from client.scroll_frame import VerticalScrolledFrame

run_tests_toplevel = None
run_tests_channel_info = None
scroll_frame = None
text_frame = None
run_tests_frame = None
run_tests_selected_bench = None

# May be longer
channel_info = []

print("Available Power Supply Types:\n" + "\n".join(map(str, supply_types)) + "\n")
print("Available Power Supply Benches:\n" + "\n".join(map(str, benches)) + "\n")


class ChannelTestInfo:

	def __init__(self, include: BooleanVar, serial: StringVar, supply_type: StringVar, tests: list[TestWrapper]):
		self.include = include
		self.serial = serial
		self.supply_type = supply_type
		self.tests = tests

	def set_include(self, include):
		self.include = include
		print(include)
	
	def set_serial_number(self, serial):
		self.serial = serial

	def set_supply_type(self, supply_type):
		self.supply_type = supply_type

# all_state is not the insurance company!!!
def fix_enabled_disabled(channel_info, i, entry, menu, select, all_state):
	if not channel_info[i].include.get():
		entry.configure(state=DISABLED)
		menu.configure(state=DISABLED)
		select.configure(state=DISABLED)
		all_state.set(False)
	else:
		entry.configure(state=NORMAL)
		menu.configure(state=NORMAL)
		select.configure(state=NORMAL)
		if all(map(lambda s: s.include.get(), channel_info)):
			all_state.set(True)

def set_all(channel_info, state):
	for i in channel_info:
		i.include.set(state)

def populate_test_channel_info(*args, **kwargs):
	# clear out the channel area and re-render
	#for child in run_tests_channel_info.winfo_children():
	#	child.destroy()
	global scroll_frame, text_frame

	# Turns out that making a scroll frame with dynamic content in tkinter is harder than curing cancer.
	if scroll_frame is not None:
		scroll_frame.destroy()
	if text_frame is not None:
		text_frame.destroy()


	# Search for the bench by-name
	bench=None
	for i in benches:
		if i.name == run_tests_selected_bench.get():
			bench=i
			break

	if bench is None:
		text_frame = ttk.Frame(run_tests_frame)
		text_frame.grid(row=2, column=1, sticky="nesw")
		Label(text_frame, text="Select a test bench to set channel information...").pack(anchor=CENTER, expand=True, fill=BOTH)
	else:

		scroll_frame = VerticalScrolledFrame(run_tests_frame)
		scroll_frame.grid(row=2, column=1, sticky="nesw")

		run_tests_channel_info = ttk.Frame(scroll_frame.interior)
		run_tests_channel_info.pack(expand=True, fill=BOTH)
		inner_table = ttk.Frame(run_tests_channel_info, padding = "8 8 8 8")
		inner_table.pack(expand=True, fill=BOTH)



		inner_table.columnconfigure((2, 3, 4), weight=1)

		# fix state
		if len(channel_info) < bench.channels:
			for i in range(bench.channels - len(channel_info)):
				channel_info.append(ChannelTestInfo(BooleanVar(value=True), StringVar(value=""), StringVar(value="Select power supply..."), []))
				channel_info[len(channel_info) - 1].include.trid = None
	
		Label(inner_table, text="Channel").grid(row=1, column=1)
		Label(inner_table, text="Use for this test?").grid(row=1, column=2, padx=10)
		Label(inner_table, text="Serial No.").grid(row=1, column=3)
		Label(inner_table, text="Type").grid(row=1, column=4)
		Label(inner_table, text="Tests").grid(row=1, column=5)

		# Settings for all channels
		Label(inner_table, text="All").grid(row=2, column=1)
		all_include_state = BooleanVar(value=True)
		all_include = Checkbutton(inner_table, variable=all_include_state, command=lambda: set_all(channel_info, all_include_state.get())).grid(row=2, column=2) 
		
		Button(inner_table, text="Auto Detect", width=25).grid(row=2, column=4, padx=8, pady=8, sticky="ew")
		Button(inner_table, text="Use Default Tests", width=20).grid(row=2, column=5)
		
		supply_options = list(map(lambda p: p.name, supply_types))

		r_offset = 3

		for i in range(bench.channels):
			Label(inner_table, text=str(i+1)).grid(row=i+r_offset, column=1)
			data = channel_info[i]
			entry = Entry(inner_table, textvariable=channel_info[i].serial)
			entry.grid(row=i+r_offset, column=3, sticky="ew")
			menu = OptionMenu(inner_table, channel_info[i].supply_type, *supply_options)
			menu.grid(row=i+r_offset, column=4, sticky="ew", padx=8, pady=8)
			menu.config(width=25)
			select = Button(inner_table, text="Select Tests", width=20, command=lambda ch=i: create_tests_window(run_tests_toplevel, ch, channel_info[ch]))
			select.grid(row=i+r_offset, column=5)
			check_state = channel_info[i].include
			Checkbutton(inner_table, variable=check_state).grid(row=i+r_offset, column=2)
			if check_state.trid is not None:
				check_state.trace_remove("write", trid)
			check_state.trace_add("write", lambda *args, idx=i, e=entry, m=menu, s=select: fix_enabled_disabled(channel_info, idx, e, m, s, all_include_state))
			fix_enabled_disabled(channel_info, i, entry, menu, select, all_include_state)

def exit():
	global channel_info
	channel_info = []
	run_tests_toplevel.destroy()			

def submit():
	test_infos = []
	bench=None
	for i in benches:
		if i.name == run_tests_selected_bench.get():
			bench=i
			break
	if bench is None:
		messagebox.showerror(title="Error", message="Please select a test bench.", parent=run_tests_toplevel)
		return
	for i in range(bench.channels):
		if channel_info[i].include.get():
			supply=None
			for s in supply_types:
				if s.name == channel_info[i].supply_type.get():
					supply = s
					break
			if supply is None:
				messagebox.showerror(title="Error", message=f"Please select a power supply for channel {i+1}", parent=run_tests_toplevel)
				return
			serial = channel_info[i].serial.get()
			if serial == "":
				serial = "unknown"
			test_infos.append(SupplyTestInfo(i, serial, supply.psid, list(map(lambda t: t.get_test(), channel_info[i].tests))))
	try:
		test_request = RunTestRequest(bench.tbid, test_infos)
		response = test_request.send()
		response.raise_for_status()
		messagebox.showinfo(title="Success", message="Tests Successfully started.", parent=run_tests_toplevel)
		exit()
	except Exception as e:
		messagebox.showerror(title="Error", message=f"There was an error starting tests. {e}", parent=run_tests_toplevel)

def run_tests_window(root):
	global run_tests_toplevel, run_tests_frame, run_tests_channel_info, scroll_frame, run_tests_selected_bench
	if run_tests_toplevel is None or not run_tests_toplevel.winfo_exists():
		run_tests_toplevel = Toplevel(root)
		run_tests_toplevel.title("Run Tests")
		run_tests_toplevel.geometry("1200x700")
		
		run_tests_frame = ttk.Frame(run_tests_toplevel, padding = "8 8 8 8")
		run_tests_frame.pack(expand=True, fill=BOTH)

		run_tests_frame.columnconfigure((1,), weight=1)
		run_tests_frame.rowconfigure((2,), weight=1)
		
		selection_frame = ttk.Frame(run_tests_frame)
		selection_frame.grid(row=1, column=1, sticky="ew")
		selection_frame.columnconfigure((1,), weight=1)
		bench_names = list(map(lambda b: b.name, benches))
		run_tests_selected_bench = StringVar(run_tests_frame, value="Choose Test Bench...")
		selection = OptionMenu(selection_frame, run_tests_selected_bench, *bench_names, command=populate_test_channel_info)
		selection.grid(row=1, column=1, pady=3)
		selection.config(width=75)

		#scroll_frame = VerticalScrolledFrame(run_tests_frame)
		#scroll_frame.grid(row=2, column=1)

		#run_tests_channel_info = ttk.Frame(scroll_frame.interior)
		#run_tests_channel_info.pack(expand=True, fill=BOTH)
		populate_test_channel_info()

		bottom_bar = ttk.Frame(run_tests_frame, padding= "8 8 8 8")
		bottom_bar.grid(row=3, column=1, sticky="ew")
		Button(bottom_bar, text="Run Tests", command=submit).pack(side=RIGHT, padx=3)
		Button(bottom_bar, text="Cancel", command=exit).pack(side=RIGHT, padx=3)
	else:
		run_tests_toplevel.lift()
