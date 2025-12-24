"""
Run server and capture all startup errors.
"""
import subprocess
import sys
import time

print("Starting server with error capture...")
process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd=r"c:\Users\tinot\Desktop\zimprep\backend"
)

# Let it run for 10 seconds
time.sleep(10)

# Terminate
process.terminate()
output, _ = process.communicate(timeout=5)

print("\n" + "="*60)
print("SERVER OUTPUT:")
print("="*60)
print(output)

with open("server_startup_log.txt", "w") as f:
    f.write(output)

print("\n" + "="*60)
print("Log saved to: server_startup_log.txt")
