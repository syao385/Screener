import re

with open("latest_report.html", "r", encoding="utf-8") as f:
    html = f.read()

scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
if scripts:
    js = scripts[0]
    with open("scripts/extracted_js_clean.js", "w", encoding="utf-8") as f:
        f.write(js)
    print("Clean Extracted JS length:", len(js))
    
    # Check for unescaped newlines in JS single/double quoted strings
    lines = js.splitlines()
    print(f"Total JS lines: {len(lines)}")
    for i, l in enumerate(lines):
        if "SyntaxError" in l or "undefined" in l:
            print(f"Line {i}: {l}")
print("Verification complete.")
