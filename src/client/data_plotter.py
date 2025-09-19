import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import common.test_bench as test_bench
import common.power_supply as power_supply
from datetime import datetime
import warnings

warnings.simplefilter('ignore', np.exceptions.RankWarning)

def show_plots(data, test_time: int, tbid: str, channel: int, test_num: int, serial_number: str, supply_type_id: str, temp_units="C"):
	
	fig, (ax1, ax2, ax4) = plt.subplots(3, constrained_layout=True)
	bench = test_bench.bench_from_id(tbid)
	supply = power_supply.supply_from_id(supply_type_id)
	title = f"{datetime.fromtimestamp(test_time).strftime("%Y-%m-%d %H:%M:%S")} {bench.name}: Channel {channel} Test #{test_num} Results for power supply \"{serial_number}\" ({supply.name})"
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
	
	ax2.legend(loc="upper left")

	ax3 = ax2.twinx()

	ax3.set_ylabel("Error (ppm)")

	ax3.plot(time, error, label="Error", color="green")

	#y_min, y_max = ax3.get_ylim()
	#y_range = y_max - y_min
	#new_y_max = y_max + y_range * 0.35
	#ax3.set_ylim(bottom=y_min, top=new_y_max)
	ax3.margins(y=0.3)
	
	max_err = error[np.argmax(np.absolute(error))]
	max_err_time = time[np.argmax(np.absolute(error))]
	
	bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
	arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=" + ("60" if max_err > 0 else "120"))
	kw = dict(xycoords='data',textcoords="offset points", arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")

	ax3.annotate(f"Max Error: {max_err:.2g}ppm", xy=(max_err_time, max_err), xytext=(130, 25 if max_err > 0 else -15), **kw)

	ax3.legend(loc="upper right")

	ax4.set_xlabel(f"Temperature ({temp_units})")
	ax4.set_ylabel("Error (ppm)")

	ax4.scatter(temp if temp_units == "F" else temp_c, error, label="Error", color="red")

	m, b = np.polyfit(temp_noramp if temp_units == "F" else temp_c_noramp, error_noramp, 1)
	
	#print(f"Temperature Coefficient: {m} ppm/{temp_units}")

	bestfit_x = np.linspace((temp_noramp.max() if temp_units == "F" else temp_c_noramp.min()) - 2, (temp_noramp.max() if temp_units == "F" else temp_c_noramp.max()) + 2, 100)
	bestfit_y = m * bestfit_x + b

	ax4.plot(bestfit_x, bestfit_y, color="red")
	
	ax4.legend()

	ax4.set_title(f"Temperature Coefficient: {m:.3g} ppm/{temp_units}")

	#fig.tight_layout()

	fig.set_figwidth(12.8)
	fig.set_figheight(9.6)
	
	plt.show()
