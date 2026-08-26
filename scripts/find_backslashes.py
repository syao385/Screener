with open("scripts/update_html_generator.py", "r", encoding="utf-8") as f:
    text = f.read()

for line_idx, line in enumerate(text.splitlines()):
    if "\\" in line:
        safe_line = line.encode('ascii', 'backslashreplace').decode('ascii')
        print(f"Line {line_idx+1}: {safe_line}")
