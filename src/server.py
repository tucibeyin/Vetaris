import http.server
import socketserver
import json
import os
import mimetypes

PORT = 8801
DIRECTORY = "public"

class VetarisHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # API Endpoints
        if self.path == '/api/products':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                with open('data/products.json', 'r', encoding='utf-8') as f:
                    data = f.read()
                    self.wfile.write(data.encode('utf-8'))
            except Exception as e:
                error_response = json.dumps({"error": str(e)})
                self.wfile.write(error_response.encode('utf-8'))
            return

        # Serve Static Files
        # Default to index.html if path is /
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
                # Binary fallback or let SimpleHTTPRequestHandler handle it? 
                # Let's handle generic reading for simplicity in this custom handler
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
    # Ensure we are in the right directory context or using absolute paths
    # For now, assuming script is run from root.
    
    print(f"Vetaris Server baslatiliyor... Port: {PORT}")
    print(f"Statik dosya dizini: {DIRECTORY}")
    
    with socketserver.TCPServer(("", PORT), VetarisHandler) as httpd:
        print("Sunucu calisiyor. Durdurmak icin CTRL+C basin.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu durduruluyor...")
            httpd.server_close()
