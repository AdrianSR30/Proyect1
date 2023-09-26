from functools import cached_property
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

class WebRequestHandler(BaseHTTPRequestHandler):
    @cached_property
    def url(self):
        return urlparse(self.path)

    @cached_property
    def query_data(self):
        return dict(parse_qsl(self.url.query))

    @cached_property
    def post_data(self):
        content_length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(content_length)

    @cached_property
    def form_data(self):
        return dict(parse_qsl(self.post_data.decode("utf-8")))

    @cached_property
    def cookies(self):
        return SimpleCookie(self.headers.get("Cookie"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset = utf-8")
        self.end_headers()
        books = None
        search_query = self.query_data.get('q', '')
        if search_query:
            books = self.search_books(search_query.split(' '))
        self.wfile.write(self.get_response(search_query, books).encode("utf-8"))

    def search_books(self, keywords):
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        return r.sinter(keywords)
        
    def get_response(self, search_query, books):
        return f"""
    <h1> Mi Libreria </h1>
    <form action="/search" method="get">
        <label for="q"> Busqueda </label>
        <input type="text" name="q" required value = "{}"/>
        <input type="submit" value="Buscar"/>
    </form>
    <p>  {self.query_data}   </p>
    <p>  {books}   </p>
"""


if __name__ == "__main__":
    print("Server starting...")
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()
