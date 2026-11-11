"""Print the Result JSON of a probe evidence file (dev helper): _show_probe.py P-07 [key ...]"""

import json
import re
import sys

pid, keys = sys.argv[1], sys.argv[2:]
text = open(f"docs/release/probes/{pid}.md", encoding="utf-8").read()
m = re.search(r"## Result\s+```json\n(.*?)\n```", text, re.S)
d = json.loads(m.group(1)) if m else {}
print(json.dumps({k: d.get(k) for k in keys} if keys else d, indent=1)[:3500])
