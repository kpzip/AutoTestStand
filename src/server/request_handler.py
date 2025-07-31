from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.parse
from datetime import datetime
import os
import tarfile

import server.test_runner
from common.test import *
import common.test_bench as test_bench

httpd = None

class RunTestRequest:
	
	def __init__(self, bench_id: str, supply_test_info: list):
		self.bench = None
		for t in server.test_runner.benches:
			if t.tbid == bench_id:
				self.bench = t
				break
		if self.bench is None:
			raise ValueError(f"Invalid bench name: `{bench_name}`")
		self.supply_test_info = supply_test_info
	
	def from_dict(d):
		ti = d["test_info"]
		return RunTestRequest(d["bench"], [SupplyTestInfo.from_dict(s) for s in ti])	

class SupplyTestInfo:

	def __init__(self, channel: int, serial_num: str, supply_type_id: str, tests: list):
		self.channel = channel
		self.serial_num = serial_num
		self.supply_type = None
		for s in server.test_runner.supply_types:
			if s.psid == supply_type_id:
				self.supply_type = s
				break
		if self.supply_type is None:
			raise ValueError(f"Invalid power supply name: `{supply_type_name}`")
		self.tests = tests
		self.time_since_last_started = None
		self.test_number = 0
		self.is_finished = False
		self.is_started = False
		self.pass_fail = None
	
	def from_dict(d):
		tests = list(map(lambda di: Test.from_dict(di), d["tests"]))
		for t in tests:
			t.pass_fail = "incomplete"
			t.aborted = False
		return SupplyTestInfo(d["channel"], d["serial_num"], d["supply_type"], tests)


