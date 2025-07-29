import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def show_plots(data, temp_units="C"):
	#pd.set_option('display.max_rows', None)
	#print(data.iloc[12000:13000])
	
	fig, (ax1, ax2, ax4) = plt.subplots(3)
	
	time = data["TIMEHRS"]
	iact = data["IACT"]
	isetpt = data["ISETPT"]
	temp = data["TEMP"]
	error = data["PPMERR"] * 1000000

	noramp_cond = np.logical_not(data["RAMPSTATE"])
	
	temp_noramp = data.loc[noramp_cond, "TEMP"]
	error_noramp = data.loc[noramp_cond, "PPMERR"]
	
	temp_c = (temp - 32) * (5/9)
	temp_c_noramp = (temp_noramp - 32) * (5/9)
	
	ax1.set_xlabel("Time (hr)")
	ax1.set_ylabel("Current (A)")

	ax1.plot(time, iact, label="Output Current", color="blue")
	ax1.plot(time, isetpt, label="Set Point", color="orange")
	#ax1.plot(time, error, label="Error", color="green")
	ax1.set_title("Current vs. Time")

	ax1.legend()
	
	#ax1.set_ylim(bottom=0)
	
	#ax2 = ax1.twinx()

	ax2.set_ylabel(f"Temperature ({temp_units})")
	ax2.set_xlabel("Time (hr)")

	ax2.plot(time, temp if temp_units == "F" else temp_c, label="Temperature", color="red")

	ax2.set_title("Temperature & Error vs. Time")
	
	ax2.legend()

	ax3 = ax2.twinx()

	ax3.set_ylabel("Error (ppm)")

	ax3.plot(time, error, label="Error", color="green")

	ax3.legend()

	ax4.set_xlabel(f"Temperature ({temp_units})")
	ax4.set_ylabel("Error (ppm)")

	ax4.scatter(temp if temp_units == "F" else temp_c, error, label="Error", color="red")

	m, b = np.polyfit(temp_noramp if temp_units == "F" else temp_c_noramp, error_noramp, 1)
	
	#print(f"Temperature Coefficient: {m} ppm/{temp_units}")

	bestfit_x = np.linspace(temp.min(), temp.max(), 100)
	bestfit_y = m * bestfit_x + b

	ax4.plot(bestfit_x, bestfit_y, color="red")
	
	ax4.legend()

	ax4.set_title(f"Temperature Coefficient: {m} ppm/{temp_units}")

	fig.tight_layout()
	
	plt.show()
