import os
import toml
from pathlib import Path
import epics

benches_definition_dir = Path(__file__).resolve().parent.parent / "data" / "benches"

def from_dict(n: str, d: dict, try_connect=True):
	name = d.get("name")
	channels = d.get("channels")

	pvs = d.get("pvs")


	# Basic input validation
	if name is None:
		raise ValueError(f"[Error] No name specified for test bench `{n}`. Test bench will not be available.")
	if channels is None:
		raise ValueError(f"[Error] No number of channels set for test bench `{n}`. Test bench will not be available.")
	if pvs is None:
		raise ValueError(f"[Error] No PVs specified for test bench `{n}`. Test bench will not be available.")
	
	# Usually PVs have uppercase names, but its not standard in TOML
	pvs = {k.replace("_", "").upper(): v for k, v in pvs.items()}
	

	if pvs["IACT"] is None:
		raise ValueError(f"[Error] No actual current PVs specified for test bench `{n}`. Test bench will not be available.")
	if pvs["ISETPT"] is None:
		raise ValueError(f"[Error] No set point PVs specified for test bench `{n}`. Test bench will not be available")
	if pvs["TEMP"] is None:
		raise ValueError(f"[Error] No temp PVs specified for test bench `{n}`. Test bench will not be available")
	if pvs["RAMPSTATE"] is None:
		raise ValueError(f"[Error] No ramp state PVs specified for test bench `{n}`. Test bench will not be available")
	# Make sure the types are correct
	if not isinstance(name, str):
		raise TypeError(f"[Error] Name for test bench `{n}` must be of type `String`. Test bench will not be available.")
	if not isinstance(channels, int):
		raise TypeError(f"[Error] The number of channels for test bench `{n}` must be an integer. Test bench will not be available.")
    
	for k, v in pvs.items():
		if not isinstance(v, list):
			if isinstance(v, str):
				try:
					pvs[k] = [v.format(channel=c+1) for c in range(channels)]
				except Exception as e:
					print(f"An unexpected error occurred during formatting. Please check your syntax! {type(e).__name__} - {e}")
			else:
				raise TypeError(f"[Error] {k} PVs for test bench `{n}`. must be a valid list or format string. Test bench will not be available.")
		elif len(v) != channels:
			raise ValueError("[Error] Wrong number of {k} PVs for test bench `{n}`. Bench has {channels} channels, but {len(v)} PVs were specified.")
	
	# Try connecting to PVs
	pvs = {k: [epics.PV(p) for p in v] for k, v in pvs.items()}
	
	if try_connect:
	# Warning message if any pv failed to connect
		for k, v in pvs.items():
			for p in v:
				if not p.wait_for_connection():
					print("[Warning] PV `{p.pvname}` failed to connect. Maybe its name has changed?")
	
	return TestBench(name, channels, pvs, n)

def load_test_benches(try_connect=True):
	benches_list: list = []
	benches: dict = {}
	for entry in os.listdir(benches_definition_dir):
		full_path = os.path.join(benches_definition_dir, entry)
		if os.path.isfile(full_path) and full_path.endswith(".toml"):
			with open(full_path, "r") as tfile:
				try:
					val = toml.load(tfile)
					for k, v in val.items():
						benches[k] = v
				except toml.TomlDecodeError as e:
					print(f"[Error] Invalid syntax in test bench definition file at: `{full_path}`. Skipping...")
					print(e)
	
	for n, b in benches.items():
		try:
			benches_list.append(from_dict(n, b, try_connect=try_connect))
		except Exception as e:
			print(e)	
	return benches_list



class TestBench:
	
	def __init__(self, name: str, channels: int, pvs: dict[str, list[str]], tbid: str):
		self.name = name
		self.channels = channels
		self.pvs = pvs
		self.tbid = tbid

	def __str__(self):
		return f"Test Bench `{self.name}` with {self.channels} channel(s)"

benches = load_test_benches(try_connect=False)

def bench_from_id(tbid: str):
	for b in benches:
		if b.tbid == tbid:
			return b
	return None
