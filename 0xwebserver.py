from http.server import SimpleHTTPRequestHandler as Handler
from socketserver import TCPServer

httpd = TCPServer(("localhost",1634),Handler)
httpd.serve_forever()
print("shit is running")
