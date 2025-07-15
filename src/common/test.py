from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import time

class Test(ABC):

	@abstractmethod
	def __init__(self, name):
		self.name = name
		self.saved_data = pd.DataFrame(columns=["TIME", "ISETPT", "IACT", "TEMP", "RAMPSTATE", "TIMEHRS"])

	def record_data(self, pvs, ms_since_test_started: int):
		self.saved_data.loc[len(self.saved_data)] = [ms_since_test_started, pvs["ISETPT"].get(), pvs["IACT"].get(), pvs["TEMP"].get(), bool(pvs["RAMPSTATE"].get()), ms_since_test_started / (60 * 60 * 1000)]

	def add_calculated_data(self, supply):
		cond = np.logical_not(self.saved_data["RAMPSTATE"])
		iavg = self.saved_data.loc[cond, "IACT"].mean()
		self.saved_data.loc[cond, "IAVG"] = iavg
		self.saved_data.loc[cond, "PPMERR"] = np.absolute((self.saved_data["IACT"] - self.saved_data["IAVG"]) / (supply.max_current if iavg > 0 else supply.min_current))
	
	def begin(self, pvs, supply_type):
		if state_set_point := pvs.get("STATESETPT"):
			state_set_point.put(1)
			# Wait for the power supply to turn on
			if state := pvs.get("STATE"):
				counter = 0
				while True:
					if state.get() == 1:
						break
					elif counter > 10:
						print("failed to turn on power supply")
						break
					else:
						counter += 1
						time.sleep(0.1)
		if (type_pv := pvs.get("TYPE")) is not None and supply_type.ename is not None:
			type_pv.put(supply_type.ename)

	def finish(self, pvs):
		pass

	@abstractmethod
	def tick(self, pvs, ms_since_test_started: int, ms_elapsed_total: int) -> bool:
		pass

	def __str__(self):
		return self.name

	@abstractmethod
	def to_dict(self):
		return { "name": self.name }

	def from_dict(di, use_ms=True):
		t = di["type"]
		if t == "constant_current":
			return ConstantCurrentTest(di.get("name", "Unnamed Test"), di["current"], di["duration"], use_ms=use_ms)
		else:
			raise ValueError(f"Unknown test type: `{t}`")

# Represents a test where the power supply is set to work at a constant current for a while.
class ConstantCurrentTest(Test):
	
	# duration is in hours
	def __init__(self, name: str, current: float | int, duration: float | int, use_ms=False):
		super().__init__(name)
		self.current = current
		if use_ms:
			self.duration = duration
		else:
			self.duration = duration * 60 * 60 * 1000

	def begin(self, pvs, supply_type):
		super().begin(pvs, supply_type)
		pvs["ISETPT"].put(self.current)

	def finish(self, pvs):
		pvs["ISETPT"].put(0)

	def tick(self, pvs, ms_since_test_started: int, ms_elapsed_total: int) -> bool:
		return ms_since_test_started >= self.duration
	
	def hours(self):
		return self.duration / (60 * 60 * 1000)

	def to_dict(self):
		start = super().to_dict()
		start["type"] = "constant_current"
		start["current"] = self.current
		start["duration"] = self.duration
		return start
