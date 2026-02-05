import http.server
import socketserver
import json
import os
import mimetypes
from http import cookies
import database  # Import our database module
from datetime import datetime, date

PORT = 8801
DIRECTORY = "public"

# Initialize Database
database.init_db()

class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

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
        
        # Helper to serialize datetime and decimal objects
        from decimal import Decimal
        def json_serial(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError ("Type %s not serializable" % type(obj))

        self.wfile.write(json.dumps(data, default=json_serial).encode('utf-8'))

    def check_admin(self):
        user_session = self.get_current_user()
        if user_session and user_session.get('is_admin'):
            return True
        return False

    def do_POST(self):
        # Admin Upload Endpoint (Multipart) - Quick & Dirty handling
        if self.path == '/api/upload':
            if not self.check_admin():
                self.send_json_response({"error": "Unauthorized"}, 403)
                return
            
            # This is a basic implementation. For production, use `cgi` or `multipart` parser
            # But simplehttp server doesn't parse multipart automatically.
            # We'll skip complex upload for now or assume a simpler base64 json mechanism if possible,
            # Or just save files to distinct path if we really want multipart.
            # Let's switch to JSON base64 for simplicity in this "no-framework" environment.
            pass 

        # Parse JSON content length
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
                self.wfile.write(json.dumps({
                    "message": "Login successful", 
                    "email": user['email'],
                    "is_admin": user.get('is_admin', False)
                }).encode('utf-8'))
            else:
                self.send_json_response({"error": "Invalid credentials"}, 401)
            return

        elif self.path == '/api/orders':
            user_session = self.get_current_user()
            if not user_session:
                self.send_json_response({"error": "Unauthorized"}, 401)
                return

            items = data.get('items')
            total = data.get('total')

            if not items or not total:
                 self.send_json_response({"error": "Items and total required"}, 400)
                 return

            try:
                order_id = database.create_order(user_session['user_id'], items, total)
                self.send_json_response({"message": "Order created successfully", "order_id": order_id})
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
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
            
        # --- Admin Endpoints ---
        
        elif self.path == '/api/products': # Create Product
            if not self.check_admin():
                self.send_json_response({"error": "Unauthorized"}, 403)
                return
            try:
                product = database.create_product(data)
                self.send_json_response(product, 201)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif self.path.startswith('/api/admin/orders/'):
            # e.g. /api/admin/orders/5/status
            if not self.check_admin():
                self.send_json_response({"error": "Unauthorized"}, 403)
                return
                
            parts = self.path.split('/')
            if len(parts) >= 6 and parts[5] == 'status':
                order_id = parts[4]
                status = data.get('status')
                if database.update_order_status(order_id, status):
                    self.send_json_response({"success": True})
                else:
                     self.send_json_response({"error": "Update failed"}, 500)
            return

        elif self.path == '/api/posts': # Create Blog Post
            if not self.check_admin():
                self.send_json_response({"error": "Unauthorized"}, 403)
                return
            try:
                post = database.create_post(data)
                self.send_json_response(post, 201)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return
            
        self.send_error(404, "Endpoint not found")

    def do_PUT(self):
        # Parse content length
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            else:
                data = {}
        except:
             self.send_json_response({"error": "Invalid request"}, 400)
             return

        if self.path.startswith('/api/products/'):
            if not self.check_admin():
                self.send_json_response({"error": "Unauthorized"}, 403)
                return
            
            product_id = self.path.split('/')[-1]
            try:
                updated = database.update_product(product_id, data)
                if updated:
                    self.send_json_response(updated)
                else:
                    self.send_json_response({"error": "Product not found"}, 404)
            except Exception as e:
                 self.send_json_response({"error": str(e)}, 500)
            return

        elif self.path.startswith('/api/posts/'):
            if not self.check_admin():
                self.send_json_response({"error": "Unauthorized"}, 403)
                return
            
            post_id = self.path.split('/')[-1]
            try:
                updated = database.update_post(post_id, data)
                if updated:
                    self.send_json_response(updated)
                else:
                    self.send_json_response({"error": "Post not found"}, 404)
            except Exception as e:
                 self.send_json_response({"error": str(e)}, 500)
            return

    def do_DELETE(self):
        if self.path.startswith('/api/products/'):
            if not self.check_admin():
                self.send_json_response({"error": "Unauthorized"}, 403)
                return
            
            product_id = self.path.split('/')[-1]
            try:
                updated = database.delete_product(product_id)
                self.send_json_response({"success": True})
            except Exception as e:
                 self.send_json_response({"error": str(e)}, 500)
            return

        elif self.path.startswith('/api/posts/'):
            if not self.check_admin():
                self.send_json_response({"error": "Unauthorized"}, 403)
                return
            
            post_id = self.path.split('/')[-1]
            try:
                updated = database.delete_post(post_id)
                self.send_json_response({"success": True})
            except Exception as e:
                 self.send_json_response({"error": str(e)}, 500)
            return

    def do_GET(self):
        # API Endpoints
        if self.path == '/api/products':
            try:
                # Read from DB now
                products = database.get_all_products()
                # If DB is empty, maybe fallback or just return empty? 
                # We migrated, so it should be fine.
                self.send_json_response(products)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return

        elif self.path == '/api/auth/me':
            user_session = self.get_current_user()
            if user_session:
                self.send_json_response({
                    "authenticated": True, 
                    "email": user_session['email'],
                    "is_admin": user_session.get('is_admin', False)
                })
            else:
                self.send_json_response({"authenticated": False}, 401)
            return

        elif self.path == '/api/orders':
            user_session = self.get_current_user()
            if not user_session:
                self.send_json_response({"error": "Unauthorized"}, 401)
                return

            orders = database.get_user_orders(user_session['user_id'])
            self.send_json_response(orders)
            return

        elif self.path == '/api/admin/orders':
            if not self.check_admin():
                 self.send_json_response({"error": "Unauthorized"}, 403)
                 return
            orders = database.get_all_orders()
            self.send_json_response(orders)
            return

        # Blog Public Endpoints
        elif self.path == '/api/posts':
            try:
                posts = database.get_all_posts(public_only=True)
                self.send_json_response(posts)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return
            
        elif self.path.startswith('/api/posts/'):
            # Single Post by ID or Slug
            post_id = self.path.split('/')[-1]
            try:
                post = database.get_post(post_id)
                if post:
                     self.send_json_response(post)
                else:
                     self.send_json_response({"error": "Post not found"}, 404)
            except Exception as e:
                self.send_json_response({"error": str(e)}, 500)
            return
        
        # Admin Blog List (All posts)
        elif self.path == '/api/admin/posts':
            if not self.check_admin():
                 self.send_json_response({"error": "Unauthorized"}, 403)
                 return
            posts = database.get_all_posts(public_only=False)
            self.send_json_response(posts)
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
