with open("reporter/html_generator.py", "r", encoding="utf-8") as f:
    content = f.read()

# Let's check all occurrences of \n, \r, \s inside JavaScript strings/regex in HTML_TEMPLATE
import re

# Look for JavaScript section
js_match = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
if js_match:
    js_text = js_match.group(1)
    print("Found script of length:", len(js_text))
    
    # Check for unescaped newlines in JS single/double quoted strings
    lines = js_text.splitlines()
    in_str = False
    quote_char = None
    for idx, line in enumerate(lines):
        # check if line has unclosed string
        # count non-escaped single quotes
        # count non-escaped double quotes
        pass
