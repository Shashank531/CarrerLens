import os
import sys
import http.server
import socketserver

DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        try:
            fs = os.fstat(f.fileno())
            total = fs[6]
            range_header = self.headers.get('Range')

            if not range_header or not range_header.startswith('bytes='):
                self.send_response(200)
                self.send_header("Content-type", self.guess_type(path))
                self.send_header("Content-Length", str(total))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                return f

            # Handle Range header
            range_str = range_header[6:].strip()
            if ',' in range_str:
                range_str = range_str.split(',')[0].strip()

            parts = range_str.split('-')
            start_str, end_str = parts[0], parts[1]

            if not start_str and not end_str:
                start, end = 0, total - 1
            elif not start_str:
                # Suffix byte range
                length = int(end_str)
                start = max(0, total - length)
                end = total - 1
            elif not end_str:
                # Prefix byte range
                start = int(start_str)
                end = total - 1
            else:
                start = int(start_str)
                end = int(end_str)

            if start >= total or end >= total or start > end:
                self.send_error(416, "Requested Range Not Satisfiable")
                self.send_header("Content-Range", f"bytes */{total}")
                self.end_headers()
                f.close()
                return None

            content_length = end - start + 1
            self.send_response(206)
            self.send_header("Content-type", self.guess_type(path))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
            self.send_header("Content-Length", str(content_length))
            self.end_headers()

            f.seek(start)
            return _RangeFileWrapper(f, content_length)

        except Exception:
            f.close()
            raise

class _RangeFileWrapper:
    def __init__(self, f, length):
        self.f = f
        self.remaining = length

    def read(self, size=-1):
        if self.remaining <= 0:
            return b""
        if size < 0 or size > self.remaining:
            size = self.remaining
        data = self.f.read(size)
        self.remaining -= len(data)
        return data

    def close(self):
        self.f.close()

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    PORT = 8000
    server = ThreadingHTTPServer(("", PORT), RangeHTTPRequestHandler)
    print(f"Serving frontend with HTTP 206 Range support on http://localhost:{PORT} from {DIRECTORY}")
    server.serve_forever()
