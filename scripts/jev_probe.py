"""One real Jev call through OpenRouter with synthetic data, to see the response shape.

Reads OPENROUTER_API_KEY from the environment; never prints it.
"""

import json
import os
import urllib.error
import urllib.request

URL = "https://openrouter.ai/api/alpha/decisions"
body = {
    "model": "typesafe/jev-1.14",
    "state": {"sample": {"file_name": "Kick_Heavy_01.wav", "folders": ["Drums", "Kicks"]}},
    "questions": {
        "one_shot": {
            "type": "noul",
            "instructions": "Is `sample` a single one-shot hit rather than a loop or phrase?",
        },
        "drum_type": {
            "type": "choice",
            "instructions": "Which drum or percussion type is `sample`?",
            "criteria": {"kick": None, "snare": None, "hat_closed": None, "tom": None},
        },
    },
}
req = urllib.request.Request(
    URL,
    data=json.dumps(body).encode(),
    headers={
        "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
        "Content-Type": "application/json",
    },
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print(r.status, json.dumps(json.load(r), indent=1)[:2500])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:1500])
