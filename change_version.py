from pathlib import Path

file = Path("pyproject.toml")
content = file.read_text(encoding="utf-8")
content = content.replace('version = "0.2.2"', 'version = "0.1.0"')
file.write_text(content, encoding="utf-8")
print("版本修改完成")