class RequestHandler(BaseHTTPRequestHandler):
	
	def do_POST(self):
		content_length = int(self.headers['Content-Length'])
		post_data = self.rfile.read(content_length)
		
		parsed_path = urllib.parse.urlparse(self.path)
		request_path = parsed_path.path
		query_params = urllib.parse.parse_qs(parsed_path.query)


		response_message = {"status": "success"}
		status = 200
		if parsed_path.path == "/run":
			if "application/json" in self.headers["Content-Type"]:
				try:
					req = RunTestRequest.from_dict(json.loads(post_data))
					server.test_runner.enqueue_test(req)
				except json.JSONDecodeError as e:
					status = 400
					response_message["status"] = "error"
					response_message["error_type"] = "json_decode"
					response_message["message"] = str(e)
				except KeyError as e:
					status = 400
					response_message["status"] = "error"
					response_message["error_type"] = "missing_field"
					response_message["message"] = str(e)	
				except ValueError as e:
					status = 400
					response_message["status"] = "error"
					response_message["error_type"] = "invalid_value"
					response_message["message"] = str(e)
				except Exception as e:
					status = 500
					response_message["status"] = "error"
			else:
				status = 400
				response_message["status"] = "error"
				response_message["error_type"] = "invalid_header"
				response_meesage["message"] = "`Content-type` header must be `application/json`."
		else:
			status = 404
			response_message["status"] = "error"
			response_message["error_type"] = "not_found"
			response_message["message"] = "invalid path"
		self.send_response(status)
		self.send_header('Content-type', 'application/json')
		self.end_headers()
		self.wfile.write(json.dumps(response_message).encode('utf-8'))
	
	def do_GET(self):
		parsed_path = urllib.parse.urlparse(self.path)
		request_path = parsed_path.path
		query_params = urllib.parse.parse_qs(parsed_path.query)
		
		status = 404
		response_message = {}
		response_data = None
		content_type = "application/json"

		if parsed_path.path == "/reports":
			print("reports query")
			number = query_params.get("display")
			if number is None:
				number = 1000
			else:
				number = number[0]
			tests_list = []
			folders = []
			path = server.test_runner.saved_data_dir
			test_log = server.test_runner.TestLog.load_from_file()
			for k, v in test_log.entries.items():
				tests_list.append({"bench": v.bench_id, "time": int(v.time / 1000), "status": v.status, "pass_fail": v.pass_fail, "uuid": str(k)})
			#for item in os.listdir(path):
			#	item_path = os.path.join(path, item)
			#	if os.path.isdir(item_path):
			#		folders.append(item)
			#for f in folders:
			#	if len(f) < len(server.test_runner.date_f_string) + 1:
			#		return
			#	split_idx = (len(f) - len(server.test_runner.date_f_string)) - 2
			#	tbid = f[:split_idx]
			#	time = f[split_idx:]
			#	time_ms = int(datetime.strptime(time, server.test_runner.date_f_string).timestamp())
			#	if tbid not in list(map(lambda e: e.tbid, test_bench.benches)):
			#		continue
			#	tests_list.append({"bench": tbid, "time": time_ms, "status": "completed"})
			print(tests_list)
			for t in server.test_runner.test_queue:
				tests_list.append({"bench": t.test_info.bench.tbid, "time": int(t.time_requested / 1000), "status": "queued", "pass_fail": "incomplete", "uuid": str(t.uuid)})
			for t in server.test_runner.running_tests:
				tests_list.append({"bench": t.test_info.bench.tbid, "time": int(t.start_time / 1000), "status": "running", "pass_fail": "incomplete", "uuid": str(t.uuid)})
			total = len(tests_list)
			tests_list.sort(reverse=True, key=lambda e: e["time"])
			tests_list = tests_list[:number]
			status = 200
			response_message["tests"] = tests_list
			response_message["total"] = total
			response_message["page_size"] = number
		elif parsed_path.path.startswith("/reports") and not parsed_path.path.endswith(".csv"):
			split = parsed_path.path.split('/')
			if len(split) == 3:
				uuid = split[2]
				#bench = split[2]
				#time = int(split[3])
				#name = bench + datetime.fromtimestamp(time).strftime(server.test_runner.date_f_string)
				path = server.test_runner.saved_data_dir / (uuid + ".csv")
				queued_test = None
				running_test = None
				for t in server.test_runner.test_queue:
					if t.uuid == uuid:
						queued_test = t
						break
				for t in server.test_runner.running_tests:
					if t.uuid == uuid:
						running_test = t
						break
				tests = []
				if queued_test is not None:
					for st in queued_test.test_info.supply_test_info:
						for i in range(len(st.tests)):
							t = st.tests[i]
							tests.append({"channel": st.channel + 1, "test_num": i + 1, "supply_type": st.supply_type.psid, "serial_num": st.serial_num, "status": "queued", "pass_fail": "incomplete"})
				elif running_test is not None:
					for st in running_test.test_info.supply_test_info:
						for i in range(len(st.tests)):
							t = st.tests[i]
							status = "queued" if i > st.test_number else ("running" if i == st.test_number else ("aborted" if t.aborted else "completed"))
							pass_fail = st.pass_fail if st.pass_fail is not None else "incomplete"
							tests.append({"channel": st.channel + 1, "test_num": i + 1, "supply_type": st.supply_type.psid, "serial_num": st.serial_num, "status": status, "pass_fail": pass_fail})
				else:
					#files = []
					#for item in os.listdir(path):
					#	item_path = os.path.join(path, item)
					#	if os.path.isfile(item_path):
					#		files.append(item)
					#for f in files:
					#	if f.endswith(".csv"):
					#		split1 = f.removesuffix(".csv").rsplit("--", 1)
					#		psid = split1[1]
					#		print(split1)
					#		split2 = split1[0].split("-", 2)
					#		channel = int(split2[0].removeprefix("ch"))
					#		test_num = int(split2[1].removeprefix("test"))
					#		serial_num = split2[2]
					#		tests.append({"channel": channel, "test_num": test_num, "supply_type": psid, "serial_num": serial_num, "status": "completed"})
					test_log = server.test_runner.TestLog.load_from_file()
					entry = test_log.entries.get(uuid)
					if entry is not None:
						for e in entry.supply_tests:
							tests.append({"channel": e.channel, "test_num": e.number, "supply_type": e.supply_id, "serial_num": e.serial_number, "status": e.status, "pass_fail": e.pass_fail})
				tests.sort(key=lambda e: e["test_num"])
				tests.sort(key=lambda e: e["channel"])
				status = 200
				response_message["tests"] = tests
				response_message["total"] = len(tests)
		elif parsed_path.path.startswith("/reports") and parsed_path.path.endswith(".csv"):
			print("get csv")
			split = parsed_path.path.split("/")
			if len(split) == 4:
				uuid = split[2]
				name = split[3]
				path = server.test_runner.saved_data_dir / (uuid + ".tar.gz")
				folderpath = server.test_runner.saved_data_dir / uuid / name
				if path.exists():
					with tarfile.open(path, "r") as tf:
						if name in tf.getnames():
							with tf.extractfile(tf.getmember(name)) as csv:
								status = 200
								content_type = "text/csv"
								response_data = csv.read().decode('utf-8')
								#print("csv: " + response_data)
						else:
							print(f"name {name} not in files {tf.getnames()}")
				elif folderpath.exists():
					# this allows directory traversal. TODO Fix later!
					with open(folderpath, "r") as f:
						status = 200
						content_type = "text/csv"
						response_data = f.read()
				else:
					print("path {path} does not exist")
				#bench = split[2]
				#time = int(split[3])
				#csv_file = split[4]
				#name = bench + datetime.fromtimestamp(time).strftime(server.test_runner.date_f_string)
				#path = server.test_runner.saved_data_dir / name / csv_file
				#if path.exists():
				#	status = 200
				#	content_type = "text/csv"
				#	with open(path, "r") as csvfile:
				#		response_data = csvfile.read()
			else:
				print("invalid path")
		print(parsed_path.path)
		self.send_response(status)
		self.send_header('Content-Type', content_type)
		self.end_headers()
		if response_data is None:
			response_data = json.dumps(response_message)
		self.wfile.write(response_data.encode('utf-8'))
				
		


def run_server(port):
	global httpd
	server_address = ('', port)
	httpd = HTTPServer(server_address, RequestHandler)
	print(f"Starting httpd server on port {port}")
	httpd.serve_forever()

if __name__ == "__main__":
	run_server(8080)
