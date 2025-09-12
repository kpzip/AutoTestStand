import time
import uuid
from datetime import datetime
import tarfile
import json
import io
import shutil

from common.test_bench import *
from common.power_supply import *
from common.test import Test

request_close = False

saved_data_dir = Path(__file__).resolve().parent.parent / "data" / "reports"

# Maybe make it per month to stop the file from becoming too big?
test_log_path = saved_data_dir / "test_log.json"

date_f_string = "-%m-%d-%Y--%H-%M-%S"

def get_csv_name(channel, number, serial, psid):
	return f"ch{channel + 1}-test{number + 1}.csv"

class SupplyTestLogEntry:

	def __init__(self, channel: int, number: int, serial_number: str, status: str, supply_id: str, pass_fail: str, test):
		self.channel = channel
		self.number = number
		self.serial_number = serial_number
		self.status = status
		self.supply_id = supply_id
		self.pass_fail = pass_fail
		self.test = test

	def to_dict(self):
		return {"channel": self.channel, "number": self.number, "serial_number": self.serial_number, "status": self.status,  "supply_id": self.supply_id, "pass_fail": self.pass_fail, "test": self.test.to_dict()}

	def from_dict(d):
		return SupplyTestLogEntry(d["channel"], d["number"], d["serial_number"], d["status"], d["supply_id"], d["pass_fail"], Test.from_dict(d["test"], use_ms=True))

class TestLogEntry:
	
	def __init__(self, supply_tests: list[SupplyTestLogEntry], bench_id: str, time: int, status: str, pass_fail: str):
		self.supply_tests = supply_tests
		self.bench_id = bench_id
		self.time = time
		self.status = status
		self.pass_fail = pass_fail

	def to_dict(self):
		return {"supply_tests": [st.to_dict() for st in self.supply_tests], "bench_id": self.bench_id, "time": self.time, "status": self.status,  "pass_fail": self.pass_fail}

	def from_dict(d):
		return TestLogEntry([SupplyTestLogEntry.from_dict(st) for st in d["supply_tests"]], d["bench_id"], d["time"], d["status"], d["pass_fail"])

class TestLog:

	def __init__(self, entries):
		self.entries = entries

	def to_dict(self):
		return {k: v.to_dict() for k, v in self.entries.items()}

	def from_dict(d):
		return TestLog({k: TestLogEntry.from_dict(v) for k, v in d.items()})
		
	def load_from_file():
		if not os.path.exists(test_log_path):
			log = TestLog({})
			log.write_out()	
			return log
		with open(test_log_path, "r") as f:
			return TestLog.from_dict(json.loads(f.read()))

	def write_out(self):
		saved_data_dir.mkdir(parents=True, exist_ok=True)
		with open(test_log_path, "w") as f:
			data = json.dumps(self.to_dict())
			print(data)
			f.write(data)

	def insert(self, uuid, entry):
		self.entries[uuid] = entry
		self.write_out()

class TestRequestState:
	
	def __init__(self, test_info):
		self.test_info = test_info
		self.uuid = str(uuid.uuid4())
		self.start_time = None
		self.time_requested = time.time() * 1000
		self.aborted = False
		self.aborted_user = False
		self.aborted_fault = False
		self.aborted_power = False

	def start(self):
		self.start_time = time.time() * 1000

test_queue: list[TestRequestState] = []
running_tests: list[TestRequestState] = []

cancel_list: list[str] = []


def enqueue_test(test):
	test_queue.append(TestRequestState(test))


