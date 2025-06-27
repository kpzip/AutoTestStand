from tkinter import *
from tkinter import ttk

from client.test_options import *
from client.util import *

from common.test import *

create_tests_toplevel = None
test_selection_list = None
supply_info = None

def fix_test_selection_list():
	test_selection_list.delete(0, END)
	for i in range(len(supply_info.tests)):
		test_selection_list.insert(END, supply_info.tests[i])

def save_and_quit():
	create_tests_toplevel.destroy()

def delete_selected():
	selection = test_selection_list.curselection()
	if len(selection) != 0:
		index = selection[0]
		supply_info.tests.pop(index)
		test_selection_list.delete(selection)

def add():
	tw = TestWrapper(ConstantCurrentTest("4Hrs @ 10A", 10, 4))
	test_selection_list.insert(END, tw)
	supply_info.tests.append(tw)
	test_options_window(create_tests_toplevel, supply_info.tests[len(supply_info.tests) - 1], fix_test_selection_list)
	

def edit():
	selection = test_selection_list.curselection()
	if len(selection) != 0:
		test_options_window(create_tests_toplevel, supply_info.tests[selection[0]], fix_test_selection_list)

def create_tests_window(root, channel, info):
	global create_tests_toplevel, test_selection_list, supply_info
	if create_tests_toplevel is None or not create_tests_toplevel.winfo_exists():
		supply_channel = channel
		supply_info = info
		
		create_tests_toplevel = Toplevel(root)
		create_tests_toplevel.title("Create Tests")
		create_tests_toplevel.geometry("500x400")

		create_tests_frame = ttk.Frame(create_tests_toplevel, padding="8 8 8 8")
		create_tests_frame.pack(expand=True, fill=BOTH)

		test_selection_list = Listbox(create_tests_frame)
		fix_test_selection_list()
		test_selection_list.pack(expand=True, fill=BOTH, anchor=W)
		
		create_tests_list = ttk.Frame(create_tests_frame)
		create_tests_list.pack(expand=True, fill=BOTH, anchor=W)

		buttons_list = ttk.Frame(create_tests_frame)
		buttons_list.pack(expand=True, fill="y", anchor=E)

		Button(buttons_list, text="Add", width=10, command=add).pack(anchor=CENTER)
		Button(buttons_list, text="Edit", width=10, command=edit).pack(anchor=CENTER)
		Button(buttons_list, text="Delete", width=10, command=delete_selected).pack(anchor=CENTER)
		Button(buttons_list, text="Ok", width=10, command=save_and_quit).pack(expand=True, anchor=S)

	else:
		create_tests_toplevel.lift()
		
