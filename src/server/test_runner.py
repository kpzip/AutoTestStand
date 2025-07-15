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
		self.time_requested = time.time() * 1000

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
					if not supply_test.is_started:
						supply_test.time_since_last_started = time.time() * 1000
						curr_test.begin(pvs, supply_test.supply_type)
						supply_test.is_started = True
					else:
						finished = curr_test.tick(pvs, time.time() * 1000 - supply_test.time_since_last_started, time.time() * 1000 - test.start_time)
						curr_test.record_data(pvs, time.time() * 1000 - supply_test.time_since_last_started)
					if finished:
						print("finished")
						curr_test.finish(pvs)
						batch_name = test.test_info.bench.tbid + datetime.fromtimestamp(test.start_time / 1000).strftime(date_f_string)
						directory = saved_data_dir / batch_name
						directory.mkdir(parents=True, exist_ok=True)
						
						filename = "ch" + str(supply_test.channel + 1) + "-test" + str(supply_test.test_number + 1) + "-" + supply_test.serial_num + "--" +  supply_test.supply_type.psid + ".csv"
						loc = directory / filename
						curr_test.add_calculated_data(supply_test.supply_type)
						curr_test.saved_data.to_csv(loc, index=False)
				
						
						supply_test.is_started = False
						supply_test.test_number += 1
						if supply_test.test_number >= len(supply_test.tests):
							supply_test.is_finished = True
			if not not_finished:
				finished = running_tests.pop(idx)
				break
		time.sleep(0.5)
		if request_close:
			break