def test_loop():
	while True:
		# See if there are any other tests we can be running right now
		# todo
		for i in range(len(test_queue)):
			q = test_queue[i]
			is_conflicting = False
			for r in running_tests:
				if q.test_info.bench.tbid == r.test_info.bench.tbid:
					for rst in r.test_info.supply_test_info:
						if rst.is_finished:
							continue
						used_channels = list(map(lambda s: s.channel, q.test_info.supply_test_info))
						if rst.channel in used_channels:
							is_conflicting = True
			if not is_conflicting:
				running_tests.append(test_queue.pop(i))
				print("Running Test...")
				break	

		#if len(running_tests) == 0 and len(test_queue) != 0:
		#	running_tests.append(test_queue.pop(0))
		#	print("Running Test...")
		
		for idx in range(len(running_tests)):
			test = running_tests[idx]
			if test.start_time is None:
				test.start()
			not_finished = False
			bench = test.test_info.bench
			for supply_test in test.test_info.supply_test_info:
				if not supply_test.is_finished:
					not_finished = True
					curr_test = supply_test.tests[supply_test.test_number]
					pvs = {k: v[supply_test.channel] for k, v in bench.pvs.items()}
					finished = False
					if test.uuid in cancel_list:
						print(f"Canceling test: {test.uuid}")
						cancel_list.remove(test.uuid)
						for t in range(supply_test.test_number, len(supply_test.tests)):
							supply_test.tests[t].aborted = True
							supply_test.tests[t].aborted_user = True
							supply_test.tests[t].pass_fail = "fail"
						supply_test.test_number = len(supply_test.tests)
						finished = True
					elif not supply_test.is_started:
						supply_test.time_since_last_started = time.time() * 1000
						start = curr_test.begin(pvs, supply_test.supply_type)
						if not start:
							print("Power Supply Failed to start! Aborting test...")
							curr_test.aborted = True
							curr_test.aborted_power = True
							finished = True
						supply_test.is_started = True
					else:
						if supply_test.time_since_last_started is None and curr_test.should_start_timer(pvs):
							supply_test.time_since_last_started = time.time() * 1000
						elapsed = None if supply_test.time_since_last_started is None else time.time() * 1000 - supply_test.time_since_last_started
						finished = curr_test.tick(pvs, elapsed, time.time() * 1000 - test.start_time)
						curr_test.record_data(pvs, time.time() * 1000 - supply_test.time_since_last_started)
						if curr_test.should_abort(pvs):
							print("Power Supply Fault! Aborting test...")
							curr_test.aborted = True
							curr_test.aborted_fault = True
							finished = True
					if finished:
						print(f"finished test {supply_test.test_number + 1} of {len(supply_test.tests)}")
						curr_test.finish(pvs)

						directory = saved_data_dir / test.uuid
						directory.mkdir(parents=True, exist_ok=True)
						
						filename = get_csv_name(supply_test.channel, supply_test.test_number, supply_test.serial_num, supply_test.supply_type.psid)
						loc = directory / filename
						curr_test.add_calculated_data(supply_test.supply_type)
						curr_test.saved_data.to_csv(loc, index=False)
				
						
						supply_test.is_started = False
						supply_test.test_number += 1
						max_err = supply_test.supply_type.max_ppm_err
						passed = curr_test.saved_data["PPMERR"].max() <= max_err * 1e-6 and not curr_test.aborted
						print(f"Passed: {passed}")
						print(f"Max Error: {curr_test.saved_data["PPMERR"].max()}")
						curr_test.pass_fail = "pass" if passed else "fail"
						
						if supply_test.test_number >= len(supply_test.tests):							
							supply_test.is_finished = True
			if not not_finished:
				finished = running_tests.pop(idx)
				# store metadata
				test_log = TestLog.load_from_file()
				supply_tests_log_entries = []
				for sts in test.test_info.supply_test_info:
					for j in range(len(sts.tests)):
						supply_tests_log_entries.append(SupplyTestLogEntry(sts.channel + 1, j + 1, sts.serial_num, ("no_power" if sts.tests[j].aborted_power else "fault" if sts.tests[j].aborted_fault else "user_canceled") if sts.tests[j].aborted else "completed", sts.supply_type.psid, sts.tests[j].pass_fail, sts.tests[j]))
				test_log.insert(test.uuid, TestLogEntry(supply_tests_log_entries, bench.tbid, test.start_time, ("no_power" if test.aborted_power else "fault" if test.aborted_fault else "user_canceled") if test.aborted else "completed", "pass" if all([le.pass_fail == "pass" for le in supply_tests_log_entries]) else "fail"))
				saved_data_dir.mkdir(parents=True, exist_ok=True)
				tarfile_name = saved_data_dir / (test.uuid + ".tar.gz")
				uncompressed_dir = saved_data_dir / test.uuid
				with tarfile.open(tarfile_name, "w:gz") as tf:
					for root, _, files in os.walk(uncompressed_dir):
						for file in files:
							full_path = os.path.join(root, file)
							relative_path = os.path.relpath(full_path, uncompressed_dir)
							tf.add(full_path, arcname=relative_path)
				shutil.rmtree(uncompressed_dir)
				break
		time.sleep(0.5)
		if request_close:
			break

def cancel_test(uuid: str):
	cancel_list.append(uuid)
