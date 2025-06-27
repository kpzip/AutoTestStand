class TestWrapper:

	def __init__(self, test):
		self.test = test

	def set_test(self, test):
		self.test = test

	def get_test(self):
		return self.test

	def __str__(self):
		return str(self.test)


