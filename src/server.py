import http.server
import socketserver
import json
import os
import mimetypes
from http import cookies
import database  # Import our database module

PORT = 8801
DIRECTORY = "public"

# Initialize Database
database.init_db()

class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class VetarisHandler(http.server.SimpleHTTPRequestHandler):
    def parse_cookies(self):
        if 'Cookie' in self.headers:
            return cookies.SimpleCookie(self.headers['Cookie'])
        return cookies.SimpleCookie()

    def get_current_user(self):
        cookie = self.parse_cookies()
        if 'session_id' in cookie:
            session_id = cookie['session_id'].value
            return database.get_session(session_id)
        return None

    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        # Parse content length
        try:
            content_length = int(self.headers.get('Content-Length', 0))
        except ValueError:
            content_length = 0
            
        post_data = self.rfile.read(content_length)
        
        try:
            if content_length > 0:
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
        except json.JSONDecodeError:
            self.send_json_response({"error": "Invalid JSON"}, 400)
            return

        # Auth Endpoints
        if self.path == '/api/auth/register':
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                self.send_json_response({"error": "Email and password required"}, 400)
                return

            try:
                user = database.create_user(email, password)
                if user:
                    self.send_json_response({"message": "User created successfully", "user_id": user[0]})
                else:
                    self.send_json_response({"error": "Unknown error"}, 500)
            except ValueError as e:
                # User already exists
                self.send_json_response({"error": str(e)}, 409)
            except Exception as e:
                # Database error
                self.send_json_response({"error": str(e)}, 500)
            return

        elif self.path == '/api/auth/login':
            email = data.get('email')
            password = data.get('password')

            user = database.get_user_by_email(email)
            if user and database.verify_password(user['password_hash'], password):
                session_id = database.create_session(user['id'])
                
                # Set Cookie
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                
                # HttpOnly cookie for security
                cookie = cookies.SimpleCookie()
                cookie['session_id'] = session_id
                cookie['session_id']['path'] = '/'
                cookie['session_id']['httponly'] = True
                self.send_header('Set-Cookie', cookie.output(header=''))
                
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Login successful", "email": user['email']}).encode('utf-8'))
            else:
                self.send_json_response({"error": "Invalid credentials"}, 401)
            return

        elif self.path == '/api/auth/logout':
            cookie = self.parse_cookies()
            if 'session_id' in cookie:
                database.delete_session(cookie['session_id'].value)
            
            # Clear cookie
            self.send_response(200)
            cookie = cookies.SimpleCookie()
            cookie['session_id'] = ''
            cookie['session_id']['path'] = '/'
            cookie['session_id']['expires'] = 0
            self.send_header('Set-Cookie', cookie.output(header=''))
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Logged out"}).encode('utf-8'))
            return

        self.send_error(404, "Endpoint not found")

    def do_GET(self):
        # API Endpoints
        if self.path == '/api/products':
            self.send_json_response({"message": "Product list placeholder. Read from file if needed."}) # Re-implement reading from file if essential, or keep simple for now
            # Restoring original product logic for compatibility
            try:
                with open('data/products.json', 'r', encoding='utf-8') as f:
                    data = f.read()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(data.encode('utf-8'))
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif self.path == '/api/auth/me':
            user_session = self.get_current_user()
            if user_session:
                self.send_json_response({"authenticated": True, "email": user_session['email']})
            else:
                self.send_json_response({"authenticated": False}, 401)
            return

        # Serve Static Files
        if self.path == '/':
            self.path = '/index.html'

        # Construct full path to the file in 'public' directory
        file_path = os.path.join(DIRECTORY, self.path.lstrip('/'))
        
        # Check if file exists
        if os.path.exists(file_path) and os.path.isfile(file_path):
             # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                self.send_response(200)
                self.send_header('Content-type', mime_type)
                self.end_headers()
                
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(200)
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
        else:
            self.send_error(404, "File not found")

    def log_message(self, format, *args):
        # Override to log to console
        print(f"[{self.log_date_time_string()}] {format%args}")

if __name__ == "__main__":
    # Force unbuffered output for Docker/Systemd logs
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    
    print(f"✅ SYSTEM: Vetaris Server baslatiliyor... Port: {PORT}")
    print(f"Statik dosya dizini: {DIRECTORY}")
    
    # Use ThreadingTCPServer for concurrent requests
    with ThreadingHTTPServer(("", PORT), VetarisHandler) as httpd:
        print("Sunucu calisiyor. Durdurmak icin CTRL+C basin.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu durduruluyor...")
            httpd.server_close()
