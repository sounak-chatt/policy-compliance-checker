import requests
import json
import os
import sys

# Reconfigure stdout to use UTF-8 on Windows to prevent cp1252 emoji errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000/api"
headers = {
    "X-Role": "admin",
    "X-User": "demo@nexuszenith"
}


def test_scan(filename, content, expected_status=200):
    url = f"{BASE}/scan"
    files = {"file": (filename, content)}
    print(f"\n--- Testing Scan: {filename} (expected {expected_status}) ---")
    try:
        r = requests.post(url, headers=headers, files=files, stream=True)
        print("Response Code:", r.status_code)
        if r.status_code != expected_status:
            print("FAILED: Status code mismatch.")
            print("Body:", r.text)
            return False
            
        if expected_status == 200:
            sha_checked = False
            for line in r.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: "):
                        data = json.loads(decoded[6:])
                        if data.get("type") == "agent_log":
                            print(f"[Agent Log] {data.get('message')}")
                        elif data.get("type") == "completed":
                            record = data.get('record', {})
                            print(f"[Completed] Score: {record.get('compliance_score')}%, Violations: {record.get('total_violations')}")
                            # Test if SHA-256 hash was generated
                            sha256 = record.get('sha256_hash')
                            print(f"[Completed] SHA-256: {sha256}")
                            if sha256:
                                sha_checked = True
                            else:
                                print("FAILED: SHA-256 integrity hash missing in ScanRecord!")
                                return False
            if sha_checked:
                print("SUCCESS: Stream completed.")
                return True
            else:
                print("FAILED: Completion event not found in stream.")
                return False
        else:
            print(f"SUCCESS: Blocked correctly. Response detail: {r.json().get('detail')}")
            return True
    except Exception as e:
        print("FAILED: Exception occurred:", e)
        return False

# 1. Compliant Document Scan
with open("backend/demo_docs/compliant_data_handling.txt", "rb") as f:
    ok1 = test_scan("compliant_data_handling.txt", f.read(), 200)

# 2. Violating Document Scan
with open("backend/demo_docs/violating_customer_export.txt", "rb") as f:
    ok2 = test_scan("violating_customer_export.txt", f.read(), 200)

# 3. Prompt Injection Guardrail
with open("backend/demo_docs/adversarial_injection.txt", "rb") as f:
    ok3 = test_scan("adversarial_injection.txt", f.read(), 400)


# 4. Large File Guardrail (> 20MB)
large_content = b"x" * (20 * 1024 * 1024 + 100)
ok4 = test_scan("huge_file.txt", large_content, 400)

# 5. Invalid Extension Guardrail
ok5 = test_scan("malicious.exe", b"executable bytes", 400)

if all([ok1, ok2, ok3, ok4, ok5]):
    print("\n🎉 ALL BACKEND GUARDRAIL AND SCAN TESTS PASSED SUCCESSFULLY! 🎉")
    exit(0)
else:
    print("\n❌ SOME TESTS FAILED. CHECK LOGS ABOVE. ❌")
    exit(1)
