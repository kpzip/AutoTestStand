from tkinter import *
from tkinter import ttk

from common.test import *

test_options_toplevel = None
selected_test_type = None
test_parameters = None
test_options_frame = None

name_val = None
current_val = None
duration_val = None

test_obj = None

fix_list_callback = None

def draw_test_parameters():
	global name_val, current_val, duration_val
	if test_parameters is None:
		return

	for child in test_parameters.winfo_children():
		child.destroy()
	
	test_type = selected_test_type.get()
	
	Label(test_parameters, text="Name:").grid(row=1, column=1)
	name_val = Entry(test_parameters)
	name_val.insert(0, test_obj.get_test().name)
	name_val.grid(row=1, column=2)

	if test_type == "Constant Current":
		Label(test_parameters, text="Current (A):").grid(row=2, column=1)
		current_val = Entry(test_parameters)
		current_val.insert(0, str(test_obj.get_test().current))
		current_val.grid(row=2, column=2)
		Label(test_parameters, text="Duration (Hr):").grid(row=3, column=1)
		duration_val = Entry(test_parameters)
		duration_val.insert(0, str(test_obj.get_test().hours()))
		duration_val.grid(row=3, column=2)
	else:
		Label(text="Select a test type to view parameters").pack(expand=True, fill=BOTH)

def save_and_quit():
	test_type = selected_test_type.get()
	
	if test_type == "Constant Current":
		test_obj.set_test(ConstantCurrentTest(name_val.get(), float(current_val.get()), float(duration_val.get())))
	fix_list_callback()
	test_options_toplevel.destroy()
	

def test_options_window(root, test_wrapper, cb):
	global test_options_toplevel, test_options_frame, test_parameters, selected_test_type, test_obj, fix_list_callback
	if test_options_toplevel is None or not test_options_toplevel.winfo_exists():
		test_obj = test_wrapper
		fix_list_callback = cb

		test_parameters = None

		test_options_toplevel = Toplevel(root)
		test_options_toplevel.title("Edit Test")
		test_options_toplevel.geometry("500x200")

		
		test_options_frame = Frame(test_options_toplevel)
		test_options_frame.pack(expand=True, fill=BOTH)

		test_types = ["Constant Current"]
		selected_test_type = StringVar(test_options_frame, value=test_types[0])
		menu = OptionMenu(test_options_frame, selected_test_type, *test_types, command=draw_test_parameters())
		menu.pack(side=LEFT, anchor=N, padx=8, pady=8)
		
		cancel_apply_section = Frame(test_options_frame)
		cancel_apply_section.pack(expand=True, fill=BOTH, side=BOTTOM, anchor=SE)
		
		Button(cancel_apply_section, text="Apply", width=10, command=save_and_quit).pack(anchor=SE, side=RIGHT, padx=8, pady=8)
		Button(cancel_apply_section, text="Cancel", width=10, command=lambda: test_options_toplevel.destroy()).pack(anchor=SE, side=RIGHT, padx=8, pady=8)
		
		test_parameters = Frame(test_options_frame)
		test_parameters.pack(expand=True, fill=BOTH, side=LEFT, padx=8, pady=8)

		draw_test_parameters()
		
	else:
		test_options_toplevel.lift()
