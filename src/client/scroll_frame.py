from tkinter import *
from tkinter import ttk

class VerticalScrolledFrame(ttk.Frame):
	"""A pure Tkinter scrollable frame that actually works!
	* Use the 'interior' attribute to place widgets inside the scrollable frame.
	* Construct and pack/place/grid normally.
	* This frame only allows vertical scrolling.
	"""
	def __init__(self, parent, *args, **kw):
		ttk.Frame.__init__(self, parent, *args, **kw)

		# Create a canvas object and a vertical scrollbar for scrolling it.
		vscrollbar = ttk.Scrollbar(self, orient=VERTICAL)
		vscrollbar.pack(fill="y", side=RIGHT, expand=False, anchor=W)
		canvas = Canvas(self, bd=0, highlightthickness=0, yscrollcommand=vscrollbar.set)
		canvas.pack(fill=BOTH, side=LEFT, expand=True)
		vscrollbar.config(command=canvas.yview)

		# Reset the view
		canvas.xview_moveto(0)
		canvas.yview_moveto(0)

		# Create a frame inside the canvas which will be scrolled with it.
		self.interior = interior = ttk.Frame(canvas)
		self.interior.pack(expand=True, fill=BOTH)
		interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

		# Track changes to the canvas and frame width and sync them,
		# also updating the scrollbar.
		def _configure_interior(event):
			# Update the scrollbars to match the size of the inner frame.
			size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
			canvas.config(scrollregion="0 0 %s %s" % size)
			if interior.winfo_reqwidth() != canvas.winfo_width():
				# Update the canvas's width to fit the inner frame.
				canvas.config(width=interior.winfo_reqwidth())
		interior.bind('<Configure>', _configure_interior)

		def _configure_canvas(event):
			if interior.winfo_reqwidth() != canvas.winfo_width():
				# Update the inner frame's width to fill the canvas.
				canvas.itemconfigure(interior_id, width=canvas.winfo_width())
		canvas.bind('<Configure>', _configure_canvas)
