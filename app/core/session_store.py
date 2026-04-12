LAST_RESULT = None


def save_last_result(result: dict) -> None:
    global LAST_RESULT
    LAST_RESULT = result


def get_last_result() -> dict | None:
    return LAST_RESULT