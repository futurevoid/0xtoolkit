from http.server import SimpleHTTPRequestHandler as Handler
from socketserver import TCPServer

httpd = TCPServer(("localhost",1632),Handler)
httpd.serve_forever()

