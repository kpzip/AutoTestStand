import os
import toml
from pathlib import Path
import common.test as test

supplies_definition_dir = Path(__file__).resolve().parent.parent / "data" / "supplies"

def from_dict(n: str, d: dict):
	name = d.get("name")
	ename = d.get("ename")
	max_current = d.get("max_current")
	min_current = d.get("min_current")
	max_ppm_err = d.get("max_ppm_err")
	default_tests = d.get("diagnostic_tests")
	# Basic input validation
	if name is None:
		raise ValueError(f"[Error] No name specified for power supply type `{n}`. Power supply type will not be available.")
	if max_current is None:
		raise ValueError(f"[Error] No maximum current value set for power supply type `{n}`. Power supply type will not be available.")
	if min_current is None:
		raise ValueError(f"[Error] No minimum current value set for power supply type `{n}`. Power supply type will not be available.")
	if default_tests is None:
		default_tests = []
	# Make sure the types are correct
	if not isinstance(name, str):
		raise TypeError(f"[Error] Name for power supply type `{n}` must be of type `String`. Power supply type will not be available.")
	if not isinstance(max_current, int) and not isinstance(max_current, float):
		raise TypeError(f"[Error] Maximum current value for power supply type `{n}` must be a valid number. Power supply type will not be available.")
	if not isinstance(max_current, int) and not isinstance(max_current, float):
		raise TypeError(f"[Error] Minimum current value for power supply type `{n}` must be a valid number. Power supply type will not be available.")	
	if not isinstance(default_tests, list):
		raise TypeError(f"[Error] Diagnostic tests for power supply type `{n}` must be a valid list. Power supply type will not be available.")	
	if not isinstance(ename, int) and ename is not None:	
		raise TypeError(f"[Error] Epics name for power supply type `{n}` must be a valid integer. Power supply type will not be available.")	
	return PowerSupplyType(max_current, min_current, name, n, list(map(lambda t: test.Test.from_dict(t, use_ms=False), default_tests)), ename, max_ppm_err)

def load_power_supply_types():
	types_list: list = []
	supply_types: dict = {}
	for entry in os.listdir(supplies_definition_dir):
		full_path = os.path.join(supplies_definition_dir, entry)
		if os.path.isfile(full_path) and full_path.endswith(".toml"):
			with open(full_path, "r") as tfile:
				try:
					val = toml.load(tfile)
					for k, v in val.items():
						supply_types[k] = v
				except toml.TomlDecodeError as e:
					print(f"[Error] Invalid syntax in power supply definition file at: `{full_path}`. Skipping...")
					print(str(e))
	
	for n, s in supply_types.items():
		try:
			types_list.append(from_dict(n, s))
		except Exception as e:
			print(str(e))	
	return types_list



class PowerSupplyType:

	def __init__(self, max_current, min_current, name, psid, default_tests, ename, max_ppm_err):
		self.name = name
		self.max_current = max_current
		self.min_current = min_current
		self.psid = psid
		self.ename = ename
		self.max_ppm_err = max_ppm_err
		self.default_tests = default_tests

	def __str__(self):
		return f"Power supply type `{self.name}` with min current {self.min_current:.5f}A and max current {self.max_current:.5f}A"


supply_types = load_power_supply_types()

def supply_from_id(psid: str):
	for ps in supply_types:
		if ps.psid == psid:
			return ps
	return None
