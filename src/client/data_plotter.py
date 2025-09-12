import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from common import test_bench
from datetime import datetime

def show_plots(data, test_time: int, tbid: str, channel: int, test_num: int, serial_number: str, temp_units="C"):
	
	fig, (ax1, ax2, ax4) = plt.subplots(3)
	bench = test_bench.bench_from_id(tbid)
	title = f"{datetime.fromtimestamp(test_time).strftime("%Y-%m-%d %H:%M:%S")} {bench.name}: Channel {channel} Test #{test_num} for power supply \"{serial_number}\""
	fig.canvas.manager.set_window_title("Test Results")
	fig.suptitle(title)
	
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
