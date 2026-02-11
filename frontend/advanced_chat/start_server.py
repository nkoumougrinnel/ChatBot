#!/usr/bin/env python3
"""
Simple HTTP server for serving the advanced chat frontend.
Listens on 192.168.10.82:8080 by default.
"""
import http.server
import socketserver
import os
import sys

# Configuration
# Bind to 0.0.0.0 so the server accepts connections from localhost and network interfaces
# This ensures connections from localhost:3000 can reach the server.
HOST = "0.0.0.0"
PORT = 3000

# Change to the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add headers to prevent caching
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, format, *args):
        # Better logging format
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

if __name__ == "__main__":
    try:
        with socketserver.TCPServer((HOST, PORT), MyHTTPRequestHandler) as httpd:
            # Show helpful access URLs
            print(f"✓ Server running and listening on {HOST}:{PORT}")
            print(f"  - Access locally via http://localhost:{PORT}")
            print(f"  - Access on this machine's LAN IP (if configured): http://<your-ip>:{PORT}")
            print(f"✓ Press Ctrl+C to stop")
            print(f"\nServing files from: {script_dir}")
            httpd.serve_forever()
    except OSError as e:
        print(f"✗ Error: Could not bind to {HOST}:{PORT}")
        print(f"  {e}")
        print(f"\n  Try:")
        print(f"  - Check if the IP 192.168.10.82 is correct for this machine")
        print(f"  - Use 0.0.0.0:{PORT} to listen on all interfaces")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
