from tkinter import *
from tkinter import ttk

from client.run_tests import *
import client.running_tests as running_tests

def main():
	global root
	root = Tk()
	root.title("Power supply test bench management")
	root.geometry("500x300")
	
	mainframe = ttk.Frame(root, padding = "12 12 12 12")
	mainframe.pack(expand=True, fill=BOTH)
	mainframe.columnconfigure((1,), weight=1)

	
	ttk.Button(mainframe, text="New Test", width=20, command=lambda: run_tests_window(root)).grid(column=1, row=1, padx=8, pady=8)
	ttk.Button(mainframe, text="Finished Tests", width=20, command=lambda: running_tests.running_tests_window(root)).grid(column=1, row=2, padx=8, pady=8)

	root.mainloop()


if __name__ == "__main__":
	main()
