import sys
import os
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import multiprocessing
import numpy as np
import pandas as pd

HandlerClass = SimpleHTTPRequestHandler
ServerClass  = BaseHTTPServer.HTTPServer
Protocol     = "HTTP/1.0"

data = pd.read_csv('ports.csv')
ports = np.unique(data['PORTS']).tolist()
print ports

def start(port):
	server_address = ('127.0.0.1', port)

	HandlerClass.protocol_version = Protocol
	httpd = ServerClass(server_address, HandlerClass)

	sa = httpd.socket.getsockname()
	print "Serving HTTP on", sa[0], "port", sa[1], "..."
	httpd.serve_forever()

if __name__ == '__main__':
	pool = multiprocessing.Pool(processes=len(ports))              # start 4 worker processes
	l = multiprocessing.RLock()

	pool.map(start,ports)
	pool.close()
	pool.join()
