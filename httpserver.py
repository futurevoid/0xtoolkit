From http.server import SimpleHttpRequestHandler as Handler
From socketserver import TCPServer

httpd = TCPServer(("0xlol",1632),Handler)
httpd.serve_forever()
