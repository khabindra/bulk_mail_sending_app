import json
import re

def parse_client_ids(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [int(v) for v in value]

    if isinstance(value, str):
        value = value.strip()
        if value.startswith('['):
            try:
                return [int(v) for v in json.loads(value)]
            except Exception:
                pass
        return [int(v) for v in re.findall(r'\d+', value)]

    try:
        return [int(value)]
    except Exception:
        return []

