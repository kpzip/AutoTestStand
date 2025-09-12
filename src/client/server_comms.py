import requests
import json
import pandas as pd
from io import StringIO

import common.power_supply as ps
from common.test import *
import common.test_bench as tb

address = "http://lcls-dev3:8080"

run_path = "/run"

reports_path = "/reports"

user_agent = "TestBenchInterface/1.0"

post_headers = {
	"Content-Type": "application/json",
	"User-Agent": user_agent,
	"Accept": "application/json"
}

get_headers = {
	"Accept": "application/json",
	"User-Agent": user_agent
}

class RunTestRequest:
	
	def __init__(self, tbid: str, supply_test_info: list):
		self.tbid = tbid
		self.supply_test_info = supply_test_info
	
	def to_dict(self):
		info = list(map(lambda t: t.to_dict(), self.supply_test_info))
		return { "bench": self.tbid, "test_info": info }

	def send(self):
		payload = self.to_dict()
		response = requests.post(address + run_path, json=payload, headers=get_headers)
		return response

class SupplyTestInfo:

	def __init__(self, channel: int, serial_num: str, psid: str, tests: list):
		self.channel = channel
		self.serial_num = serial_num
		self.psid = psid
		self.tests = tests
	
	def to_dict(self):
		tests = list(map(lambda t: t.to_dict(), self.tests))
		return { "channel": self.channel, "serial_num": self.serial_num, "supply_type": self.psid, "tests": tests }

class Report:
	
	def __init__(self, uuid: str, bench: str, time: int, status: str, pass_fail: str):
		self.bench = None
		for b in tb.benches:
			if b.tbid == bench:
				self.bench = b
				break
		if self.bench is None:
			raise ValueError(f"No Bench with id `{bench}`!")
		self.uuid = uuid
		self.time = time
		self.status = status
		self.pass_fail = pass_fail
	
	def from_dict(d):
		return Report(d["uuid"], d["bench"], d["time"], d["status"], d["pass_fail"])

	def __eq__(self, rhs):
		if rhs is None:
			return False
		return self.uuid == rhs.uuid and self.bench.tbid == rhs.bench.tbid and self.time == rhs.time and self.status == rhs.status and self.pass_fail == rhs.pass_fail

class ReportsList:
	
	def __init__(self, tests: list, total: int, page_size: int):
		self.tests = tests
		self.total = total
		self.page_size = page_size

	def from_dict(d):
		return ReportsList(list(map(Report.from_dict, d["tests"])), d["total"], d["page_size"])

	def __eq__(self, rhs):
		if rhs is None:
			return False
		return self.tests == rhs.tests and self.total == rhs.total and self.page_size == rhs.page_size

def get_reports_list():
	resp = requests.get(address + reports_path, headers=get_headers)
	return ReportsList.from_dict(json.loads(resp.text))

class SupplyTestReport:
	
	def __init__(self, channel: int, test_number: int, supply_type_name: str, serial_num: str, status: str, pass_fail: str, test):
		self.channel = channel
		self.test_number = test_number
		self.serial_num = serial_num
		self.supply_type = None
		self.status = status
		self.pass_fail = pass_fail
		self.test = test
		for s in ps.supply_types:
			if s.psid == supply_type_name:
				self.supply_type = s
				break
		if self.supply_type == None:
			raise ValueError(f"No Supply with id `{supply_type_name}`!")

	def from_dict(d):
		return SupplyTestReport(d["channel"], d["test_num"], d["supply_type"], d["serial_num"], d["status"], d["pass_fail"], Test.from_dict(d["test_info"], use_ms=True))

	def __eq__(self, rhs):
		if rhs is None:
			return False
		return self.channel == rhs.channel and self.test_number == rhs.test_number and self.serial_num == rhs.serial_num and self.supply_type.psid == rhs.supply_type.psid and self.status == rhs.status and self.pass_fail == rhs.pass_fail

class SupplyTestReportList:
	
	def __init__(self, tests: list, total: int):
		self.tests = tests
		self.total = total
	
	def from_dict(d):
		return SupplyTestReportList(list(map(SupplyTestReport.from_dict, d["tests"])), d["total"])

	def __eq__(self, rhs):
		if rhs is None:
			return False
		return self.tests == rhs.tests and self.total == rhs.total

def get_supply_test_reports_list(uuid: str):
	resp = requests.get(address + reports_path + "/" + uuid, headers=get_headers)
	return SupplyTestReportList.from_dict(json.loads(resp.text))

def get_csv_file_name(channel: int, test_number: int):
	name = f"ch{str(channel)}-test{str(test_number)}.csv"
	#print(name)
	return name

def download_csv(uuid: str, channel: int, test_number: int, path=None):
	get_path = address + reports_path + "/" + uuid + "/" + get_csv_file_name(channel, test_number)
	print(get_path)
	csv = requests.get(get_path, headers=get_headers)
	#print(csv.text)
	if path is None:
		csvio = StringIO(csv.text)
		return pd.read_csv(csvio)
	else:
		with open(path, "w") as csvfile:
			csvfile.write(csv.text)
