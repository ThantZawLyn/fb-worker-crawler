import urllib.parse as urlparse
from urllib.parse import parse_qs


def get_param(url, param):
    try:
        parsed = urlparse.urlparse(url)
        results = parse_qs(parsed.query)[param]
        if len(results) > 0:
            return results[0]
    except:
        return None
    return None
