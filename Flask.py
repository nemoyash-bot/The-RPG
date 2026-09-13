import subprocess
import sys

print("Installing Flask directly into this Python IDLE environment...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
print("\n✅ SUCCESS! Flask is installed. You can close this window now.")
