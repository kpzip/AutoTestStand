import sys

def main():
	if "--server" in sys.argv:
		import server
		server.main()
	else:
		import client
		client.main()

if __name__ == "__main__":
	main()

