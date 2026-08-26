with open("reporter/html_generator.py", "r", encoding="utf-8") as f:
    text = f.read()

import re
scripts = re.findall(r'<script>(.*?)</script>', text, re.DOTALL)
if scripts:
    js = scripts[0]
    for line_idx, line in enumerate(js.splitlines()):
        if "\\" in line:
            safe = line.encode('ascii', 'backslashreplace').decode('ascii')
            print(f"JS Line {line_idx+1}: {safe}")
print("JS check complete.")
