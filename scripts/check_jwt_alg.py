"""Test JWT decode with different secrets and approaches."""
import json, base64
from jose import jwt, jws
import time

jwt_secret = "y63S9cg9Bsjbevec2KQTAnliMiN72Gy7cnSq7uCIPkUA48+Mi2CIpb02IWOjICUQRdJkO80XnMY13QFJoOpPig=="

# 1. Self-signed test
payload = {"sub": "test", "iss": "test", "exp": int(time.time()) + 3600}
token = jwt.encode(payload, jwt_secret, algorithm="HS256")
decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
print("1. Self-signed HS256 test: OK")

# 2. Decode service role key with jwt_secret
service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJzeHdxY3JrdHRsZm5xYmpncGdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDU3MTMxNywiZXhwIjoyMDg2MTQ3MzE3fQ.dxjnj7uQ3-uRRmqFa-MXnM6t3xL-Fci8A-xTqOvy-MU"
try:
    d = jwt.decode(service_key, jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
    role = d.get("role")
    print("2. Service key decode: OK - role=" + str(role))
except Exception as e:
    print("2. Service key decode: FAIL - " + str(e))

# 3. Check what version of jose we have
import jose
print("3. python-jose version: " + jose.__version__)

# 4. Check the algorithms list in jose
print("4. JWS SUPPORTED: " + str(jws.ALGORITHMS.SUPPORTED))

# 5. Check if the issue is with the installed jose backend
# python-jose can use different backends: native, cryptography, pycryptodome
try:
    from jose.backends import ECKey
    print("5. jose backend: has ECKey (cryptography)")
except ImportError:
    print("5. jose backend: NO ECKey - using native/fallback")

# 6. List installed jose packages
import pkg_resources
for p in pkg_resources.working_set:
    if "jose" in p.key or "crypt" in p.key.lower():
        print("6. Package: " + p.key + "==" + p.version)
