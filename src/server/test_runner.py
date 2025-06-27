import time
from datetime import datetime

from common.test_bench import *
from common.power_supply import *

request_close = False

saved_data_dir = Path(__file__).resolve().parent.parent / "data" / "reports"

date_f_string = "-%m-%d-%Y--%H-%M-%S"

class TestRequestState:
	
	def __init__(self, test_info):
		self.test_info = test_info
		self.start_time = None

	def start(self):
		self.start_time = time.time() * 1000

test_queue: list[TestRequestState] = []
running_tests: list[TestRequestState] = []


def enqueue_test(test):
	test_queue.append(TestRequestState(test))


def test_loop():
	while True:
		# See if there are any other tests we can be running right now
		# todo
		if len(running_tests) == 0 and len(test_queue) != 0:
			running_tests.append(test_queue.pop(0))
			print("Running Test...")
		
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
					if not supply_test.is_started:
						supply_test.time_since_last_started = time.time() * 1000
						curr_test.begin(pvs)
						supply_test.is_started = True
					finished = curr_test.tick(pvs, time.time() * 1000 - supply_test.time_since_last_started, time.time() * 1000 - test.start_time)
					curr_test.record_data(pvs, time.time() * 1000 - supply_test.time_since_last_started)
					if finished:
						print("finished")
						curr_test.finish(pvs)
						supply_test.is_started = False
						supply_test.test_number += 1
						if supply_test.test_number >= len(supply_test.tests):
							supply_test.is_finished = True
			if not not_finished:
				finished = running_tests.pop(idx)
				batch_name = test.test_info.bench.tbid + datetime.fromtimestamp(test.start_time / 1000).strftime(date_f_string)
				directory = saved_data_dir / batch_name
				directory.mkdir(parents=True, exist_ok=True)
				for supply_test in test.test_info.supply_test_info:
					for i in range(len(supply_test.tests)):
						curr_test = supply_test.tests[i]
						filename = "ch" + str(supply_test.channel + 1) + "-test" + str(i + 1) + "-" + supply_test.serial_num + "--" +  supply_test.supply_type.psid + ".csv"
						loc = directory / filename
						curr_test.add_calculated_data(supply_test.supply_type)
						curr_test.saved_data.to_csv(loc, index=False)
				break
		if request_close:
			break
