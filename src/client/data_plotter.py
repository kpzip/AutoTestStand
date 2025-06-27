import matplotlib.pyplot as plt

def show_plots(data, temp_units="F"):
	
	fig, (ax1, ax3) = plt.subplots(2)
	
	time = data["TIME"]
	iact = data["IACT"]
	isetpt = data["ISETPT"]
	temp = data["TEMP"]
	error = data["PPMERR"]
	
	
	temp_c = (temp - 32) * (5/9)
	
	
	ax1.set_xlabel("Time (ms)")
	ax1.set_ylabel("Current (A)")

	ax1.plot(time, iact, label="Output Current", color="blue")
	ax1.plot(time, isetpt, label="Set Point", color="orange")

	ax1.legend()
	
	#ax1.set_ylim(bottom=0)
	
	ax2 = ax1.twinx()

	ax2.set_ylabel(f"Temperature ({temp_units})")

	ax2.plot(time, temp if temp_units == "F" else temp_c, label="Temperature", color="red")
	
	ax2.legend()

	#ax2.set_ylim(bottom=0)

	#fig.title("Current vs. Time")

	ax3.set_xlabel(f"Temperature ({temp_units})")
	ax3.set_ylabel("Error (PPM)")

	ax3.scatter(temp if temp_units == "F" else temp_c, error, label="Error", color="red")
	
	ax3.legend()

	#fig.tight_layout()
	
	plt.show()
