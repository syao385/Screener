import re

with open("latest_report.html", "r", encoding="utf-8") as f:
    html = f.read()

scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
if scripts:
    js = scripts[0]
    with open("scripts/extracted_js.js", "w", encoding="utf-8") as f:
        f.write(js)
    print("Extracted JS saved to scripts/extracted_js.js")
