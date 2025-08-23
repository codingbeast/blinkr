import base64
import sys
import os

if len(sys.argv) != 2:
    print("Usage: python encode_firebase.py path/to/firebase.json")
    sys.exit(1)

json_path = sys.argv[1]

if not os.path.exists(json_path):
    print(f"File not found: {json_path}")
    sys.exit(1)

with open(json_path, "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")

print(encoded)
