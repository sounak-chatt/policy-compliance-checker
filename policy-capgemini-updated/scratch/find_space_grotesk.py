with open("c:/Users/LENOVO/Downloads/new_policy/policy-compliance-capgemini-updated/policy-capgemini-updated/frontend/src/AppFull.jsx", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if "Space Grotesk" in line:
            print(f"Line {i+1}: {line.strip()[:140]}")
