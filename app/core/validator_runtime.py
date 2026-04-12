from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import json


def check_health(health_url: str) -> dict:
    try:
        with urlopen(health_url, timeout=5) as response:
            body = response.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body

            return {
                "ok": response.status == 200,
                "status_code": response.status,
                "body": parsed,
                "error": None,
            }
    except HTTPError as e:
        return {
            "ok": False,
            "status_code": e.code,
            "body": None,
            "error": str(e),
        }
    except URLError as e:
        return {
            "ok": False,
            "status_code": None,
            "body": None,
            "error": str(e),
        }
    except Exception as e:
        return {
            "ok": False,
            "status_code": None,
            "body": None,
            "error": str(e),
        }