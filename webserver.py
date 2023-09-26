from functools import cached_property
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse
import redis
import re
from bs4 import BeautifulSoup

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
        if self.query_data and 'q' in self.query_data:
            query = self.query_data['q'].lower()  
            words = re.split(r'\s+', query)  
            books = self.search_books(words)
        self.wfile.write(self.get_response(books).encode("utf-8"))

    def search_books(self, words):
        book_ids = set()
        for word in words:
            word = word.lower() 
            book_ids.update(r.smembers(word))
        return list(book_ids)

    def get_response(self, books):
        books_info = []
        if books:
            for book_id in books:
                html = r.get(book_id).decode('utf-8')
                title = self.extract_title(html)
                books_info.append(f"Libro {book_id}")

        return f"""
        <h1> Busqueda: </h1>
        <form action="/" method="get">
            <label for="q">Buscar </label>
            <input type="text" name="q" required/>
        </form>
        <p>Palabra(s) clave: {self.query_data.get('q', '')}</p>
        <p>Libros registrados:</p>
        <ul>
            {"".join(f'<li>{info}</li>' for info in books_info)}
        </ul>
        """

    def extract_title(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        return title.get_text() if title else 'Sin titulo'


if __name__ == "__main__":
    print("Server starting...")
    server = HTTPServer(("0.0.0.0", 8000), WebRequestHandler)
    server.serve_forever()
