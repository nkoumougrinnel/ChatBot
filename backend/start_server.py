#!/usr/bin/env python3
"""
Start Django development server on 0.0.0.0:8001
Allows frontend from 192.168.10.82 to connect to this API.
"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting Django Backend Server...")
print()
print("Server will be accessible at:")
print("  - http://192.168.10.82:8001")
print("  - http://localhost:8001 (if on same machine)")
print()

try:
    subprocess.run([sys.executable, "manage.py", "runserver", "0.0.0.0:8001"], check=True)
except KeyboardInterrupt:
    print("\nServer stopped")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
