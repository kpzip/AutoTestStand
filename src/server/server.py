import threading
import server.request_handler
import server.test_runner
import time
import sys

port = 8080

threads = []

def command_loop():
	while True:
		command = input("")
		if command == "help":
			print("""\
| Help menu:
| help - Display this menu
| exit - Stop the server""")
		elif command == "exit":
			return
		else:
			print("Unknown command. use `help` to see available commands.")

def shdown_counter():
	start = time.time()
	while time.time() - start < 1:
		pass
	sys.exit(0)

def main():
	comms = threading.Thread(target=server.request_handler.run_server, args=(port,))
	comms.start()
	tests = threading.Thread(target=server.test_runner.test_loop)
	tests.start()
	threads.append(tests)
	threads.append(comms)
	command_loop()
	
	shutdown_counter = threading.Thread(target=shdown_counter)
	shutdown_counter.start()

	if server.request_handler.httpd is not None:
		print("Shutting down http server...")
		server.request_handler.httpd.shutdown()
	server.test_runner.request_close = True
	for t in threads:
		t.join()

if __name__ == "__main__":
	main()
