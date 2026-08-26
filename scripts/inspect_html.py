with open("latest_report.html", "r", encoding="utf-8") as f:
    html = f.read()

print("HTML length:", len(html))
print("Contains nav-tab-portfolio:", "nav-tab-portfolio" in html)
print("Contains id='day-table':", 'id="day-table"' in html)
print("Contains id='portfolio-table':", 'id="portfolio-table"' in html)
print("Contains id='view-screener-section':", 'id="view-screener-section"' in html)
print("Contains id='view-portfolio-section':", 'id="view-portfolio-section"' in html)

# Check script tags
import re
scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
print(f"Found {len(scripts)} scripts")
if scripts:
    js = scripts[0]
    print("JS length:", len(js))
    # Check for syntax oddities in JS
    for line in js.splitlines()[:50]:
        if "{" in line or "}" in line or "function" in line or "addEventListener" in line:
            print(line[:100])
